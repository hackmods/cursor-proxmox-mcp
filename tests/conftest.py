"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from tests.fakes.proxmox import make_fake_proxmox


@pytest.fixture
def fake_api():
    return make_fake_proxmox()


@pytest.fixture
def fake_api_with_vm():
    return make_fake_proxmox(qemu={"100": {"name": "vm100", "status": "running", "cores": 2}})


@pytest.fixture
def fake_api_stopped_vm():
    return make_fake_proxmox(qemu={"100": {"name": "vm100", "status": "stopped", "cores": 2}})
