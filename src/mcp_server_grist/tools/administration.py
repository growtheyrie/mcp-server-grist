"""
Admin tools for the Grist API.

This module contains the MCP tools to manage the administrative aspects
of Grist: creation and modification of objects, access management.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configure the logger
logger = logging.getLogger("grist_mcp_server")


# --- Helper Method for JSON String Encoding ---
def encode_widget_options(columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Encode widgetOptions from dict to JSON string for Grist API.

    Args:
        columns: List of column definitions

    Returns:
        List of column definitions with widgetOptions encoded as JSON strings
    """
    processed_columns = []
    for column in columns:
        processed_col = column.copy()
        if "fields" in processed_col and "widgetOptions" in processed_col["fields"]:
            widget_opts = processed_col["fields"]["widgetOptions"]
            if isinstance(widget_opts, dict):
                processed_col["fields"]["widgetOptions"] = json.dumps(widget_opts)
        processed_columns.append(processed_col)
    return processed_columns


def register_admin_tools(mcp_server):
    """
    Registers all administrative tools in the MCP server.

    Args:
        mcp_server: The instance of the MCP server to save the tools to.
    """
    # Organisation
    mcp_server.tool()(modify_organization)
    mcp_server.tool()(delete_organization)

    # Workspace
    mcp_server.tool()(create_workspace)
    mcp_server.tool()(modify_workspace)
    mcp_server.tool()(delete_workspace)

    # Document
    mcp_server.tool()(create_document)
    mcp_server.tool()(modify_document)
    mcp_server.tool()(delete_document)
    mcp_server.tool()(move_document)
    mcp_server.tool()(force_reload_document)
    mcp_server.tool()(delete_document_history)

    # Table
    mcp_server.tool()(create_table)
    # Note: modify_table removed because Grist API doesn't support table renaming

    # Column
    mcp_server.tool()(create_column)
    mcp_server.tool()(modify_column)
    mcp_server.tool()(delete_column)
    mcp_server.tool()(get_formula_helpers)


# --- Organisation Management ---

