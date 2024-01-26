# test/test_helpers.py

import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from .app.helpers import deregister_service_with_etcd
from .app.helpers import get_etcd_client
from .app.helpers import get_hls_services_from_etcd
from .app.helpers import get_ip_address
from .app.helpers import register_service_with_etcd
from .app.helpers import start_ffmpeg



# Test start_ffmpeg function
def test_start_ffmpeg():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        process = start_ffmpeg("some_directory", MagicMock(url="rtsp://example.com", access_token="token"))
        mock_popen.assert_called_once()
        assert process is not None


# Test get_ip_address function
def test_get_ip_address():
    ip = get_ip_address()
    assert isinstance(ip, str)  # Add more specific checks based on your requirements


# Assuming default etcd host and port
ETCD_HOST = "127.0.0.1"
ETCD_PORT = 2379


@pytest.mark.asyncio
async def test_register_and_deregister_service_with_etcd():
    service_name = "hls_test_service"
    ip = "127.0.0.1"
    port = 8081

    # Set environment variables for etcd connection if needed
    os.environ["etcd_host"] = ETCD_HOST
    os.environ["etcd_port"] = str(ETCD_PORT)

    c = get_etcd_client()
    # Register service
    await register_service_with_etcd(c, service_name, ip, port)

    # Retrieve services
    services = await get_hls_services_from_etcd(etcd=c)
    assert f"/services/{service_name}" in services

    # Deregister service
    await deregister_service_with_etcd(etcd=c, service_name=service_name)
    services_after_deregister = await get_hls_services_from_etcd(c)
    assert f"/services/{service_name}" not in services_after_deregister
