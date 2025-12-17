"""
Outils de gestion des accès pour l'API Grist.

Ce module contient des outils MCP pour gérer les droits d'accès
aux organisations, espaces de travail et documents Grist.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configurer le logger
logger = logging.getLogger("grist_mcp_server")


def register_access_tools(mcp_server):
    """
    Enregistre tous les outils de gestion des accès sur le serveur MCP.
    
    Args:
        mcp_server: L'instance du serveur MCP sur laquelle enregistrer les outils.
    """
    # Organisation
    mcp_server.tool()(list_organization_access)
    mcp_server.tool()(modify_organization_access)
    
    # Workspace
    mcp_server.tool()(list_workspace_access)
    mcp_server.tool()(modify_workspace_access)
    
    # Document
    mcp_server.tool()(list_document_access)
    mcp_server.tool()(modify_document_access)


# --- Organisation Access ---

async def list_organization_access(
    org_id: Union[int, str], 
    ctx=None
) -> Dict[str, Any]:
    """
    Lists users who have access to an organization.

    Prerequisites:

        - list_organizations: To obtain a valid org_id

    Args:

        org_id: The ID of the organization



    Returns:

    Dict with status, message and access details
    """
    logger.info(f"Tool called: list_organization_access with org_id: {org_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        access_info = await client.list_org_access(org_id)
        
        return {
            "success": True,
            "message": f"Accès à l'organisation {org_id} récupérés avec succès",
            "access": access_info
        }
    except Exception as e:
        logger.error(f"Error listing organization access: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération des accès à l'organisation: {str(e)}"
        }


async def modify_organization_access(
    org_id: Union[int, str], 
    user_email: str,
    access_level: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies a user's access to an organization.

    Prerequisites:

        - list_organizations: To obtain a valid org_id

        - list_organization_access: To see current access

    Args:

        org_id: The ID of the organization

        user_email: User's email

        access_level: Access level (owners, editors, viewers, members, or null to remove)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_organization_access with org_id: {org_id}, user_email: {user_email}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        if access_level not in ["owners", "editors", "viewers", "members", "null"]:
            return {
                "success": False,
                "message": "Niveau d'accès invalide. Doit être: owners, editors, viewers, members, ou null"
            }
        
        access_delta = {
            "users": {
                user_email: None if access_level == "null" else access_level
            }
        }
        
        await client.modify_org_access(org_id, access_delta)
        
        action = "supprimé" if access_level == "null" else f"défini à {access_level}"
        return {
            "success": True,
            "message": f"Accès pour {user_email} {action} avec succès"
        }
    except Exception as e:
        logger.error(f"Error modifying organization access: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification des accès à l'organisation: {str(e)}"
        }


# --- Workspace Access ---

async def list_workspace_access(
    workspace_id: int, 
    ctx=None
) -> Dict[str, Any]:
    """
    Lists users who have access to a workspace.

    Prerequisites:

        - list_workspaces: To obtain a valid workspace_id

    Args:

        workspace_id: The ID of the workspace



    Returns:

    Dict with status, message and access details
    """
    logger.info(f"Tool called: list_workspace_access with workspace_id: {workspace_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        access_info = await client.list_workspace_access(workspace_id)
        
        return {
            "success": True,
            "message": f"Accès à l'espace de travail {workspace_id} récupérés avec succès",
            "access": access_info
        }
    except Exception as e:
        logger.error(f"Error listing workspace access: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération des accès à l'espace de travail: {str(e)}"
        }


async def modify_workspace_access(
    workspace_id: int, 
    user_email: str,
    access_level: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies a user's access to a workspace.

    Prerequisites:

        - list_workspaces: To obtain a valid workspace_id

        - list_workspace_access: To see current access

    Args:

        workspace_id: The ID of the workspace

        user_email: User's email

        access_level: Access level (owners, editors, viewers, or null to remove)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_workspace_access with workspace_id: {workspace_id}, user_email: {user_email}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        if access_level not in ["owners", "editors", "viewers", "null"]:
            return {
                "success": False,
                "message": "Niveau d'accès invalide. Doit être: owners, editors, viewers, ou null"
            }
        
        access_delta = {
            "users": {
                user_email: None if access_level == "null" else access_level
            }
        }
        
        await client.modify_workspace_access(workspace_id, access_delta)
        
        action = "supprimé" if access_level == "null" else f"défini à {access_level}"
        return {
            "success": True,
            "message": f"Accès pour {user_email} {action} avec succès"
        }
    except Exception as e:
        logger.error(f"Error modifying workspace access: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification des accès à l'espace de travail: {str(e)}"
        }


# --- Document Access ---

async def list_document_access(
    doc_id: str, 
    ctx=None
) -> Dict[str, Any]:
    """
    Lists the users who have access to a document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id

    Args:

        doc_id: The ID of the document



    Returns:

    Dict with status, message and access details
    """
    logger.info(f"Tool called: list_document_access with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        access_info = await client.list_doc_access(doc_id)
        
        return {
            "success": True,
            "message": f"Accès au document {doc_id} récupérés avec succès",
            "access": access_info
        }
    except Exception as e:
        logger.error(f"Error listing document access: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération des accès au document: {str(e)}"
        }


async def modify_document_access(
    doc_id: str, 
    user_email: str,
    access_level: str,
    ctx=None
) -> Dict[str, Any]:
    """
    Modifies a user's access to a document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id

        - list_document_access: To see current access

    Args:

        doc_id: The ID of the document

        user_email: User's email

        access_level: Access level (owners, editors, viewers, or null to remove)



    Returns:

    Dict with status and message of the operation
    """
    logger.info(f"Tool called: modify_document_access with doc_id: {doc_id}, user_email: {user_email}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        if access_level not in ["owners", "editors", "viewers", "null"]:
            return {
                "success": False,
                "message": "Niveau d'accès invalide. Doit être: owners, editors, viewers, ou null"
            }
        
        access_delta = {
            "users": {
                user_email: None if access_level == "null" else access_level
            }
        }
        
        await client.modify_doc_access(doc_id, access_delta)
        
        action = "supprimé" if access_level == "null" else f"défini à {access_level}"
        return {
            "success": True,
            "message": f"Accès pour {user_email} {action} avec succès"
        }
    except Exception as e:
        logger.error(f"Error modifying document access: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la modification des accès au document: {str(e)}"
        }
