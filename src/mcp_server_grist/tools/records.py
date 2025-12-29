"""
Outils de gestion des enregistrements pour l'API Grist.

Ce module contient des outils MCP pour manipuler les enregistrements
dans les tables Grist: ajout, update et deletion.
"""

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configurer le logger
logger = logging.getLogger("grist_mcp_server")


def register_record_tools(mcp_server):
    """
    Enregistre tous les outils de gestion des enregistrements sur le serveur MCP.
    
    Args:
        mcp_server: L'instance du serveur MCP sur laquelle enregistrer les outils.
    """
    # Enregistrement des outils sur le serveur MCP
    mcp_server.tool()(add_grist_records)
    mcp_server.tool()(add_grist_records_safe)
    mcp_server.tool()(update_grist_records)
    mcp_server.tool()(delete_grist_records)


# --- Helper Method for DateTime Conversion ---
def parse_datetime_to_unix(datetime_str: str) -> int:
    """
    Convert datetime string to Unix timestamp.

    Supports two formats:
    - DateTime: "2025-12-28 07:52 UTC +8"
    - Date: "2025-12-28 UTC +8"

    Args:
        datetime_str: DateTime with UTC offset

    Returns:
        Unix timestamp (int)

    Raises:
        ValueError: If format is invalid
    """
    datetime_str = datetime_str.strip()

    # Try DateTime format first: "YYYY-MM-DD HH:MM UTC +offset"
    pattern_datetime = r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC ([+-]\d+)'
    match = re.match(pattern_datetime, datetime_str)

    if match:
        date_part, time_part, offset_hours = match.groups()
        dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
    else:
        # Try Date format: "YYYY-MM-DD UTC +offset"
        pattern_date = r'(\d{4}-\d{2}-\d{2}) UTC ([+-]\d+)'
        match = re.match(pattern_date, datetime_str)

        if not match:
            raise ValueError(
                f"Invalid datetime format. Expected: 'YYYY-MM-DD HH:MM UTC +8' or 'YYYY-MM-DD UTC +8', "
                f"got: '{datetime_str}'"
            )

        date_part, offset_hours = match.groups()
        dt = datetime.strptime(f"{date_part} 00:00", "%Y-%m-%d %H:%M")

    # Create timezone with offset
    offset = timedelta(hours=int(offset_hours))
    tz = timezone(offset)
    dt_aware = dt.replace(tzinfo=tz)

    return int(dt_aware.timestamp())


