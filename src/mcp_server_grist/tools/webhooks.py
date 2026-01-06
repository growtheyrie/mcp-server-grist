"""
Webhook management tools for the Grist API.

This module contains MCP tools for managing webhooks in
Grist documents: listing, creating, editing, and deleting.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configure the logger
logger = logging.getLogger("grist_mcp_server")


def register_webhook_tools(mcp_server):
    """
    Registers all webhook management tools in the MCP server.

    Args:
        mcp_server: The instance of the MCP server to save the tools to.
    """
    mcp_server.tool()(list_webhooks)
    mcp_server.tool()(create_webhook)
    mcp_server.tool()(modify_webhook)
    mcp_server.tool()(delete_webhook)
    mcp_server.tool()(clear_webhook_queue)


async def list_webhooks(doc_id: str, ctx=None) -> Dict[str, Any]:
    """
    Lists the webhooks of a Grist document.

    Prerequisites:
        - list_documents: To obtain a valid doc_id

    Args:
        - doc_id: The ID of the document

    Returns:
        Dict with status, message, and list of webhooks
    """
    logger.info(f"Tool called: list_webhooks with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured",
                "webhooks": []
            }

        webhooks = await client.list_webhooks(doc_id)

        return {
            "success": True,
            "message": f"{len(webhooks)} webhooks found in the document {doc_id}",
            "webhooks": webhooks
        }
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        return {
            "success": False,
            "message": f"Error retrieving webhooks in document {doc_id}: {str(e)}",
            "webhooks": []
        }


async def create_webhook(
    doc_id: str,
    url: str,
    table_id: str,
    event_types: List[str] = ["add"],
    memo: Optional[str] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a webhook for a Grist document.

    Prerequisites:
        - list_documents: To obtain a valid doc_id
        - list_tables: To obtain a valid table_id

    Args:
        - doc_id: The ID of the document
        - URL: URL of the webhook (where notifications will be sent)
        - table_id: ID of the table to monitor
        - event_types: Types of events to monitor (default: ["add"])
        - Possible event type values: ["add", "update"]
        - Memo: Descriptive note for the webhook (optional)

    Returns:
        Dict with status, message, and ID of the created webhook
    """
    logger.info(f"Tool called: create_webhook with doc_id: {doc_id}, url: {url}, table_id: {table_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        # Validate event types
        valid_event_types = ["add", "update"]
        if event_types:
            for event_type in event_types:
                if event_type not in valid_event_types:
                    return {
                        "success": False,
                        "message": f"Invalid event type: {event_type}. Must be among: {valid_event_types}"
                    }

        # Prepare webhook data
        webhook_data = {
            "url": url,
            "tableId": table_id,
            "eventTypes": event_types
        }

        if memo:
            webhook_data["memo"] = memo

        # Create the webhook
        result = await client.create_webhooks(doc_id, [webhook_data])

        if result and len(result) > 0:
            webhook_id = result[0].get("id")
            return {
                "success": True,
                "message": f"Webhook successfully created for URL {url}",
                "webhook_id": webhook_id,
                "webhook": result[0]
            }
        else:
            return {
                "success": False,
                "message": "No webhook has been created"
            }
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        return {
            "success": False,
            "message": f"Error creating webhook: {str(e)}"
        }


async def modify_webhook(
    doc_id: str,
    webhook_id: str,
    url: Optional[str] = None,
    table_id: Optional[str] = None,
    event_types: Optional[List[str]] = None,
    memo: Optional[str] = None,
    active: Optional[bool] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies an existing webhook.

    Prerequisites:
        - list_webhooks: To obtain a valid webhook_id

    Args:
        - doc_id: The ID of the document
        - webhook_id: The ID of the webhook to modify
        - URL: New webhook URL (optional)
        - table_id: New table ID to monitor (optional)
        - event_types: New types of events to monitor (optional)
        - Memo: New descriptive note (optional)
        - active: Webhook activation status (optional)

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_webhook with doc_id: {doc_id}, webhook_id: {webhook_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        # Validate event types
        valid_event_types = ["add", "update"]
        if event_types:
            for event_type in event_types:
                if event_type not in valid_event_types:
                    return {
                        "success": False,
                        "message": f"Invalid event type: {event_type}. Must be among: {valid_event_types}"
                    }

        # Prepare webhook data
        webhook_data = {}

        if url is not None:
            webhook_data["url"] = url

        if table_id is not None:
            webhook_data["tableId"] = table_id

        if event_types is not None:
            webhook_data["eventTypes"] = event_types

        if memo is not None:
            webhook_data["memo"] = memo

        if active is not None:
            webhook_data["active"] = active

        if not webhook_data:
            return {
                "success": False,
                "message": "No update provided"
            }

        # Edit the webhook
        await client.modify_webhook(doc_id, webhook_id, webhook_data)

        return {
            "success": True,
            "message": f"Webhook {webhook_id} successfully modified"
        }
    except Exception as e:
        logger.error(f"Error modifying webhook: {e}")
        return {
            "success": False,
            "message": f"Error modifying webhook: {str(e)}"
        }


async def delete_webhook(
    doc_id: str,
    webhook_id: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes a webhook.

    Prerequisites:
        - list_webhooks: To obtain a valid webhook_id

    Args:
        - doc_id: The ID of the document
        - webhook_id: The ID of the webhook to delete

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_webhook with doc_id: {doc_id}, webhook_id: {webhook_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        result = await client.delete_webhook(doc_id, webhook_id)

        return {
            "success": True,
            "message": f"Webhook {webhook_id} successfully deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return {
            "success": False,
            "message": f"Error deleting webhook: {str(e)}"
        }


async def clear_webhook_queue(
    doc_id: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Clears the webhook queue from a document.

    Useful where undelivered payloads accumulate.

    Args:
        - doc_id: The ID of the document

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: clear_webhook_queue with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.clear_webhook_queue(doc_id)

        return {
            "success": True,
            "message": f"Webhook queue successfully purged from document {doc_id}"
        }
    except Exception as e:
        logger.error(f"Error clearing webhook queue: {e}")
        return {
            "success": False,
            "message": f"Error clearing webhook queue: {str(e)}"
        }
