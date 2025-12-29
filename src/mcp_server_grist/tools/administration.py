"""
Outils d'administration pour l'API Grist.

Ce module contient des outils MCP pour gérer les aspects administratifs
de Grist: création et modification d'objets, gestion des accès.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configurer le logger
logger = logging.getLogger("grist_mcp_server")


def register_admin_tools(mcp_server):
    """
    Enregistre tous les outils d'administration sur le serveur MCP.
    
    Args:
        mcp_server: L'instance du serveur MCP sur laquelle enregistrer les outils.
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
    mcp_server.tool()(modify_table)
    
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

        org_id: The ID of the organization to modify

        name: New name for the organization (optional)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_organization with org_id: {org_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        org_data = {}
        if name is not None:
            org_data["name"] = name
        
        if not org_data:
            return {
                "success": False,
                "message": "Aucune donnée de modification fournie"
            }
        
        await client.modify_org(org_id, org_data)
        
        return {
            "success": True,
            "message": f"Organisation {org_id} modifiée avec succès"
        }
    except Exception as e:
        logger.error(f"Error modifying organization: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification de l'organisation: {str(e)}"
        }


async def delete_organization(
    org_id: Union[int, str], 
    ctx=None
) -> Dict[str, Any]:
    """
    Deletes an organization.

    This operation automatically retrieves the organization name before deletion.

    Attention:

    This action is irreversible and will delete all workspaces.

    documents and data associated with this organization.

    Prerequisites:

        - list_organizations: To obtain a valid org_id

    Typical workflow:

        1. list_organizations() → identify the organization

        2. describe_organization(org_id) → review details before deletion

        3. delete_organization(org_id) → delete (irreversible)

    Args:

        org_id: The ID of the organization to delete



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_organization with org_id: {org_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.delete_org(org_id)
        
        return {
            "success": True,
            "message": f"Organisation {org_id} supprimée avec succès"
        }
    except Exception as e:
        logger.error(f"Error deleting organization: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la deletion de l'organisation: {str(e)}"
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

        org_id: The ID of the organization

        name: Name of the new workspace



    Returns:

    Dict with status, message, and ID of the created workspace
    """
    logger.info(f"Tool called: create_workspace with org_id: {org_id}, name: {name}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        workspace_data = {"name": name}
        workspace_id = await client.create_workspace(org_id, workspace_data)
        
        return {
            "success": True,
            "message": f"Espace de travail '{name}' créé avec succès",
            "workspace_id": workspace_id
        }
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la création de l'espace de travail: {str(e)}"
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

        workspace_id: The ID of the workspace to modify

        name: New name for the workspace (optional)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_workspace with workspace_id: {workspace_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        workspace_data = {}
        if name is not None:
            workspace_data["name"] = name
        
        if not workspace_data:
            return {
                "success": False,
                "message": "Aucune donnée de modification fournie"
            }
        
        await client.modify_workspace(workspace_id, workspace_data)
        
        return {
            "success": True,
            "message": f"Espace de travail {workspace_id} modifié avec succès"
        }
    except Exception as e:
        logger.error(f"Error modifying workspace: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification de l'espace de travail: {str(e)}"
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

        workspace_id: The ID of the workspace to delete



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_workspace with workspace_id: {workspace_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.delete_workspace(workspace_id)
        
        return {
            "success": True,
            "message": f"Espace de travail {workspace_id} supprimé avec succès"
        }
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la deletion de l'espace de travail: {str(e)}"
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

        workspace_id: The ID of the workspace

        name: Name of the new document



    Returns:

    Dict with status, message, and ID of the created document.
    """
    logger.info(f"Tool called: create_document with workspace_id: {workspace_id}, name: {name}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        doc_data = {"name": name}
        doc_id = await client.create_doc(workspace_id, doc_data)
        
        return {
            "success": True,
            "message": f"Document '{name}' créé avec succès",
            "doc_id": doc_id
        }
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la création du document: {str(e)}"
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

        doc_id: The ID of the document to be modified

        name: New name for the document (optional)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_document with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        doc_data = {}
        if name is not None:
            doc_data["name"] = name
        if is_pinned is not None:
            doc_data["isPinned"] = is_pinned
        
        if not doc_data:
            return {
                "success": False,
                "message": "Aucune donnée de modification fournie"
            }
        
        await client.modify_doc(doc_id, doc_data)
        
        return {
            "success": True,
            "message": f"Document {doc_id} modifié avec succès"
        }
    except Exception as e:
        logger.error(f"Error modifying document: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification du document: {str(e)}"
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

        doc_id: The ID of the document to delete



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_document with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.delete_doc(doc_id)
        
        return {
            "success": True,
            "message": f"Document {doc_id} supprimé avec succès"
        }
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la deletion du document: {str(e)}"
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

        doc_id: The ID of the document to move

        target_workspace_id: The ID of the destination workspace



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: move_document with doc_id: {doc_id}, target_workspace_id: {target_workspace_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.move_doc(doc_id, target_workspace_id)
        
        return {
            "success": True,
            "message": f"Document {doc_id} déplacé vers l'espace de travail {target_workspace_id} avec succès"
        }
    except Exception as e:
        logger.error(f"Error moving document: {e}")
        return {
            "success": False,
            "message": f"Erreur lors du déplacement du document: {str(e)}"
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

        doc_id: The ID of the document to reload



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: force_reload_document with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.force_reload_doc(doc_id)
        
        return {
            "success": True,
            "message": f"Document {doc_id} rechargé avec succès"
        }
    except Exception as e:
        logger.error(f"Error reloading document: {e}")
        return {
            "success": False,
            "message": f"Erreur lors du rechargement du document: {str(e)}"
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

        doc_id: The ID of the document whose history to delete



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_document_history with doc_id: {doc_id}, keep: {keep}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.delete_doc_history(doc_id, keep)
        
        return {
            "success": True,
            "message": f"Historique du document {doc_id} supprimé avec succès, conservant {keep} actions récentes"
        }
    except Exception as e:
        logger.error(f"Error deleting document history: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la deletion de l'historique du document: {str(e)}"
        }


# --- Table Management ---

async def create_table(
    doc_id: str, 
    table_id: str,
    columns: List[Dict[str, Any]],
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a new table in a document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id

    Typical workflow:

        1. list_documents(workspace_id) → get doc_id

        2. create_table(doc_id, "TableName") → create the table

        3. list_tables(doc_id) → verify creation

    Args:

        doc_id: The ID of the document

        table_id: ID of the new table (must be unique within the document)

        columns: List of columns to create



    Returns:

    Dict with status, message, and details of the created table
    """
    logger.info(f"Tool called: create_table with doc_id: {doc_id}, table_id: {table_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        table_data = {
            "tables": [
                {
                    "id": table_id,
                    "columns": columns
                }
            ]
        }
        
        result = await client.create_tables(doc_id, table_data)
        
        return {
            "success": True,
            "message": f"Table '{table_id}' créée avec succès",
            "table": result[0] if result else None
        }
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la création de la table: {str(e)}"
        }


async def modify_table(
    doc_id: str, 
    table_id: str,
    new_table_id: Optional[str] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies the properties of a table.

    Prerequisites:

        - list_tables: To obtain a valid table_id

    Args:

        doc_id: The ID of the document

        table_id: The current ID of the table

        new_table_id: New ID for the table (optional)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_table with doc_id: {doc_id}, table_id: {table_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        table_data = {
            "tables": [
                {
                    "tableId": table_id
                }
            ]
        }
        
        if new_table_id:
            table_data["tables"][0]["newTableId"] = new_table_id
        
        await client.modify_tables(doc_id, table_data)
        
        message = f"Table {table_id} modifiée avec succès"
        if new_table_id:
            message += f" (renamemée en '{new_table_id}')"
        
        return {
            "success": True,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error modifying table: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification de la table: {str(e)}"
        }


# --- Column Management ---

async def create_column(
    doc_id: str, 
    table_id: str,
    column_id: str,
    column_type: str = "Text",
    label: Optional[str] = None,
    formula: Optional[str] = None,
    widget_options: Optional[Dict[str, Any]] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Creates a new column in a table.

    Prerequisites:

        - list_tables: To obtain a valid table_id

    Typical workflow:

        1. list_tables(doc_id) → get table_id

        2. create_column(doc_id, table_id, "col_name", "Text", "Name") → create the column

        3. list_columns(doc_id, table_id) → verify creation

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        column_id: ID of the new column (must be unique within the table)

        column_type: Data type (Text, Numeric, Boolean, Date, etc.)

        label: Column display label (optional)

        formula: Formula for calculated columns (optional)

        widget_options: Display options (optional)



    Returns:

    Dict with status, message, and details of the created column
    """
    logger.info(f"Tool called: create_column with doc_id: {doc_id}, table_id: {table_id}, column_id: {column_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        column_data = {
            "columns": [
                {
                    "id": column_id,
                    "fields":{
                        "type": column_type
                    }
                }
            ]
        }
        
        # Ajouter les champs optionnels s'ils sont fournis
        if label:
            column_data["columns"][0]["fields"]["label"] = label
        if formula:
            column_data["columns"][0]["fields"]["formula"] = formula
            column_data["columns"][0]["fields"]["isFormula"] = True
        if widget_options:
            column_data["columns"][0]["fields"]["widgetOptions"] = widget_options
        
        result = await client.create_columns(doc_id, table_id, column_data)
        
        return {
            "success": True,
            "message": f"Colonne '{column_id}' créée avec succès",
            "column": result[0] if result else None
        }
    except Exception as e:
        logger.error(f"Error creating column: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la création de la colonne: {str(e)}"
        }


async def modify_column(
    doc_id: str, 
    table_id: str,
    column_id: str,
    new_column_id: Optional[str] = None,
    column_type: Optional[str] = None,
    label: Optional[str] = None,
    formula: Optional[str] = None,
    widget_options: Optional[Dict[str, Any]] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies the properties of a column.

    Prerequisites:

        - list_columns: To obtain a valid column_id

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        column_id: The current ID of the column

        new_column_id: New ID for the column (optional)

        column_type: New data type (optional)

        label: New display label (optional)

        formula: New formula (optional)

        widget_options: New display options (optional)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_column with doc_id: {doc_id}, table_id: {table_id}, column_id: {column_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        column_data = {
            "columns": [
                {
                    "id": column_id,
                    "fields": {} 
                }
            ]
        }
        
        # Ajouter les champs à modifier s'ils sont fournis
        if new_column_id:
            column_data["columns"][0]["newId"] = new_column_id
        if column_type:
            column_data["columns"][0]["fields"]["type"] = column_type
        if label:
            column_data["columns"][0]["fields"]["label"] = label
        if formula is not None:  # Permettre de vider la formule avec une chaîne vide
            column_data["columns"][0]["fields"]["formula"] = formula
            column_data["columns"][0]["fields"]["isFormula"] = bool(formula)
        if widget_options:
            column_data["columns"][0]["fields"]["widgetOptions"] = widget_options
        
        await client.modify_columns(doc_id, table_id, column_data)
        
        message = f"Colonne '{column_id}' modifiée avec succès"
        if new_column_id:
            message += f" (renamemée en '{new_column_id}')"
        
        return {
            "success": True,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error modifying column: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification de la colonne: {str(e)}"
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

        doc_id: The ID of the document

        table_id: The table ID

        column_id: The ID of the column to delete



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: delete_column with doc_id: {doc_id}, table_id: {table_id}, column_id: {column_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        await client.delete_column(doc_id, table_id, column_id)
        
        return {
            "success": True,
            "message": f"Colonne '{column_id}' supprimée avec succès"
        }
    except Exception as e:
        logger.error(f"Error deleting column: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la deletion de la colonne: {str(e)}"
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
        doc_id: The ID of the document
        table_id: The table ID
    
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
                "message": "Client Grist non configuré"
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
            "message": f"Erreur lors de la récupération des helpers de formule: {str(e)}"
        }
