"""Access token secret must not be logged at INFO."""
import logging

from proxmox_mcp.tools.access import AccessTools
from tests.fakes.proxmox import make_fake_proxmox


def test_create_token_banner_and_no_secret_in_logs(caplog):
    tools = AccessTools(make_fake_proxmox())
    with caplog.at_level(logging.INFO):
        out = tools.create_token("u@pve", "tok")
    assert "SECURITY" in out[0].text or "Store the secret" in out[0].text
    assert "secret-once" not in caplog.text
