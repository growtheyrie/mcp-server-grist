"""
Outils de gestion des pièces jointes pour l'API Grist.

Ce module contient des outils MCP pour gérer les pièces jointes
dans les documents Grist: liste, téléchargement, téléversement.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configurer le logger
logger = logging.getLogger("grist_mcp_server")


def register_attachment_tools(mcp_server):
    """
    Enregistre tous les outils de gestion des pièces jointes sur le serveur MCP.
    
    Args:
        mcp_server: L'instance du serveur MCP sur laquelle enregistrer les outils.
    """
    mcp_server.tool()(list_attachments)
    mcp_server.tool()(get_attachment_info)
    mcp_server.tool()(download_attachment)
    mcp_server.tool()(upload_attachment)


async def list_attachments(
    doc_id: str,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Lists the attachments of a Grist document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id

    Args:

        doc_id: The ID of the document

        Sort: Sort column (optional)

        limit: Maximum number of results (optional)



    Returns:

    Dict with status, message, and list of attachments
    """
    logger.info(f"Tool called: list_attachments with doc_id: {doc_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "attachments": []
            }
        
        attachments = await client.list_attachments(doc_id, sort=sort, limit=limit)
        
        return {
            "success": True,
            "message": f"{len(attachments)} pièces jointes trouvées dans le document {doc_id}",
            "attachments": attachments
        }
    except Exception as e:
        logger.error(f"Error listing attachments: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération des pièces jointes pour le document {doc_id}: {str(e)}",
            "attachments": []
        }


async def get_attachment_info(
    doc_id: str,
    attachment_id: int,
    ctx=None
) -> Dict[str, Any]:
    """
    Retrieves the metadata of an attachment.

    Prerequisites:

        - list_attachments: To obtain a valid attachment_id

    Args:

        doc_id: The ID of the document

        attachment_id: The ID of the attachment



    Returns:

    Dict with status, message, and attachment metadata
    """
    logger.info(f"Tool called: get_attachment_info with doc_id: {doc_id}, attachment_id: {attachment_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        attachment_info = await client.get_attachment_metadata(doc_id, attachment_id)
        
        return {
            "success": True,
            "message": f"Métadonnées de la pièce jointe {attachment_id} récupérées avec succès",
            "attachment": attachment_info
        }
    except Exception as e:
        logger.error(f"Error getting attachment info: {e}")
        return {
            "success": False,
            "message": f"Erreur lors de la récupération des métadonnées de la pièce jointe: {str(e)}"
        }


async def download_attachment(
    doc_id: str,
    attachment_id: int,
    ctx=None
) -> Dict[str, Any]:
    """
    Downloads the contents of an attachment.

    Prerequisites:

        - list_attachments: To obtain a valid attachment_id

        - get_attachment_info: To obtain the metadata (type, name)

    Args:

        doc_id: The ID of the document

        attachment_id: The ID of the attachment



    Returns:

    Dict with status, message and content encoded in base64
    """
    logger.info(f"Tool called: download_attachment with doc_id: {doc_id}, attachment_id: {attachment_id}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        # Récupérer d'abord les métadonnées pour avoir le nom et le type
        metadata = await client.get_attachment_metadata(doc_id, attachment_id)
        
        # Télécharger le contenu
        content = await client.download_attachment(doc_id, attachment_id)
        
        # Encoder le contenu binaire en base64
        import base64
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        filename = metadata.get("fileName", f"attachment_{attachment_id}")
        content_type = metadata.get("fileType", "application/octet-stream")
        
        return {
            "success": True,
            "message": f"Pièce jointe {attachment_id} téléchargée avec succès",
            "filename": filename,
            "content_type": content_type,
            "content_base64": encoded_content,
            "size_bytes": len(content)
        }
    except Exception as e:
        logger.error(f"Error downloading attachment: {e}")
        return {
            "success": False,
            "message": f"Erreur lors du téléchargement de la pièce jointe: {str(e)}"
        }


async def upload_attachment(
    doc_id: str,
    filename: str,
    content_base64: str,
    content_type: str = "application/octet-stream",
    ctx=None
) -> Dict[str, Any]:
    """
    Uploads an attachment to a Grist document.

    Prerequisites:

        - list_documents: To obtain a valid doc_id

    Args:

        doc_id: The ID of the document

        filename: File name

        content_base64: Content of the base64-encoded file

        content_type: MIME type of the file



    Returns:

    Dict with status, message, and ID of the created attachment
    """
    logger.info(f"Tool called: upload_attachment with doc_id: {doc_id}, filename: {filename}")
    
    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré"
            }
        
        # Décoder le contenu base64
        import base64
        content = base64.b64decode(content_base64)
        
        # Préparer les données pour le téléversement
        files = [(filename, content, content_type)]
        
        # Téléverser la pièce jointe
        result = await client.upload_attachments(doc_id, files)
        
        attachment_ids = [attachment.get("id") for attachment in result]
        
        return {
            "success": True,
            "message": f"Pièce jointe '{filename}' téléversée avec succès",
            "attachment_ids": attachment_ids
        }
    except Exception as e:
        logger.error(f"Error uploading attachment: {e}")
        return {
            "success": False,
            "message": f"Erreur lors du téléversement de la pièce jointe: {str(e)}"
        }
