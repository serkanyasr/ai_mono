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


    