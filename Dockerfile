# Production image for proxmox-mcp-server (stdio MCP; mount config at runtime)
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

ENV PROXMOX_MCP_CONFIG=/config/config.json

ENTRYPOINT ["proxmox-mcp-server"]
