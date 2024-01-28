import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .data import RTSPSettings
from .helpers import deregister_service_with_etcd
from .helpers import get_etcd_client
from .helpers import get_ip_address
from .helpers import makeup_service_name
from .helpers import register_service_with_etcd
from .helpers import start_ffmpeg
from .logger import get_logger


logger = get_logger(__name__)

PORT = int(os.getenv("PORT", 8081))
ENABLE_DISCOVERY = os.getenv("ENABLE_DISCOVERY", "False")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ENABLE_DISCOVERY == "True":
        logger.info(f"Discovery is {ENABLE_DISCOVERY}, registering in ETCD")
        await register_service_with_etcd(get_etcd_client(), makeup_service_name(RTSPSettings()), get_ip_address(), PORT)

    yield

    if ENABLE_DISCOVERY == "True":
        logger.info("Unregistering in ETCD")
        await deregister_service_with_etcd(get_etcd_client(), makeup_service_name(RTSPSettings()))


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    try:
        settings = RTSPSettings()
    except ValidationError as e:
        print("Invalid RTSP stream configuration:", e.json())
        os._exit(1)

    hls_directory = "hls_stream"

    os.makedirs(hls_directory, exist_ok=True)

    app.mount("/hls_stream", StaticFiles(directory=hls_directory), name="hls_stream")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    start_ffmpeg(hls_directory, rtsp_stream=settings)

    return app


if __name__ == "__main__":
    logger.info("Starting HLS streamer application")
    app = create_app()
    logger.info("HLS streamer application started")
