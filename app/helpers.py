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


def make_service_name(settings: RTSPSettings) -> str:
    return f"hls_streamer_{settings.url.split(':')[1][-3:]}_{settings.access_token[:3]}"


import re


def parse_gst_log(log_line: str) -> dict[str, int]:
    patterns = {
        "packets_received": r"packets-received.+?\)(\d+)",
        "packets_lost": r"packets-lost.+?\)(\d+)",
        "recv_packet_rate": r"recv-packet-rate.+?\)(\d+)",
    }

    result = {key: 0 for key in patterns.keys()}

    for key, pattern in patterns.items():
        if match := re.search(pattern, log_line):
            result[key] = int(match.group(1))

    return result


def start_gstreamer(
    hls_settings: HLSSettings, rtsp_settings: RTSPSettings, feature_flags: FeatureFlags
) -> Optional[subprocess.Popen]:
    rtsp_url = f"{rtsp_settings.url}/{rtsp_settings.access_token}"
    playlist_location = os.path.join(hls_settings.directory, "stream.m3u8")
    segment_location = os.path.join(hls_settings.directory, "segment%05d.ts")

    command = [
        "gst-launch-1.0",
        "-v",
        "rtspsrc",
        f"location={rtsp_url}",
        "tls-validation-flags=0",
        "protocols=GST_RTSP_LOWER_TRANS_TCP",
        "!",
        "rtph264depay",
        "!",
        "h264parse",
        "!",
        "hlssink2",
        f"location={segment_location}",
        f"playlist-location={playlist_location}",
        f"playlist-root=http://localhost:{os.getenv('PORT', 8081)}/hls_stream/",
        f"max-files={hls_settings.list_size}",
        f"target-duration={hls_settings.time}",
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logger.info(f"Started GStreamer process for {rtsp_url}")

        if feature_flags.enable_prometheus:
            logger.info(f"Prometheus requested, exporting on port: {os.getenv('PROM_PORT')}")
            loss_counter = prometheus.Gauge("packets_lost", "Number of lost packets")
            packet_rate = prometheus.Gauge("recv_packet_rate", "Rate of packet transmission")

        def log_output(stream) -> None:
            for line in iter(stream.readline, b""):
                line_decoded = line.decode().strip()
                logger.debug(line_decoded)
                if feature_flags.enable_prometheus:
                    stats = parse_gst_log(line_decoded)
                    loss_counter.set(stats["packets_lost"])
                    packet_rate.set(stats["recv_packet_rate"])

        t = threading.Thread(target=log_output, args=(process.stdout,), daemon=True)
        t.start()

        return process
    except Exception as e:
        logger.error(f"Failed to start GStreamer process: {e}")
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
