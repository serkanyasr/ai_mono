from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()


class MCPConfig(BaseSettings):

    memory_mcp_name: str = Field(
        default="memory-server", env="MEMORY_MCP_NAME")
    memory_mcp_version: str = Field(default="1.0.0", env="MEMORY_MCP_VERSION")
    memory_mcp_host: str = Field(default="localhost", env="MEMORY_MCP_HOST")
    memory_mcp_port: int = Field(default=8080, env="MEMORY_MCP_PORT")
    memory_mcp_log: str = Field(default="info", env="MEMORY_MCP_LOG")
    memory_mcp_transport: str = Field(
        default="stdio", env="MEMORY_MCP_TRANSPORT")


mcp_config = MCPConfig()
