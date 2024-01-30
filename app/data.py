from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class RTSPSettings(BaseSettings):
    url: str = Field(
        ...,
    )
    access_token: str = Field(
        ...,
    )

    model_config = SettingsConfigDict(env_prefix="RTSP_")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("rtsp://", "rtsps://")):
            raise ValueError("Invalid RTSP URL format")
        return v


class HLSSettings(BaseSettings):
    hls_directory: str = Field("hls_stream", description="Directory path for storing HLS segments and playlist files.")
    hls_time: int = Field(
        2,
        description="Length of each HLS segment in seconds.",
        ge=1,
    )
    hls_list_size: int = Field(
        3,
        description="Number of segments to include in the HLS playlist.",
        gt=0,
    )
    hls_flags: str = Field("delete_segments", description="Additional flags for HLS processing.")

    model_config = SettingsConfigDict(env_prefix="HLS_")
