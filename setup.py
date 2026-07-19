"""Compatibility setup for older tools. Prefer pyproject.toml."""

from setuptools import setup, find_packages

setup(
    name="proxmox-mcp-server",
    version="0.3.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "mcp>=0.2.0",
        "proxmoxer>=2.0.1,<3.0.0",
        "requests>=2.31.0,<3.0.0",
        "pydantic>=2.0.0,<3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "proxmox-mcp=proxmox_mcp.server:main",
            "proxmox-mcp-server=proxmox_mcp.server:main",
        ],
    },
)
