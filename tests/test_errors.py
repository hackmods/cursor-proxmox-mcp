"""Unit tests for errors and sanitization."""
from proxmox_mcp.errors import (
    ProxmoxAPIError,
    ProxmoxAuthError,
    ProxmoxNotFoundError,
    ProxmoxPermissionError,
    classify_proxmox_error,
    sanitize_error_message,
)


def test_sanitize_token_value():
    assert "***" in sanitize_error_message("token_value=abc-secret-here")


def test_sanitize_password():
    assert "***" in sanitize_error_message("password=hunter2")


def test_classify_not_found():
    err = classify_proxmox_error("get vm", Exception("VM does not exist"))
    assert isinstance(err, ProxmoxNotFoundError)


def test_classify_permission():
    err = classify_proxmox_error("delete", Exception("403 permission denied"))
    assert isinstance(err, ProxmoxPermissionError)


def test_classify_auth():
    err = classify_proxmox_error("connect", Exception("401 unauthorized"))
    assert isinstance(err, ProxmoxAuthError)


def test_classify_api():
    err = classify_proxmox_error("x", Exception("boom"))
    assert isinstance(err, ProxmoxAPIError)
    assert "Failed to x" in str(err)
