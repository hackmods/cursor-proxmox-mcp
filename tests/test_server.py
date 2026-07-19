"""
Tests for the Proxmox MCP server.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from proxmox_mcp.server import ProxmoxMCPServer
from proxmox_mcp.config.models import Config, ProxmoxConfig, AuthConfig, LoggingConfig

@pytest.fixture
def mock_config():
    """Fixture to create a mock configuration."""
    return Config(
        proxmox=ProxmoxConfig(
            host="test.proxmox.com",
            port=8006,
            verify_ssl=False,
            service="pve"
        ),
        auth=AuthConfig(
            user="test@pve",
            token_name="test_token",
            token_value="test_value"
        ),
        logging=LoggingConfig(
            level="DEBUG"
        )
    )

@pytest.fixture
def mock_env_vars():
    """Fixture to set up test environment variables."""
    env_vars = {
        "PROXMOX_HOST": "test.proxmox.com",
        "PROXMOX_USER": "test@pve",
        "PROXMOX_TOKEN_NAME": "test_token",
        "PROXMOX_TOKEN_VALUE": "test_value",
        "LOG_LEVEL": "DEBUG"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_proxmox():
    """Fixture to mock ProxmoxAPI."""
    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as mock:
        # Create a mock instance
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock nodes endpoint
        mock_instance.nodes.get.return_value = [
            {"node": "node1", "status": "online"},
            {"node": "node2", "status": "online"}
        ]
        
        # Mock node status
        mock_instance.nodes.return_value.status.get.return_value = {
            "status": "running",
            "uptime": 123456
        }
        
        # Mock VMs
        mock_instance.nodes.return_value.qemu.get.return_value = [
            {"vmid": "100", "name": "vm1", "status": "running"},
            {"vmid": "101", "name": "vm2", "status": "stopped"}
        ]
        
        # Mock containers
        mock_instance.nodes.return_value.lxc.get.return_value = [
            {"vmid": "200", "name": "container1", "status": "running", "mem": 0, "maxmem": 2147483648},
            {"vmid": "201", "name": "container2", "status": "stopped", "mem": 0, "maxmem": 2147483648}
        ]
        mock_instance.nodes.return_value.lxc.return_value.config.get.return_value = {
            "hostname": "container1",
            "cores": 2,
            "features": "nesting=1",
        }
        mock_instance.nodes.return_value.lxc.return_value.status.current.get.return_value = {
            "status": "stopped",
            "name": "container1",
        }
        mock_instance.nodes.return_value.lxc.return_value.status.start.post.return_value = (
            "UPID:node1:000:000:start:200:"
        )
        mock_instance.nodes.return_value.lxc.return_value.status.stop.post.return_value = (
            "UPID:node1:000:000:stop:200:"
        )
        mock_instance.nodes.return_value.lxc.return_value.delete.return_value = (
            "UPID:node1:000:000:vzdestroy:200:"
        )
        mock_instance.nodes.return_value.lxc.return_value.config.put.return_value = None
        
        # Mock storage with proper numeric values
        mock_instance.storage.get.return_value = [
            {"storage": "local", "type": "dir", "enabled": True},
            {"storage": "ceph", "type": "rbd", "enabled": True}
        ]
        
        # Mock storage status with numeric values
        mock_instance.nodes.return_value.storage.return_value.status.get.return_value = {
            "used": 1000000000,  # 1GB
            "total": 10000000000,  # 10GB
            "avail": 9000000000   # 9GB
        }
        
        # Mock cluster status as a list (not dict)
        mock_instance.cluster.status.get.return_value = [
            {"name": "test-cluster", "quorate": 1, "nodes": 2}
        ]
        
        # Mock VM status for command execution
        mock_instance.nodes.return_value.qemu.return_value.status.current.get.return_value = {
            "status": "running"
        }
        
        # Mock VM command execution
        mock_instance.nodes.return_value.qemu.return_value.agent.return_value.post.return_value = {
            "pid": 12345
        }
        mock_instance.nodes.return_value.qemu.return_value.agent.return_value.get.return_value = {
            "out-data": "command output",
            "err-data": "",
            "exitcode": 0,
            "exited": 1
        }
        
        yield mock

@pytest.fixture
def server(mock_config, mock_proxmox):
    """Fixture to create a ProxmoxMCPServer instance."""
    with patch("proxmox_mcp.server.load_config", return_value=mock_config):
        return ProxmoxMCPServer()

def test_server_initialization(server, mock_proxmox):
    """Test server initialization with environment variables."""
    assert server.config.proxmox.host == "test.proxmox.com"
    assert server.config.auth.user == "test@pve"
    assert server.config.auth.token_name == "test_token"
    assert server.config.auth.token_value == "test_value"
    assert server.config.logging.level == "DEBUG"

    mock_proxmox.assert_called_once()

@pytest.mark.asyncio
async def test_list_tools(server):
    """Test listing available tools."""
    tools = await server.mcp.list_tools()

    assert len(tools) > 0
    tool_names = [tool.name for tool in tools]
    assert "get_nodes" in tool_names
    assert "get_vms" in tool_names
    assert "get_containers" in tool_names
    assert "create_lxc" in tool_names
    assert "start_lxc" in tool_names
    assert "stop_lxc" in tool_names
    assert "shutdown_lxc" in tool_names
    assert "reboot_lxc" in tool_names
    assert "delete_lxc" in tool_names
    assert "update_lxc_features" in tool_names
    assert "get_storage" in tool_names
    assert "execute_vm_command" in tool_names

@pytest.mark.asyncio
async def test_get_nodes(server, mock_proxmox):
    """Test get_nodes tool."""
    response = await server.mcp.call_tool("get_nodes", {})

    assert len(response) == 1
    assert response[0].type == "text"
    assert "node1" in response[0].text
    assert "node2" in response[0].text
    assert "Proxmox Nodes" in response[0].text

@pytest.mark.asyncio
async def test_get_node_status_missing_parameter(server):
    """Test get_node_status tool with missing parameter."""
    with pytest.raises(ToolError, match="Field required"):
        await server.mcp.call_tool("get_node_status", {})

@pytest.mark.asyncio
async def test_get_node_status(server, mock_proxmox):
    """Test get_node_status tool with valid parameter."""
    response = await server.mcp.call_tool("get_node_status", {"node": "node1"})
    
    assert len(response) == 1
    assert response[0].type == "text"
    assert "node1" in response[0].text
    assert "RUNNING" in response[0].text

@pytest.mark.asyncio
async def test_get_vms(server, mock_proxmox):
    """Test get_vms tool."""
    response = await server.mcp.call_tool("get_vms", {})
    
    assert len(response) == 1
    assert response[0].type == "text"
    assert "vm1" in response[0].text
    assert "vm2" in response[0].text
    assert "Virtual Machines" in response[0].text

@pytest.mark.asyncio
async def test_get_containers(server, mock_proxmox):
    """Test get_containers tool."""
    response = await server.mcp.call_tool("get_containers", {})

    assert len(response) == 1
    assert response[0].type == "text"
    assert "container1" in response[0].text
    assert "Containers" in response[0].text

@pytest.mark.asyncio
async def test_start_lxc(server, mock_proxmox):
    """Test start_lxc tool."""
    response = await server.mcp.call_tool("start_lxc", {"node": "node1", "vmid": "200"})

    assert len(response) == 1
    assert response[0].type == "text"
    assert "200" in response[0].text
    assert "start" in response[0].text.lower()
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.status.start.post.assert_called()

@pytest.mark.asyncio
async def test_stop_lxc(server, mock_proxmox):
    """Test stop_lxc tool when container is running."""
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running",
        "name": "container1",
    }
    response = await server.mcp.call_tool("stop_lxc", {"node": "node1", "vmid": "200"})

    assert len(response) == 1
    assert "stop" in response[0].text.lower()
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.status.stop.post.assert_called()

@pytest.mark.asyncio
async def test_delete_lxc(server, mock_proxmox):
    """Test delete_lxc tool for a stopped container."""
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "stopped",
        "name": "container1",
    }
    response = await server.mcp.call_tool("delete_lxc", {"node": "node1", "vmid": "200"})

    assert len(response) == 1
    assert "deletion" in response[0].text.lower() or "deleting" in response[0].text.lower()
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.delete.assert_called()

@pytest.mark.asyncio
async def test_update_lxc_features(server, mock_proxmox):
    """Test update_lxc_features tool."""
    response = await server.mcp.call_tool(
        "update_lxc_features",
        {"node": "node1", "vmid": "200", "features": "nesting=1,keyctl=1"},
    )

    assert len(response) == 1
    assert "features updated" in response[0].text.lower()
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.config.put.assert_called_with(
        features="nesting=1,keyctl=1"
    )

@pytest.mark.asyncio
async def test_get_storage(server, mock_proxmox):
    """Test get_storage tool."""
    response = await server.mcp.call_tool("get_storage", {})
    
    assert len(response) == 1
    assert response[0].type == "text"
    assert "local" in response[0].text
    assert "ceph" in response[0].text
    assert "Storage Pools" in response[0].text

@pytest.mark.asyncio
async def test_get_cluster_status(server, mock_proxmox):
    """Test get_cluster_status tool."""
    response = await server.mcp.call_tool("get_cluster_status", {})
    
    assert len(response) == 1
    assert response[0].type == "text"
    assert "test-cluster" in response[0].text

@pytest.mark.asyncio
async def test_execute_vm_command_success(server, mock_proxmox):
    """Test successful VM command execution."""
    response = await server.mcp.call_tool("execute_vm_command", {
        "node": "node1",
        "vmid": "100",
        "command": "ls -l"
    })
    
    assert len(response) == 1
    assert response[0].type == "text"
    assert "SUCCESS" in response[0].text
    assert "command output" in response[0].text
    assert "ls -l" in response[0].text

@pytest.mark.asyncio
async def test_execute_vm_command_missing_parameters(server):
    """Test VM command execution with missing parameters."""
    with pytest.raises(ToolError):
        await server.mcp.call_tool("execute_vm_command", {})

@pytest.mark.asyncio
async def test_execute_vm_command_vm_not_running(server, mock_proxmox):
    """Test VM command execution when VM is not running."""
    # Override the default mock for this test
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }

    with pytest.raises(ToolError, match="not running"):
        await server.mcp.call_tool("execute_vm_command", {
            "node": "node1",
            "vmid": "100",
            "command": "ls -l"
        })

@pytest.mark.asyncio
async def test_execute_vm_command_with_error(server, mock_proxmox):
    """Test VM command execution with command error."""
    # Override the default mock for this test
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.agent.return_value.get.return_value = {
        "out-data": "",
        "err-data": "command not found",
        "exitcode": 1,
        "exited": 1
    }

    response = await server.mcp.call_tool("execute_vm_command", {
        "node": "node1",
        "vmid": "100",
        "command": "invalid-command"
    })
    
    assert len(response) == 1
    assert response[0].type == "text"
    assert "SUCCESS" in response[0].text  # API call succeeded
    assert "command not found" in response[0].text
    assert "invalid-command" in response[0].text
