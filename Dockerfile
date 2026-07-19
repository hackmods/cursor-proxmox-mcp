# Production image for cursor-proxmox-mcp (stdio MCP; mount config at runtime)
FROM python:3.12-slim

LABEL org.opencontainers.image.title="cursor-proxmox-mcp" \
      org.opencontainers.image.description="Formal Cursor MCP server for Proxmox VE" \
      org.opencontainers.image.source="https://github.com/hackmods/cursor-proxmox-mcp" \
      io.modelcontextprotocol.server.name="io.github.hackmods/cursor-proxmox-mcp"

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

ENV PROXMOX_MCP_CONFIG=/config/config.json

ENTRYPOINT ["cursor-proxmox-mcp"]
