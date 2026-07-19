"""Config loader tests."""
import json

import pytest

from proxmox_mcp.config.loader import expand_env_vars, load_config


def test_expand_env_vars(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert expand_env_vars({"a": "${FOO}"}) == {"a": "bar"}


def test_expand_missing_env():
    with pytest.raises(ValueError, match="not set"):
        expand_env_vars("${NO_SUCH_VAR_XYZ}")


def test_load_config_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("TOK", "secret")
    cfg = {
        "proxmox": {"host": "10.0.0.1", "port": 8006, "verify_ssl": True, "service": "PVE"},
        "auth": {"user": "u@pve", "token_name": "t", "token_value": "${TOK}"},
        "logging": {"level": "INFO"},
    }
    path = tmp_path / "c.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    loaded = load_config(str(path))
    assert loaded.proxmox.host == "10.0.0.1"
    assert loaded.auth.token_value == "secret"


def test_load_config_missing_host(tmp_path):
    cfg = {
        "proxmox": {"host": "", "port": 8006},
        "auth": {"user": "u@pve", "token_name": "t", "token_value": "v"},
        "logging": {"level": "INFO"},
    }
    path = tmp_path / "c.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="host"):
        load_config(str(path))


def test_load_config_requires_path():
    with pytest.raises(ValueError, match="PROXMOX_MCP_CONFIG"):
        load_config(None)


def test_load_bad_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(str(path))
