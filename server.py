"""
Root-level entrypoint for FastMCP deployment.
This file exists before package installation to pass validation,
then imports from the installed package at runtime.
"""

from mcp_server_grist.server import create_mcp_server

# Expose the function at module level
__all__ = ["create_mcp_server"]