async def modify_organization(
    org_id: Union[int, str], 
    name: Optional[str] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies the properties of an organization.

    Prerequisites:
        - list_organizations: To obtain a valid org_id

    Args:
        - org_id: The ID of the organization to modify
        - name: New name for the organization (optional)

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_organization with org_id: {org_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        org_data = {}
        if name is not None:
            org_data["name"] = name

        if not org_data:
            return {
                "success": False,
                "message": "No modification data provided"
            }

        await client.modify_org(org_id, org_data)

        return {
            "success": True,
            "message": f"Organisation {org_id} successfully modified"
        }
    except Exception as e:
        logger.error(f"Error modifying organization: {e}")
        return {
            "success": False,
            "message": f"Error editing organisation: {str(e)}"
        }


async def delete_organization(
    org_id: Union[int, str], 
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes an organization.

    This operation automatically retrieves the organization name before deletion.

    Attention:
        This action is irreversible and will delete all workspaces,
        documents and data associated with this organization.

    Prerequisites:
        - list_organizations: To obtain a valid org_id

    Typical workflow:
        1. list_organizations() → identify the organization
        2. describe_organization(org_id) → review details before deletion
        3. delete_organization(org_id) → delete (irreversible)

    Args:
        - org_id: The ID of the organization to delete

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_organization with org_id: {org_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.delete_org(org_id)

        return {
            "success": True,
            "message": f"Organisation {org_id} successfully deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting organization: {e}")
        return {
            "success": False,
            "message": f"Error deleting organisation: {str(e)}"
        }


# --- Workspace Management ---

async def create_workspace(
    org_id: Union[int, str], 
    name: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a new workspace within an organization.

    Prerequisites:
        - list_organizations: To obtain a valid org_id

    Typical workflow:
        1. list_organizations() → get org_id
        2. create_workspace(org_id, "Name") → create the workspace
        3. list_workspaces(org_id) → verify creation

    Args:
        - org_id: The ID of the organization
        - name: Name of the new workspace

    Returns:
        Dict with status, message, and ID of the created workspace
    """
    logger.info(f"Tool called: create_workspace with org_id: {org_id}, name: {name}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        workspace_data = {"name": name}
        workspace_id = await client.create_workspace(org_id, workspace_data)

        return {
            "success": True,
            "message": f"Workspace '{name}' successfully created",
            "workspace_id": workspace_id
        }
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        return {
            "success": False,
            "message": f"Error creating workspace: {str(e)}"
        }


async def modify_workspace(
    workspace_id: int, 
    name: Optional[str] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies the properties of a workspace.

    Prerequisites:
        - list_workspaces: To obtain a valid workspace_id

    Args:
        - workspace_id: The ID of the workspace to modify
        - name: New name for the workspace (optional)

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_workspace with workspace_id: {workspace_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        workspace_data = {}
        if name is not None:
            workspace_data["name"] = name

        if not workspace_data:
            return {
                "success": False,
                "message": "No modification data provided"
            }

        await client.modify_workspace(workspace_id, workspace_data)

        return {
            "success": True,
            "message": f"Workspace {workspace_id} successfully modified"
        }
    except Exception as e:
        logger.error(f"Error modifying workspace: {e}")
        return {
            "success": False,
            "message": f"Error editing workspace: {str(e)}"
        }


async def delete_workspace(
    workspace_id: int, 
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes a workspace.

    Attention:
        This action is irreversible and will delete all documents
        and data associated with this workspace.

    Args:
        - workspace_id: The ID of the workspace to delete

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_workspace with workspace_id: {workspace_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.delete_workspace(workspace_id)

        return {
            "success": True,
            "message": f"Workspace {workspace_id} successfully deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        return {
            "success": False,
            "message": f"Error deleting workspace: {str(e)}"
        }


# --- Document Management ---

async def create_document(
    workspace_id: int, 
    name: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a new document in a workspace.

    Prerequisites:
        - list_workspaces: To obtain a valid workspace_id

    Typical workflow:
        1. list_workspaces(org_id) → get workspace_id
        2. create_document(workspace_id, "Name") → create the document
        3. list_documents(workspace_id) → verify creation

    Args:
        - workspace_id: The ID of the workspace
        - name: Name of the new document

    Returns:
        Dict with status, message, and ID of the created document.
    """
    logger.info(f"Tool called: create_document with workspace_id: {workspace_id}, name: {name}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        doc_data = {"name": name}
        doc_id = await client.create_doc(workspace_id, doc_data)

        return {
            "success": True,
            "message": f"Document '{name}' successfully created",
            "doc_id": doc_id
        }
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        return {
            "success": False,
            "message": f"Error creating document: {str(e)}"
        }


async def modify_document(
    doc_id: str, 
    name: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies the properties of a document.

    Prerequisites:
        - list_documents: To obtain a valid doc_id

    Args:
        - doc_id: The ID of the document to be modified
        - name: New name for the document (optional)

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_document with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        doc_data = {}
        if name is not None:
            doc_data["name"] = name
        if is_pinned is not None:
            doc_data["isPinned"] = is_pinned

        if not doc_data:
            return {
                "success": False,
                "message": "No modification data provided"
            }

        await client.modify_doc(doc_id, doc_data)

        return {
            "success": True,
            "message": f"Document {doc_id} successfully modified"
        }
    except Exception as e:
        logger.error(f"Error modifying document: {e}")
        return {
            "success": False,
            "message": f"Error editing document: {str(e)}"
        }


async def delete_document(
    doc_id: str, 
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes a document.

    Attention:
        This action is irreversible and will delete all tables
        and data associated with this document.

    Args:
        - doc_id: The ID of the document to delete

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_document with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.delete_doc(doc_id)

        return {
            "success": True,
            "message": f"Document {doc_id} successfully deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return {
            "success": False,
            "message": f"Error deleting document: {str(e)}"
        }


async def move_document(
    doc_id: str, 
    target_workspace_id: int,
    ctx=None
) -> Dict[str, Any]:
    """
    Moves a document to another workspace.

    Prerequisites:
        - list_documents: To obtain a valid doc_id
        - list_workspaces: To obtain a valid destination workspace_id

    Args:
        - doc_id: The ID of the document to move
        - target_workspace_id: The ID of the destination workspace

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: move_document with doc_id: {doc_id}, target_workspace_id: {target_workspace_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.move_doc(doc_id, target_workspace_id)

        return {
            "success": True,
            "message": f"Document {doc_id} successfully moved to workspace {target_workspace_id}"
        }
    except Exception as e:
        logger.error(f"Error moving document: {e}")
        return {
            "success": False,
            "message": f"Error moving document: {str(e)}"
        }


async def force_reload_document(
    doc_id: str, 
    ctx=None
) -> Dict[str, Any]:
    """
    Forces the reloading of a document.

    Useful when the document has been modified outside of the API.
    Or when you want to reset the document state.

    Args:
        - doc_id: The ID of the document to reload

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: force_reload_document with doc_id: {doc_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.force_reload_doc(doc_id)

        return {
            "success": True,
            "message": f"Document {doc_id} successfully reloaded"
        }
    except Exception as e:
        logger.error(f"Error reloading document: {e}")
        return {
            "success": False,
            "message": f"Error reloading document: {str(e)}"
        }


async def delete_document_history(
    doc_id: str, 
    keep: int = 1000,
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes the history of a document.

    Attention:
        This action is irreversible and will delete all versions
        historical records of the document, retaining only the current state.

    Args:
        - doc_id: The ID of the document whose history to delete

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_document_history with doc_id: {doc_id}, keep: {keep}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.delete_doc_history(doc_id, keep)

        return {
            "success": True,
            "message": f"Document {doc_id} history successfully deleted, retaining {keep} recent actions"
        }
    except Exception as e:
        logger.error(f"Error deleting document history: {e}")
        return {
            "success": False,
            "message": f"Error deleting document history: {str(e)}"
        }


# --- Table Management ---

async def create_table(
    doc_id: str, 
    table_name: str,
    columns: List[Dict[str, Any]],
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a new table with basic column structure.

    Attention:
        This tool creates only the table skeleton (column IDs and labels).
        Use modify_column immediately after to add descriptions, types, and other properties.

    Reason for two-step approach:
        The API endpoint for creating tables doesn't support column descriptions or 
        advanced properties. These must be added via modify_column.

    Prerequisites:
        - list_documents: To obtain a valid doc_id

    Typical workflow:
        1. list_documents(workspace_id) → get doc_id
        2. create_table(doc_id, table_name, columns) → create skeleton
        3. modify_column(doc_id, table_id, column_id, ...) → add details for each column
        4. list_columns(doc_id, table_id) → verify complete structure

    Args:
        - doc_id: The ID of the document
        - table_name: Human-readable name (e.g., "Project Tracker", "Team Members")
              Grist auto-converts to table_id: "Project_Tracker", "Team_Members"
        - columns: Minimal column definitions - just id and label.
              Example:
                  [
                      {
                          "id": "Project_Name",        # Words_Separated_By_Underscores
                          "fields": {
                              "label": "Project Name"  # Title Case With Spaces
                          }
                      },
                      {
                          "id": "Priority_Level",
                          "fields": {
                              "label": "Priority Level"
                          }
                      }
                  ]

    Naming Convention:
        - Human-readable (Names/Labels): "Project Name", "Priority Level"
        - System IDs: "Project_Name", "Priority_Level"
        - Tables: table_name → table_id (auto-converted by Grist)
        - Columns: Specify both id and label explicitly in the columns parameter

    Returns:
        Dict with status, message, and details of the created table

    Next steps:
        - Use modify_column to add type, description, widgetOptions, formulas
    """
    logger.info(f"Tool called: create_table with doc_id: {doc_id}, table_name: {table_name}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        table_data = {
            "tables": [
                {
                    "id": table_name,
                    "columns": columns
                }
            ]
        }

        result = await client.create_tables(doc_id, table_data)

        return {
            "success": True,
            "message": f"Table '{table_name}' successfully created",
            "table": result[0] if result else None
        }
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return {
            "success": False,
            "message": f"Error creating table: {str(e)}"
        }


# --- Column Management ---

async def create_column(
    doc_id: str, 
    table_id: str,
    column_id: str,
    label: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a new column with basic structure.

    Attention:
        This tool creates only the column skeleton (ID and label).
        Use modify_column immediately after to add description, type, and other properties.

    Reason for two-step approach:
        Maintains consistency with create_table workflow and ensures all column
        properties (especially descriptions) are added via modify_column.

    Prerequisites:
        - list_tables: To obtain a valid table_id

    Typical workflow:
        1. list_tables(doc_id) → get table_id
        2. create_column(doc_id, table_id, column_id, label) → create skeleton
        3. modify_column(doc_id, table_id, column_id, ...) → add details
        4. list_columns(doc_id, table_id) → verify

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID (e.g., "Projects", "Team_Members")
        - column_id: Column identifier following Grist convention
              (e.g., "Priority_Level", "Start_Date", "Is_Active")
        - label: Column display label in Title Case
              (e.g., "Priority Level", "Start Date", "Is Active")

    Naming Convention:
        - column_id: Words_Separated_By_Underscores (e.g., "Project_Name")
        - label: Title Case With Spaces (e.g., "Project Name")

    Returns:
        Dict with status, message, and details of the created column

    Next steps:
        - Use modify_column to add type, description, widgetOptions, formulas
    """
    logger.info(f"Tool called: create_column with doc_id: {doc_id}, table_id: {table_id}, column_id: {column_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        column_data = {
            "columns": [
                {
                    "id": column_id,
                    "fields":{
                        "label": label
                    }
                }
            ]
        }

        result = await client.create_columns(doc_id, table_id, column_data)

        return {
            "success": True,
            "message": f"Column '{column_id}' successfully created",
            "column": result[0] if result else None
        }
    except Exception as e:
        logger.error(f"Error creating column: {e}")
        return {
            "success": False,
            "message": f"Error creating column: {str(e)}"
        }


async def modify_column(
    doc_id: str, 
    table_id: str,
    column_id: str,
    column_type: Optional[str] = None,
    label: Optional[str] = None,
    formula: Optional[str] = None,
    description: Optional[str] = None,
    widget_options: Optional[Dict[str, Any]] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies column properties - the primary tool for enriching column metadata.

    Typical use case:
        After creating a table with create_table OR creating a column with create_column,
        use this tool to add:
            - Column type (Text, Numeric, Date, Choice, Reference, etc.)
            - Description (crucial for AI and human understanding)
            - Widget options (choices, date formats, reference tables)
            - Formulas for calculated columns

    Prerequisites:
        - list_columns: Use this first ONLY if modifying an existing column
              (to discover the column_id and see current properties)
        - create_table OR create_column: Use one of these first ONLY if adding 
              details to a newly-created column skeleton

    Typical workflow:
        Scenario A - Enriching a newly-created column:
            1. create_table(doc_id, table_id, columns=[...]) OR
               create_column(doc_id, table_id, column_id, label) → create skeleton
            2. modify_column(doc_id, table_id, column_id, ...) → add details
        Scenario B - Modifying an existing column:
            1. list_columns(doc_id, table_id) → get column_id
            2. modify_column(doc_id, table_id, column_id, ...) → modify details

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID (e.g., "Projects", "Team_Members")
        - column_id: Current column ID (e.g., "Priority_Level", "Start_Date")
        - column_type: New data type (optional) - see examples below
        - label: New display label (optional)
        - description: New explanation of column's purpose (optional but recommended)
        - formula: New formula for calculated columns (optional)
        - widget_options: New display/behavior options as dict (optional)

    Column type examples:
        - Text: column_type="Text", description="Full legal name of the organization"
        - Numeric: column_type="Numeric", description="Total number of employees, updated quarterly"
        - Boolean: column_type="Bool", description="Whether this record is currently active"
        - Date: column_type="Date", description="Date when the contract began", 
              widget_options={"dateFormat": "YYYY-MM-DD"}
        - Datetime: column_type="DateTime", description="Timestamp of the most recent update",
              widget_options={"dateFormat": "YYYY-MM-DD", "timeFormat": "HH:mm"}
        - Choice (single): column_type="Choice", description="Urgency level for task processing",
              widget_options={"choices": ["High", "Medium", "Low"]}
        - Choice list (multiple): column_type="ChoiceList", description="Category tags for filtering",
              widget_options={"choices": ["Urgent", "Planning", "Review"]}
        - Reference (link to another table): column_type="Ref:People", description="Team member responsible
              (links to People table)", widget_options={"widget": "Reference"}.
              Note: Format is "Ref:Target_Table_ID".
        - Reference list (multiple links): column_type="RefList:People", description="All people working on this
              project (links to People table)", widget_options={"widget": "Reference"}.
              Note: Format is "RefList:Target_Table_ID".
        - Formula (calculated): column_type="Text", description="Automatically combines first and last name",
              formula="$First_Name + ' ' + $Last_Name". Note: Use $Column_ID format to reference other columns.
        - Attachments: column_type="Attachments", description="Files, images, or documents related to this record"

    Returns:
        Dict with status and message of the operation

    Notes:
        - Column descriptions are crucial for AI assistants to understand and 
              properly use the data in your tables. Always add them when possible.
    """
    logger.info(f"Tool called: modify_column with doc_id: {doc_id}, table_id: {table_id}, column_id: {column_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        column_data = {
            "columns": [
                {
                    "id": column_id,
                    "fields": {} 
                }
            ]
        }

        # Add fields to edit if provided
        if column_type:
            column_data["columns"][0]["fields"]["type"] = column_type
        if label:
            column_data["columns"][0]["fields"]["label"] = label
        if formula is not None:  # Allow to dump the formula with an empty string
            column_data["columns"][0]["fields"]["formula"] = formula
            column_data["columns"][0]["fields"]["isFormula"] = bool(formula)
        if description is not None:
            column_data["columns"][0]["fields"]["description"] = description
        if widget_options:
            column_data["columns"][0]["fields"]["widgetOptions"] = json.dumps(widget_options)

        await client.modify_columns(doc_id, table_id, column_data)

        message = f"Column '{column_id}' successfully modified"

        return {
            "success": True,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error modifying column: {e}")
        return {
            "success": False,
            "message": f"Error editing column: {str(e)}"
        }


async def delete_column(
    doc_id: str, 
    table_id: str,
    column_id: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes a column from a table.

    Attention:
        This action is irreversible and will delete all data.
        associated with this column.

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID
        - column_id: The ID of the column to delete

    Returns:
        Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_column with doc_id: {doc_id}, table_id: {table_id}, column_id: {column_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        await client.delete_column(doc_id, table_id, column_id)

        return {
            "success": True,
            "message": f"Column '{column_id}' successfully deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting column: {e}")
        return {
            "success": False,
            "message": f"Error deleting column: {str(e)}"
        }


async def get_formula_helpers(
    doc_id: str,
    table_id: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Gets formula construction helpers for a Grist table.

    Provides a mapping of column names to their correct formula references,
    helping to build formulas with proper syntax.

    Prerequisites:
        - list_tables: To obtain a valid table_id

    Typical workflow:
        1. list_tables(doc_id) → get table_id
        2. get_formula_helpers(doc_id, table_id) → get formula reference map
        3. Use the references to construct formulas correctly

    Use case:
        - Building formulas that reference other columns
        - Avoiding case sensitivity errors in column references
        - Understanding the correct $ColumnID syntax

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID

    Returns:
        Dict with:
            - success (bool): Indicates whether the operation was successful
            - message (str): Success or error message
            - formula_map (Dict): Mapping with column info and formula references
    """
    logger.info(f"Tool called: get_formula_helpers with doc_id: {doc_id}, table_id: {table_id}")

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured"
            }

        formula_map = await client.get_formula_column_map(doc_id, table_id)

        if "error" in formula_map:
            return {
                "success": False,
                "message": formula_map["error"]
            }

        return {
            "success": True,
            "message": f"Formula helpers retrieved for table {table_id}",
            "formula_map": formula_map
        }
    except Exception as e:
        logger.error(f"Error getting formula helpers: {e}")
        return {
            "success": False,
            "message": f"Error getting formula helpers: {str(e)}"
        }
