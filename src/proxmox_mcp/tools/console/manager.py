"""
Module for managing VM console operations via QEMU guest agent.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from ..helpers import check_exec_allowlist, qemu_not_found_message


class VMConsoleManager:
    """Execute commands in a VM via QEMU guest agent."""

    def __init__(self, proxmox_api: Any):
        self.proxmox = proxmox_api
        self.logger = logging.getLogger("proxmox-mcp.vm-console")

    async def execute_command(self, node: str, vmid: str, command: str) -> Dict[str, Any]:
        """Execute a command in a VM's console via QEMU guest agent."""
        try:
            check_exec_allowlist(command)

            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            if vm_status["status"] != "running":
                self.logger.error("Failed to execute command on VM %s: VM is not running", vmid)
                raise ValueError(f"VM {vmid} on node {node} is not running")

            truncated = command if len(command) <= 120 else command[:117] + "..."
            self.logger.warning(
                "Executing guest command on VM %s (node=%s): %s", vmid, node, truncated
            )

            endpoint = self.proxmox.nodes(node).qemu(vmid).agent
            try:
                exec_result = endpoint("exec").post(command=command)
            except Exception as e:
                raise RuntimeError(f"Failed to start command: {e}") from e

            if "pid" not in exec_result:
                raise RuntimeError("No PID returned from command execution")

            pid = exec_result["pid"]
            timeout = float(os.environ.get("PROXMOX_MCP_EXEC_TIMEOUT", "30"))
            poll_interval = 0.5
            elapsed = 0.0
            console: Optional[Dict[str, Any]] = None

            while elapsed < timeout:
                try:
                    console = endpoint("exec-status").get(pid=pid)
                except Exception as e:
                    raise RuntimeError(f"Failed to get command status: {e}") from e
                if not console:
                    raise RuntimeError("No response from exec-status")
                if console.get("exited"):
                    break
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            else:
                raise RuntimeError(
                    f"Command timed out after {timeout}s (PID {pid}). "
                    "Increase PROXMOX_MCP_EXEC_TIMEOUT if needed."
                )

            output = console.get("out-data", "") if isinstance(console, dict) else str(console)
            error = console.get("err-data", "") if isinstance(console, dict) else ""
            exit_code = console.get("exitcode", 0) if isinstance(console, dict) else 0
            try:
                exit_code_int = int(exit_code)
            except (TypeError, ValueError):
                exit_code_int = 1 if exit_code else 0

            return {
                "success": exit_code_int == 0,
                "output": output,
                "error": error,
                "exit_code": exit_code_int,
            }

        except ValueError:
            raise
        except Exception as e:
            self.logger.error("Failed to execute command on VM %s: %s", vmid, e)
            if "not found" in str(e).lower():
                raise ValueError(qemu_not_found_message(vmid, node)) from e
            raise RuntimeError(f"Failed to execute command: {e}") from e
