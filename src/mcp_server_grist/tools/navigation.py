"""
Outils de navigation pour l'API Grist.

Ce module contient des outils MCP pour naviguer dans la structure hiérarchique de Grist:
organisations, espaces de travail, documents, tables, colonnes et enregistrements.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client
from ..models import MCP_Response

# Configurer le logger
logger = logging.getLogger("grist_mcp_server")

def register_navigation_tools(mcp_server):
    """
    Enregistre tous les outils de navigation sur le serveur MCP.
    
    Args:
        mcp_server: L'instance du serveur MCP sur laquelle enregistrer les outils.
    """
    # Enregistrement des outils sur le serveur MCP
    mcp_server.tool()(list_organizations)
    mcp_server.tool()(describe_organization)
    mcp_server.tool()(list_workspaces)
    mcp_server.tool()(describe_workspace)
    mcp_server.tool()(list_documents)
    mcp_server.tool()(describe_document)
    mcp_server.tool()(list_tables)
    mcp_server.tool()(list_columns)
    mcp_server.tool()(list_records)
    mcp_server.tool()(get_table_schema)


async def list_organizations(ctx=None) -> Dict[str, Any]:
    """
    Lists all accessible Grist organizations.

    Prerequisites:

    None - this tool is the main entry point for navigation.

    Typical workflow:

        1. list_organizations() → get all available org_ids

        2. list_workspaces(org_id) → explore workspaces

    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - organizations (List): List of available organizations
    """
    logger.info("Tool called: list_organizations")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "organizations": []
            }
        
        orgs = await client.list_orgs()
        
        return {
            "success": True,
            "message": f"Found {len(orgs)} organizations",
            "organizations": [org.model_dump() for org in orgs]
        }
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        return {
            "success": False,
            "message": f"Error listing organizations: {str(e)}",
            "organizations": []
        }


async def describe_organization(org_id: Union[int, str], ctx=None) -> Dict[str, Any]:
    """
    Gets detailed information about a specific organization.

    Prerequisites:

        - list_organizations: To obtain a valid org_id

    Typical workflow:

        1. list_organizations() → identify the organization

        2. describe_organization(org_id) → get details

    Args:

        org_id: The ID of the organization to be described



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - organization (Dict): Organization details
    """
    logger.info(f"Tool called: describe_organization with org_id: {org_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        org_details = await client.describe_org(org_id)
        
        return {
            "success": True,
            "message": f"Found organization details for {org_id}",
            "organization": org_details
        }
    except Exception as e:
        logger.error(f"Error describing organization: {e}")
        return {
            "success": False,
            "message": f"Error describing organization {org_id}: {str(e)}"
        }


async def list_workspaces(org_id: Union[int, str], ctx=None) -> Dict[str, Any]:
    """
    Lists all workspaces in a Grist organization.

    Prerequisites:

        - list_organizations: To obtain a valid org_id



    Typical workflow:

        1. list_organizations() → choose org_id

        2. list_workspaces(org_id) → get workspace_id

        3. list_documents(workspace_id) → navigate through documents

    See also:

        - create_workspace: To create a new workspace

        - describe_workspace: To get the details of a workspace

        - modify_workspace_access: To manage permissions

    Args:

        org_id: The organization ID (integer or subdomain string)



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - workspaces (List): List of workspaces
    """
    logger.info(f"Tool called: list_workspaces with org_id: {org_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "workspaces": []
            }
        
        workspaces = await client.list_workspaces(org_id)
        
        return {
            "success": True,
            "message": f"Found {len(workspaces)} workspaces in organization {org_id}",
            "workspaces": [workspace.model_dump() for workspace in workspaces]
        }
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        return {
            "success": False,
            "message": f"Error listing workspaces for organization {org_id}: {str(e)}",
            "workspaces": []
        }


async def describe_workspace(workspace_id: int, ctx=None) -> Dict[str, Any]:
    """
    Gets detailed information about a specific workspace.

    Prerequisites:

        - list_workspaces: To obtain a valid workspace_id

    Typical workflow:

        1. list_organizations() → identify the organization

        2. list_workspaces(org_id) → identify the workspace

        3. describe_workspace(workspace_id) → get details

    Args:

        workspace_id: The ID of the workspace to describe



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - workspace (Dict): Workspace details
    """
    logger.info(f"Tool called: describe_workspace with workspace_id: {workspace_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        workspace_details = await client.describe_workspace(workspace_id)
        
        return {
            "success": True,
            "message": f"Found workspace details for {workspace_id}",
            "workspace": workspace_details
        }
    except Exception as e:
        logger.error(f"Error describing workspace: {e}")
        return {
            "success": False,
            "message": f"Error describing workspace {workspace_id}: {str(e)}"
        }


async def list_documents(workspace_id: int, ctx=None) -> Dict[str, Any]:
    """
    Lists all documents in a Grist workspace.

    Prerequisites:

        - list_workspaces: To obtain a valid workspace_id



    Typical workflow:

        1. list_workspaces(org_id) → get workspace_id

        2. list_documents(workspace_id) → get doc_id

        3. list_tables(doc_id) → explore the document tables

    See also:

        - create_document: To create a new document

        - describe_document: To get the details of a document

        - modify_document_access: To manage permissions

    Args:

        workspace_id: The ID of the workspace



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - documents (List): List of documents
    """
    logger.info(f"Tool called: list_documents with workspace_id: {workspace_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "documents": []
            }
        
        documents = await client.list_documents(workspace_id)
        
        return {
            "success": True,
            "message": f"Found {len(documents)} documents in workspace {workspace_id}",
            "documents": [document.model_dump() for document in documents]
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return {
            "success": False,
            "message": f"Error listing documents for workspace {workspace_id}: {str(e)}",
            "documents": []
        }


async def describe_document(doc_id: str, ctx=None) -> Dict[str, Any]:
    """
    Gets detailed information about a specific document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id

    Typical workflow:

        1. list_workspaces(org_id) → identify the workspace

        2. list_documents(workspace_id) → identify the document

        3. describe_document(doc_id) → get details

    Args:

        doc_id: The ID of the document to be described



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - document (Dict): Document details
    """
    logger.info(f"Tool called: describe_document with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        document_details = await client.describe_doc(doc_id)
        
        return {
            "success": True,
            "message": f"Found document details for {doc_id}",
            "document": document_details
        }
    except Exception as e:
        logger.error(f"Error describing document: {e}")
        return {
            "success": False,
            "message": f"Error describing document {doc_id}: {str(e)}"
        }


async def list_tables(doc_id: str, ctx=None) -> Dict[str, Any]:
    """
    Lists all tables in a Grist document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id



    Typical workflow:

        1. list_documents(workspace_id) → get doc_id

        2. list_tables(doc_id) → get table_id

        3. list_columns(doc_id, table_id) → explore the structure

    See also:

        - create_table: To create a new table

        - filter_sql_query: To query the data in a table

    Args:

        doc_id: The ID of the document



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - tables (List): List of tables
    """
    logger.info(f"Tool called: list_tables with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "tables": []
            }
        
        tables = await client.list_tables(doc_id)
        
        return {
            "success": True,
            "message": f"Found {len(tables)} tables in document {doc_id}",
            "tables": [table.model_dump() for table in tables]
        }
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return {
            "success": False,
            "message": f"Error listing tables for document {doc_id}: {str(e)}",
            "tables": []
        }


async def list_columns(doc_id: str, table_id: str, ctx=None) -> Dict[str, Any]:
    """
    Lists all columns in a Grist table.

    Prerequisites:

        - list_tables: To obtain a valid table_id



    Typical workflow:

        1. list_tables(doc_id) → get table_id

        2. list_columns(doc_id, table_id) → explore the structure

        3. list_records(doc_id, table_id) → get the data

    See also:

        - create_column: To add a new column

        - modify_column: To modify an existing column

    Args:

        doc_id: The ID of the document

        table_id: The table ID



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - columns (List): List of columns
    """
    logger.info(f"Tool called: list_columns with doc_id: {doc_id}, table_id: {table_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "columns": []
            }
        
        columns = await client.list_columns(doc_id, table_id)
        
        return {
            "success": True,
            "message": f"Found {len(columns)} columns in table {table_id}",
            "columns": [column.model_dump() for column in columns]
        }
    except Exception as e:
        logger.error(f"Error listing columns: {e}")
        return {
            "success": False,
            "message": f"Error listing columns for table {table_id} in document {doc_id}: {str(e)}",
            "columns": []
        }


async def list_records(
    doc_id: str, 
    table_id: str, 
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Lists records in a Grist table with optional sorting and limiting.

    Prerequisites:

        - list_tables: To obtain a valid table_id



    Typical workflow:

        1. list_tables(doc_id) → get table_id

        2. list_columns(doc_id, table_id) → understand the structure

        3. list_records(doc_id, table_id, sort="name", limit=10) → retrieve the data

    See also:

        - filter_sql_query: Alternative with advanced filtering

        - add_grist_records: To add records

    Args:

        doc_id: The ID of the Grist document

        table_id: The table ID

        sort: Sort column (optional, format: "column" or "column:asc/desc")

        limit: Maximum number of records to return (optional)



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - records (List): List of records

        - record_count (int): Total number of records returned
    """
    logger.info(f"Tool called: list_records with doc_id: {doc_id}, table_id: {table_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "records": [],
                "record_count": 0
            }
        
        records = await client.list_records(doc_id, table_id, sort=sort, limit=limit)
        
        limit_info = f" (limited to {limit})" if limit else ""
        sort_info = f" sorted by {sort}" if sort else ""
        
        return {
            "success": True,
            "message": f"Found {len(records)} records in table {table_id}{sort_info}{limit_info}",
            "records": [record.model_dump() for record in records],
            "record_count": len(records)
        }
    except Exception as e:
        logger.error(f"Error listing records: {e}")
        return {
            "success": False,
            "message": f"Error listing records for table {table_id} in document {doc_id}: {str(e)}",
            "records": [],
            "record_count": 0
        }


async def get_table_schema(doc_id: str, table_id: str, ctx=None) -> Dict[str, Any]:
    """
    Gets the detailed schema of a Grist table.

    Prerequisites:

        - list_tables: To obtain a valid table_id



    Typical workflow:

        1. list_tables(doc_id) → get table_id

        2. get_table_schema(doc_id, table_id) → get the detailed structure

    See also:

        - list_columns: For a simpler list of columns

    Args:

        doc_id: The ID of the document

        table_id: The table ID



    Returns:

    Dict with:

        - success (bool): Indicates whether the operation was successful

        - message (str): Success or error message

        - schema (Dict): Detailed schema of the table in frictionless format
    """
    logger.info(f"Tool called: get_table_schema with doc_id: {doc_id}, table_id: {table_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        schema = await client.download_table_schema(doc_id, table_id)
        
        return {
            "success": True,
            "message": f"Retrieved schema for table {table_id}",
            "schema": schema
        }
    except Exception as e:
        logger.error(f"Error getting table schema: {e}")
        return {
            "success": False,
            "message": f"Error getting schema for table {table_id} in document {doc_id}: {str(e)}"
        }
