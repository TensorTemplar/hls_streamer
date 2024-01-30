import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import start_http_server
from pydantic import ValidationError

from .configuration import FeatureFlags
from .configuration import HLSSettings
from .configuration import RTSPSettings
from .helpers import deregister_service_with_etcd
from .helpers import get_etcd_client
from .helpers import get_ip_address
from .helpers import makeup_service_name
from .helpers import register_service_with_etcd
from .helpers import start_ffmpeg
from .logger import get_logger


logger = get_logger(__name__)

PORT = int(os.getenv("PORT", 8081))
FEATURE_FLAGS = FeatureFlags()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if FEATURE_FLAGS.enable_discovery:
        logger.info(f"Discovery is {FEATURE_FLAGS.enable_discovery}, registering in ETCD")
        await register_service_with_etcd(get_etcd_client(), makeup_service_name(RTSPSettings()), get_ip_address(), PORT)

    yield

    if FEATURE_FLAGS.enable_discovery:
        logger.info("Unregistering in ETCD")
        await deregister_service_with_etcd(get_etcd_client(), makeup_service_name(RTSPSettings()))


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    try:
        rtsp_settings = RTSPSettings()
        hls_settings = HLSSettings()
    except ValidationError as e:
        print("Invalid RTSP stream configuration:", e.json())
        os._exit(1)

    os.makedirs(hls_settings.directory, exist_ok=True)

    app.mount("/hls_stream", StaticFiles(directory=hls_settings.directory), name="hls_stream")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if FEATURE_FLAGS.enable_prometheus:
        start_http_server(9090)

    start_ffmpeg(hls_settings=hls_settings, rtsp_settings=rtsp_settings, feature_flags=FEATURE_FLAGS)

    return app


if __name__ == "__main__":
    logger.info("Starting HLS streamer application")
    app = create_app()
    logger.info("HLS streamer application started")
