import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from app.configuration import FeatureFlags
from app.configuration import HLSSettings
from app.configuration import RTSPSettings
from app.helpers import deregister_service_with_etcd
from app.helpers import get_etcd_client
from app.helpers import get_hls_services_from_etcd
from app.helpers import get_ip_address
from app.helpers import parse_gst_log
from app.helpers import register_service_with_etcd
from app.helpers import start_gstreamer


def test_start_ffmpeg():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        hls_settings = HLSSettings(
            directory="some_directory",
            time=2,
            list_size=3,
            flags="delete_segments",
        )
        feature_flags = FeatureFlags()
        rtsp_stream = RTSPSettings(url="rtsp://example.com", access_token="token")
        process = start_gstreamer(hls_settings, rtsp_stream, feature_flags)
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


@pytest.mark.parametrize(
    "log_line,expected_result",
    [
        (
            r'2024-02-03T09:28:13Z [DEBUG] app.helpers: /GstPipeline:pipeline0/GstRTSPSrc:rtspsrc0/GstRtpBin:manager/GstRtpSession:rtpsession0: stats = application/x-rtp-session-stats, rtx-drop-count=(uint)0, sent-nack-count=(uint)0, recv-nack-count=(uint)0, source-stats=(GValueArray)< "application/x-rtp-source-stats\\, ssrc\\=(uint)1362859901\\, internal\\=(boolean)false\\, validated\\=(boolean)true\\, received-bye\\=(boolean)false\\, is-csrc\\=(boolean)false\\, is-sender\\=(boolean)true\\, seqnum-base\\=(int)-1\\, clock-rate\\=(int)48000\\, octets-sent\\=(guint64)0\\, packets-sent\\=(guint64)0\\, octets-received\\=(guint64)2724062\\, packets-received\\=(guint64)16247\\, bytes-received\\=(guint64)3373942\\, bitrate\\=(guint64)77923\\, packets-lost\\=(int)-1\\, jitter\\=(uint)1371\\, sent-pli-count\\=(uint)0\\, recv-pli-count\\=(uint)0\\, sent-fir-count\\=(uint)0\\, recv-fir-count\\=(uint)0\\, sent-nack-count\\=(uint)0\\, recv-nack-count\\=(uint)0\\, recv-packet-rate\\=(uint)45\\, have-sr\\=(boolean)true\\, sr-ntptime\\=(guint64)9487551828706254126\\, sr-rtptime\\=(uint)191950902\\, sr-octet-count\\=(uint)2711990\\, sr-packet-count\\=(uint)16175\\, sent-rb\\=(boolean)true\\, sent-rb-fractionlost\\=(uint)0\\, sent-rb-packetslost\\=(int)-1\\, sent-rb-exthighestseq\\=(uint)19614\\, sent-rb-jitter\\=(uint)1371\\, sent-rb-lsr\\=(uint)2384394788\\, sent-rb-dlsr\\=(uint)98714\\, have-rb\\=(boolean)false\\, rb-ssrc\\=(uint)0\\, rb-fractionlost\\=(uint)0\\, rb-packetslost\\=(int)0\\, rb-exthighestseq\\=(uint)0\\, rb-jitter\\=(uint)0\\, rb-lsr\\=(uint)0\\, rb-dlsr\\=(uint)0\\, rb-round-trip\\=(uint)0\\;',
            {"packets_received": 16247, "packets_lost": 1371, "recv_packet_rate": 45},
        ),
        ("No matching information", {"packets_received": 0, "packets_lost": 0, "recv_packet_rate": 0}),
    ],
)
def test_parse_gst_log(log_line, expected_result):
    assert expected_result == parse_gst_log(log_line)
