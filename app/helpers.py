import os
import re
import socket
import subprocess
import threading
from typing import Optional
from typing import OrderedDict

import prometheus_client as prometheus
from etcetra import EtcdClient
from etcetra import HostPortPair

from .configuration import FeatureFlags
from .configuration import HLSSettings
from .configuration import RTSPSettings
from .logger import get_logger


logger = get_logger(__name__)


def makeup_service_name(settings: RTSPSettings) -> str:
    return f"hls_streamer_{settings.url.split(':')[1][-3:]}_{settings.access_token[:3]}"


def log_to_prometheus(line: str, ffmpeg_frame_drops: prometheus.Gauge, ffmpeg_fps: prometheus.Gauge):
    match = re.search(r"fps=\s*(\d+) .* drop=(\d+)", line)
    if match:
        fps = int(match.group(1))
        drop = int(match.group(2))
        ffmpeg_fps.set(fps)
        ffmpeg_frame_drops.set(drop)
        logger.debug(f"FPS: {fps}, Drop: {drop}")


def start_ffmpeg(
    hls_settings: HLSSettings, rtsp_settings: RTSPSettings, feature_flags: FeatureFlags
) -> Optional[subprocess.Popen]:
    rtsp_url = f"{rtsp_settings.url}/{rtsp_settings.access_token}"
    output_path = os.path.join(hls_settings.directory, "stream.m3u8")
    command = [
        "ffmpeg",
        "-i",
        rtsp_url,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-hls_time",
        str(hls_settings.time),
        "-hls_list_size",
        str(hls_settings.list_size),
        "-hls_flags",
        hls_settings.flags,
        output_path,
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logger.info(f"Started FFmpeg process for {rtsp_url}")

        if feature_flags.enable_prometheus:
            logger.info(f"Prometheus requested, exporting on port: {os.getenv('PROM_PORT')}")
            fps_gauge = prometheus.Gauge("ffmpeg_fps", "Frames Per Second")
            drop_counter = prometheus.Gauge("ffmpeg_frame_drop", "Number of Dropped Frames")

        def log_output(stream) -> None:
            for line in iter(stream.readline, b""):
                line_decoded = line.decode().strip()
                logger.debug(line_decoded)
                if feature_flags.enable_prometheus:
                    log_to_prometheus(line_decoded, ffmpeg_frame_drops=drop_counter, ffmpeg_fps=fps_gauge),

        t = threading.Thread(target=log_output, args=(process.stdout,), daemon=True)
        t.start()

        return process
    except Exception as e:
        logger.error(f"Failed to start FFmpeg process: {e}")
        return None


def get_ip_address() -> str:
    """Function to get the IP address of the machine"""
    return socket.gethostbyname(socket.gethostname())


def get_etcd_client() -> EtcdClient:
    return EtcdClient(HostPortPair(os.getenv("etcd_host", "localhost"), os.getenv("etcd_port", 2379)))


async def register_service_with_etcd(etcd: EtcdClient, service_name: str, ip: str, port: int) -> EtcdClient:
    service_key = f"/services/{service_name}"
    service_value = f"{ip}:{port}"
    async with etcd.connect() as c:
        await c.put(key=service_key, value=service_value)
        logger.info(f"Registered at {service_key}")
    return etcd


async def deregister_service_with_etcd(etcd, service_name: str) -> bool:
    service_key = f"/services/{service_name}"
    async with etcd.connect() as c:
        await c.delete(service_key)
        logger.info(f"Unregistered {service_key}")


async def get_hls_services_from_etcd(etcd: EtcdClient) -> OrderedDict[str, str]:
    async with etcd.connect() as c:
        return await c.get_prefix("/services/hls_")
