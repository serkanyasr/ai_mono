#!/bin/bash
set -e

echo "Starting MCP Memory Server..."

# Wait for database to be ready
echo "Waiting for Memory PostgreSQL..."
until pg_isready -h ${MEMORY_DB_HOST:-memory_postgres} -p ${MEMORY_DB_PORT:-5432} -U ${MEMORY_DB_USER:-postgres}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up!"

# Start MCP Memory Server
exec python -m src.mcp.memory.memory_server
