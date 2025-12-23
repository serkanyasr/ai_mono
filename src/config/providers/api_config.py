from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    
    
    # =====================
    # API Config
    # =====================
    api_env: str = Field("development", validation_alias="API_ENV")
    api_host: str = Field("0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(8000, validation_alias="API_PORT")
    api_log_level: str = Field("info", validation_alias="API_LOG_LEVEL")


    
    # =====================
    # CORS Settings
    # =====================
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias="CORS_ORIGINS"
    )

    cors_allow_credentials: bool = Field(
        default=True,
        validation_alias="CORS_ALLOW_CREDENTIALS"
    )

    cors_allow_methods: List[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias="CORS_ALLOW_METHODS"
    )

    cors_allow_headers: List[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias="CORS_ALLOW_HEADERS"
    )

    cors_expose_headers: List[str] = Field(
        default_factory=list,
        validation_alias="CORS_EXPOSE_HEADERS"
    )

    cors_max_age: int = Field(
        default=600,
        validation_alias="CORS_MAX_AGE"
    )

    # ---------------------
    # Validators (ENV parse)
    # ---------------------
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None:
            return ["*"]
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("cors_allow_methods", "cors_allow_headers", "cors_expose_headers", mode="before")
    @classmethod
    def parse_csv_list(cls, v):
        if v is None:
            return ["*"]
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                return []
            # "GET, POST"
            return [x.strip() for x in s.split(",") if x.strip()]
        return v
