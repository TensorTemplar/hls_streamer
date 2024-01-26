import os
import socket
import subprocess
from typing import OrderedDict

from etcetra import EtcdClient
from etcetra import HostPortPair

from .data import Settings
from .logger import get_logger


logger = get_logger(__name__)


def makeup_service_name(settings: Settings) -> str:
    return f"hls_streamer_{settings.url.split(':')[1][-3:]}_{settings.access_token[:3]}"


def start_ffmpeg(hls_directory: str, rtsp_stream: Settings) -> subprocess.Popen:
    rtsp_url = f"{rtsp_stream.url}/{rtsp_stream.access_token}"
    output_path = os.path.join(hls_directory, "stream.m3u8")
    command = [
        "ffmpeg",
        "-i",
        rtsp_url,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-hls_time",
        "2",
        "-hls_list_size",
        "3",
        "-hls_flags",
        "delete_segments",
        output_path,
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Started FFmpeg process for {rtsp_url}")
        return process
    except Exception as e:
        logger.error(f"Failed to start FFmpeg process: {e}")
        raise


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
