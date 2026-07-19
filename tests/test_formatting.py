"""Formatting smoke tests."""
from proxmox_mcp.formatting import ProxmoxTemplates, ProxmoxFormatters


def test_templates_empty_safe():
    assert isinstance(ProxmoxTemplates.node_list([]), str)
    assert isinstance(ProxmoxTemplates.vm_list([]), str)
    assert isinstance(ProxmoxTemplates.storage_list([]), str)
    assert isinstance(ProxmoxTemplates.container_list([]), str)
    assert isinstance(ProxmoxTemplates.cluster_status({"name": "c", "nodes": 1}), str)


def test_templates_with_data():
    nodes = [{"node": "pve", "status": "online", "cpu": 0.1, "maxcpu": 4, "mem": 1, "maxmem": 2}]
    assert "pve" in ProxmoxTemplates.node_list(nodes)
    vms = [{"vmid": 100, "name": "vm", "status": "running", "node": "pve", "cpus": 1, "memory": {"used": 1, "total": 2}}]
    assert ProxmoxTemplates.vm_list(vms)
    storage = [{"storage": "local", "type": "dir", "content": ["iso"], "status": "online", "used": 1, "total": 2, "available": 1}]
    assert ProxmoxTemplates.storage_list(storage)
    assert ProxmoxTemplates.node_status("pve", {"uptime": 1, "cpu": 0.1, "memory": {"used": 1, "total": 2}})


def test_format_command_output():
    text = ProxmoxFormatters.format_command_output(True, "echo", "hi", None)
    assert "echo" in text or "hi" in text
    err = ProxmoxFormatters.format_command_output(False, "bad", "", "oops")
    assert "oops" in err or "bad" in err
