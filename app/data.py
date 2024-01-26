from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
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
