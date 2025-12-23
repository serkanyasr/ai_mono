#!/bin/bash
set -e

echo "Starting MCP RAG Server..."

# Wait for database to be ready
echo "Waiting for RAG PostgreSQL..."
until pg_isready -h ${RAG_DB_HOST:-rag_postgres} -p ${RAG_DB_PORT:-5432} -U ${RAG_DB_USER:-postgres}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up!"

# Start MCP RAG Server
exec python -m src.mcp.rag.rag_server
