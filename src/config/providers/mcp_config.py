from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",   # .env içinde fazla değişken varsa sorun çıkarmaz
    )

    # Memory MCP Settings
    memory_mcp_name: str = Field(
        default="memory-server",
        validation_alias="MEMORY_MCP_NAME",
    )
    memory_mcp_version: str = Field(
        default="1.0.0",
        validation_alias="MEMORY_MCP_VERSION",
    )
    memory_mcp_host: str = Field(
        default="localhost",
        validation_alias="MEMORY_MCP_HOST",
    )
    memory_mcp_port: int = Field(
        default=8080,
        validation_alias="MEMORY_MCP_PORT",
    )
    memory_mcp_log: str = Field(
        default="info",
        validation_alias="MEMORY_MCP_LOG",
    )
    memory_mcp_transport: Literal[
        "stdio", "http", "sse", "streamable-http"
    ] = Field(
        default="streamable-http",
        validation_alias="MEMORY_MCP_TRANSPORT",
    )

    # RAG MCP Settings
    rag_mcp_name: str = Field(
        default="rag-server",
        validation_alias="RAG_MCP_NAME",
    )
    rag_mcp_version: str = Field(
        default="1.0.0",
        validation_alias="RAG_MCP_VERSION",
    )
    rag_mcp_host: str = Field(
        default="localhost",
        validation_alias="RAG_MCP_HOST",
    )
    rag_mcp_port: int = Field(
        default=8055,
        validation_alias="RAG_MCP_PORT",
    )
    rag_mcp_log: str = Field(
        default="info",
        validation_alias="RAG_MCP_LOG",
    )
    rag_mcp_transport: Literal[
        "stdio", "http", "sse", "streamable-http"
    ] = Field(
        default="streamable-http",
        validation_alias="RAG_MCP_TRANSPORT",
    )


mcp_config = MCPConfig()