def preprocess_datetime_values(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert datetime strings to GristObjCode format.

    Detects and converts:
    - "YYYY-MM-DD HH:MM UTC +offset" → ["D", timestamp, "UTC"]
    - "YYYY-MM-DD UTC +offset" → ["d", timestamp]

    Leaves other values unchanged.
    """
    import re

    # Patterns for detection
    datetime_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC [+-]\d+$'
    date_pattern = r'^\d{4}-\d{2}-\d{2} UTC [+-]\d+$'

    processed = []
    for record in records:
        new_record = {}
        for key, value in record.items():
            if isinstance(value, str):
                if re.match(datetime_pattern, value):
                    # DateTime with time component
                    timestamp = parse_datetime_to_unix(value)
                    new_record[key] = ["D", timestamp, "UTC"]
                elif re.match(date_pattern, value):
                    # Date without time component
                    timestamp = parse_datetime_to_unix(value)
                    new_record[key] = ["d", timestamp]
                else:
                    # Regular string, leave it alone
                    new_record[key] = value
            else:
                # Not a string, leave it alone
                new_record[key] = value
        processed.append(new_record)
    return processed


async def add_grist_records(doc_id: str,
                            table_id: str,
                            records: List[Dict[str, Any]],
                            ctx=None) -> Dict[str, Any]:
    """
    Adds records to a Grist table.
	
    DATETIME/DATE VALUES (Automatic Conversion)
    ============================================

    Use simple string formats - automatic conversion to GristObjCode:

    DateTime (with time):  "2025-12-28 14:30 UTC +8"  → ["D", timestamp, "UTC"]
    Date (date only):      "2025-12-28 UTC +8"        → ["d", timestamp]

    Example:
    {"DueDate": "2025-12-30 UTC +8", "CreatedAt": "2025-12-28 14:30 UTC +8"}

    COMPLEX COLUMN TYPES (Manual GristObjCode)
    ===========================================

    Other complex types require manual encoding:

    Choice List:        ["L", "item1", "item2", ...]
                        Example: {"Tags": ["L", "Urgent", "Planning"]}

    Reference:          ["R", "table_id", row_id]
                        Example: {"Lead": ["R", "People", 17]}

    Reference List:     ["r", "table_id", [row_id1, row_id2]]
                        Example: {"Team": ["r", "People", [15, 16]]}

    REGULAR COLUMN TYPES
    ====================

    Use plain values (no encoding needed):

    Text:               "Hello World"
    Numeric:            42 or 3.14
    Choice (single):    "High"
    Boolean:            true or false

    COMPLETE EXAMPLE
    ================

    records = [{
        "Name": "Q1 Planning",                      # Text
        "Priority": "High",                         # Choice (single)
        "Tags": ["L", "Urgent", "Planning"],        # Choice List
        "Lead": ["R", "People", 17],                # Reference
        "Team": ["r", "People", [8, 9, 10]],        # Reference List
        "StartDate": "2025-01-15 UTC +8",           # Date (auto-converted)
        "CreatedAt": "2025-12-28 14:30 UTC +8",     # DateTime (auto-converted)
        "Budget": 50000,                            # Numeric
        "Active": true                              # Boolean
    }]

    Args:

        doc_id: The ID of the Grist document

        table_id: The table ID

        records: List of records to add. Each record is a dictionary

        where the keys are the column names and the values ​​are the data.

        Example: [{"name": "Dupont", "first name": "Jean", "age": 35}]



    Returns:

    Dict with status, message and IDs of created records:

    {

    "success": True/False,

    "message": "Success or error message",

    "record_ids": [1, 2, 3] # IDs of the created records

    }
    """
    logger.info(
        f"Tool called: add_grist_records for doc_id: {doc_id}, table_id: {table_id}"
    )

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "record_ids": []
            }

       # Preprocess datetime strings
        records = preprocess_datetime_values(records)

        record_ids = await client.add_records(doc_id, table_id, records)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} enregistrements ajoutés avec succès",
            "record_ids": record_ids
        }
    except Exception as e:
        logger.error(f"Error in add_grist_records: {str(e)}")
        return {
            "success": False,
            "message": f"Erreur lors de l'ajout des enregistrements: {str(e)}",
            "record_ids": []
        }


async def add_grist_records_safe(doc_id: str,
                                 table_id: str,
                                 records: List[Dict[str, Any]],
                                 ctx=None) -> Dict[str, Any]:
    """
    Adds records with prior validation of the structure.

    This secure version validates the existence of the table and columns

    before adding the records, and suggests corrections if necessary.

    DATETIME CONVERSION (Automatic)
    --------------------------------

    Datetime strings are automatically converted to GristObjCode:
    - DateTime: "YYYY-MM-DD HH:MM UTC +offset" → ["D", timestamp, "UTC"]
    - Date: "YYYY-MM-DD UTC +offset" → ["d", timestamp]

    For other GristObjCode types (Choice List, Reference, Reference List),
    see add_grist_records() docstring for complete documentation.

    Prerequisites:

        - list_tables, list_columns: performed automatically internally

    Typical workflow:

        1. get_table_schema(doc_id, table_id) → understand the types

        2. add_grist_records_safe(doc_id, table_id, records) → validated insertion

        3. list_records(doc_id, table_id, limit=5) → check the result

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        Records: List of records to add



    Returns:

    Dict with status, message, and possibly correction suggestions

    and IDs of the records created if the operation was successful
    """
    logger.info(
        f"Tool called: add_grist_records_safe for doc_id: {doc_id}, table_id: {table_id}"
    )

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "record_ids": []
            }

        # Validation 1: Vérifier si la table existe
        table_validation = await client.validate_table_exists(doc_id, table_id)
        if not table_validation.get("exists", False):
            return {
                "success":
                False,
                "message":
                table_validation.get("error", f"Table '{table_id}' not found"),
                "available_tables":
                table_validation.get("available_tables", []),
                "suggestion":
                table_validation.get("suggestion"),
                "record_ids": []
            }

        # Validation 2: Vérifier les names de colonnes si des enregistrements sont fournis
        if records and isinstance(records, list) and len(records) > 0:
            # Extraire tous les names de colonnes utilisés
            column_names = set()
            for record in records:
                column_names.update(record.keys())

            # Valider l'existence des colonnes
            columns_validation = await client.validate_columns_exist(
                doc_id, table_id, list(column_names))
            if not columns_validation.get(
                    "valid", True) and "error" not in columns_validation:
                return {
                    "success":
                    False,
                    "message":
                    f"Some columns do not exist in table '{table_id}'",
                    "missing_columns":
                    columns_validation.get("missing_columns", []),
                    "suggestions":
                    columns_validation.get("suggestions", {}),
                    "available_columns":
                    columns_validation.get("available_columns", []),
                    "record_ids": []
                }

        # Preprocess datetime strings
        records = preprocess_datetime_values(records)

        # Si tout est valide, ajouter les enregistrements
        record_ids = await client.add_records(doc_id, table_id, records)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} enregistrements ajoutés avec succès après validation",
            "record_ids": record_ids
        }
    except Exception as e:
        logger.error(f"Error in add_grist_records_safe: {str(e)}")
        return {
            "success": False,
            "message":
            f"Erreur lors de l'ajout sécurisé des enregistrements: {str(e)}",
            "record_ids": []
        }


async def update_grist_records(doc_id: str,
                               table_id: str,
                               records: List[Dict[str, Any]],
                               ctx=None) -> Dict[str, Any]:
    """
    Updates existing records in a Grist table.

    DATETIME CONVERSION (Automatic)
    --------------------------------

    Datetime strings are automatically converted to GristObjCode:
    - DateTime: "YYYY-MM-DD HH:MM UTC +offset" → ["D", timestamp, "UTC"]
    - Date: "YYYY-MM-DD UTC +offset" → ["d", timestamp]

    For other GristObjCode types (Choice List, Reference, Reference List),
    see add_grist_records() docstring for complete documentation.

    Prerequisites:

        - list_records: To obtain the IDs of the records to update

    Typical workflow:

        1. list_records(doc_id, table_id) → get the IDs

        2. update_grist_records(doc_id, table_id, records_with_id) → update

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        records: List of records to be updated.

    Each record must contain an 'id' field

        Example: [{"id": 1, "name": "Smith", "first_name": "John"}]



    Returns:

    Dict with updated status, message, and record IDs
    """
    logger.info(
        f"Tool called: update_grist_records for doc_id: {doc_id}, table_id: {table_id}"
    )

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Client Grist non configuré",
                "record_ids": []
            }

        # Vérifier que tous les enregistrements ont un ID
        for i, record in enumerate(records):
            if "id" not in record:
                return {
                    "success": False,
                    "message":
                    f"L'enregistrement à l'index {i} n'a pas d'ID. Chaque enregistrement doit contenir un champ 'id'.",
                    "record_ids": []
                }

        # Preprocess datetime strings
        records = preprocess_datetime_values(records)

        record_ids = await client.update_records(doc_id, table_id, records)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} enregistrements mis à jour avec succès",
            "record_ids": record_ids
        }
    except Exception as e:
        logger.error(f"Error in update_grist_records: {str(e)}")
        return {
            "success": False,
            "message":
            f"Erreur lors de la update des enregistrements: {str(e)}",
            "record_ids": []
        }


async def delete_grist_records(doc_id: str,
                               table_id: str,
                               record_ids: List[int],
                               ctx=None) -> Dict[str, Any]:
    """
    Deletes records from a Grist table.

    Prerequisites:

        - list_records: To get the IDs of the records to delete

    Typical workflow:

        1. list_records(doc_id, table_id) → get the IDs

        2. delete_grist_records(doc_id, table_id, record_ids) → deletion

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        record_ids: List of IDs of records to delete



    Returns:

    Dict with status and confirmation message
    """
    logger.info(
        f"Tool called: delete_grist_records for doc_id: {doc_id}, table_id: {table_id}"
    )

    try:
        client = get_client(ctx)
        if not client:
            return {"success": False, "message": "Client Grist non configuré"}

        # Vérifier que tous les IDs sont des entiers
        for i, record_id in enumerate(record_ids):
            if not isinstance(record_id, int):
                return {
                    "success":
                    False,
                    "message":
                    f"L'ID à l'index {i} ({record_id}) n'est pas un entier. Tous les IDs doivent être des entiers."
                }

        await client.delete_records(doc_id, table_id, record_ids)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} enregistrements supprimés avec succès"
        }
    except Exception as e:
        logger.error(f"Error in delete_grist_records: {str(e)}")
        return {
            "success": False,
            "message":
            f"Erreur lors de la deletion des enregistrements: {str(e)}"
        }
