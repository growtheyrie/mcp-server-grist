"""
Export and download tools for the Grist API.

This module contains MCP tools for exporting and downloading
Grist documents and tables in various formats.
"""

import base64
import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configure the logger
logger = logging.getLogger("grist_mcp_server")


def register_export_tools(mcp_server):
    """
    Saves all export tools to the MCP server.

    Args:
        mcp_server: The instance of the server to save the tools to.
    """
    mcp_server.tool()(download_document_sqlite)
    mcp_server.tool()(download_document_excel)
    mcp_server.tool()(download_table_csv)


async def download_document_sqlite(
    doc_id: str,
    nohistory: bool = False,
    template: bool = False,
    ctx=None
) -> Dict[str, Any]:
    """
    Downloads a Grist document in SQLite format.

    Prerequisites:
        - list_documents: To obtain a valid doc_id

    Args:
        - doc_id: The ID of the document
        - nohistory: If True, excludes change history
        - template: If True, download as a template (without user data)

    Returns:
        Dict with status, message, and content encoded in base64
    """
    logger.info(f"Tool called: download_document_sqlite with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        content = await client.download_doc(doc_id, nohistory=nohistory, template=template)

        # Encode binary content in base64
        encoded_content = base64.b64encode(content).decode('utf-8')

        return {
            "success": True,
            "message": f"Document {doc_id} successfully downloaded in SQLite format",
            "content_type": "application/x-sqlite3",
            "filename": f"{doc_id}.sqlite",
            "content_base64": encoded_content,
            "size_bytes": len(content)
        }
    except Exception as e:
        logger.error(f"Error downloading document as SQLite: {e}")
        return {
            "success": False,
            "message": f"Error downloading document in SQLite format: {str(e)}"
        }


async def download_document_excel(
    doc_id: str,
    header: str = "label",
    ctx=None
) -> Dict[str, Any]:
    """
    Downloads a Grist document in Excel format.

    Prerequisites:
        - list_documents: To obtain a valid doc_id

    Args:
        - doc_id: The ID of the document
        - header: Header format (label, id, or none)

    Returns:
        Dict with status, message, and content encoded in base64
    """
    logger.info(f"Tool called: download_document_excel with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        if header not in ["colId", "label"]:
            return {
                "success": False,
                "message": "Invalid header format. Must be: colId or label"
            }

        content = await client.download_doc_xlsx(doc_id, header=header)

        # Encode binary content in base64
        encoded_content = base64.b64encode(content).decode('utf-8')

        return {
            "success": True,
            "message": f"Document {doc_id} successfully downloaded in Excel format",
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "filename": f"{doc_id}.xlsx",
            "content_base64": encoded_content,
            "size_bytes": len(content)
        }
    except Exception as e:
        logger.error(f"Error downloading document as Excel: {e}")
        return {
            "success": False,
            "message": f"Error downloading document in Excel format: {str(e)}"
        }


async def download_table_csv(
    doc_id: str,
    table_id: str,
    header: str = "label",
    ctx=None
) -> Dict[str, Any]:
    """
    Downloads a Grist table in CSV format.

    Prerequisites:
        - list_documents: To obtain a valid doc_id
        - list_tables: To obtain a valid table_id

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID
        - header: Header format (colId or label, default: label)

    Returns:
        Dict with status, message, and CSV content
    """
    logger.info(f"Tool called: download_table_csv with doc_id: {doc_id}, table_id: {table_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        if header not in ["colId", "label"]:
            return {
                "success": False,
                "message": "Invalid header format. Must be: colId or label"
            }

        content = await client.download_table_csv(doc_id, table_id, header=header)

        return {
            "success": True,
            "message": f"Table {table_id} of document {doc_id} successfully downloaded in CSV format",
            "content_type": "text/csv",
            "filename": f"{table_id}.csv",
            "content": content,
            "size_bytes": len(content.encode('utf-8'))
        }
    except Exception as e:
        logger.error(f"Error downloading table as CSV: {e}")
        return {
            "success": False,
            "message": f"Error downloading table in CSV format: {str(e)}"
        }
