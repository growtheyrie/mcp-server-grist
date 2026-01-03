"""
Outils de gestion des enregistrements pour l'API Grist.

Ce module contient des outils MCP pour manipuler les enregistrements
dans les tables Grist: ajout, update et deletion.
"""

import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

from ..client import get_client

# Configurer le logger
logger = logging.getLogger("grist_mcp_server")

# Load environment variables
load_dotenv()

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

        1. DateTime with explicit timezone: "2025-12-28 14:30 UTC+8"

        2. DateTime without timezone: "2025-12-28 14:30" (uses TIMEZONE_OFFSET from .env)

        3. Date only: "2025-12-28" (converted to midnight UTC+0)

    Args:

        datetime_str: DateTime string in one of the supported formats



    Returns:

    Unix timestamp (int)

    Raises:

    ValueError: If format is invalid

    Environment Variables:

    TIMEZONE_OFFSET: Default timezone offset (e.g., "+8", "-5"). Defaults to "+0" if not set.
    """
    datetime_str = datetime_str.strip()

    # Get default timezone offset from environment
    default_offset = os.environ.get("TIMEZONE_OFFSET", "+0")
    
    # Pattern 1: DateTime with explicit timezone "YYYY-MM-DD HH:MM UTC±offset"
    pattern_datetime_tz = r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC([+-]\d+)'
    match = re.match(pattern_datetime_tz, datetime_str)
    
    if match:
        date_part, time_part, offset_hours = match.groups()
        dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        offset = timedelta(hours=int(offset_hours))
        tz = timezone(offset)
        dt_aware = dt.replace(tzinfo=tz)
        return int(dt_aware.timestamp())
    
    # Pattern 2: DateTime without timezone "YYYY-MM-DD HH:MM"
    pattern_datetime_no_tz = r'^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})$'
    match = re.match(pattern_datetime_no_tz, datetime_str)
    
    if match:
        date_part, time_part = match.groups()
        dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        offset = timedelta(hours=int(default_offset))
        tz = timezone(offset)
        dt_aware = dt.replace(tzinfo=tz)
        logger.debug(f"Using default timezone offset {default_offset} for datetime: {datetime_str}")
        return int(dt_aware.timestamp())
    
    # Pattern 3: Date only "YYYY-MM-DD"
    pattern_date = r'^(\d{4}-\d{2}-\d{2})$'
    match = re.match(pattern_date, datetime_str)
    
    if match:
        date_part = match.groups()[0]
        dt = datetime.strptime(f"{date_part} 00:00", "%Y-%m-%d %H:%M")
        # Dates are always midnight UTC+0
        tz = timezone(timedelta(hours=0))
        dt_aware = dt.replace(tzinfo=tz)
        logger.debug(f"Converting date to midnight UTC: {datetime_str}")
        return int(dt_aware.timestamp())
    
    raise ValueError(
        f"Invalid datetime format. Expected formats:\n"
        f"  - DateTime with timezone: 'YYYY-MM-DD HH:MM UTC±offset' (e.g., '2025-12-28 14:30 UTC+8')\n"
        f"  - DateTime without timezone: 'YYYY-MM-DD HH:MM' (e.g., '2025-12-28 14:30')\n"
        f"  - Date only: 'YYYY-MM-DD' (e.g., '2025-12-28')\n"
        f"Got: '{datetime_str}'"
    )


def preprocess_datetime_values(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert datetime strings to Unix timestamps.

    Detects and converts:

        - "YYYY-MM-DD HH:MM UTC±offset" → Unix timestamp

        - "YYYY-MM-DD HH:MM" → Unix timestamp (uses TIMEZONE_OFFSET)

        - "YYYY-MM-DD" → Unix timestamp (midnight UTC)

    Leaves other values unchanged, including:

        - Reference Lists: ["L", row_id1, row_id2, ...]

        - Choice Lists: ["L", "item1", "item2", ...]

        - All other column types
    """
    # Patterns for detection
    datetime_with_tz_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC[+-]\d+$'
    datetime_no_tz_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    processed = []
    for record in records:
        new_record = {}
        for key, value in record.items():
            if isinstance(value, str):
                if (re.match(datetime_with_tz_pattern, value) or 
                    re.match(datetime_no_tz_pattern, value) or 
                    re.match(date_pattern, value)):
                    # Convert datetime/date string to Unix timestamp
                    timestamp = parse_datetime_to_unix(value)
                    new_record[key] = timestamp
                else:
                    # Regular string, leave it alone
                    new_record[key] = value
            else:
                # Not a string (could be int, list, bool, etc.), leave it alone
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
    ===========================================

    Use simple string formats - automatic conversion to Unix timestamps:

        - DateTime (with timezone): "2025-12-28 14:30 UTC+8" → Unix timestamp

        - DateTime (without timezone): "2025-12-28 14:30" → Unix timestamp (uses TIMEZONE_OFFSET)

        - Date (date only): "2025-12-28" → Unix timestamp (midnight UTC)

    Examples:

    {"Due_Date": "2025-12-30", "Created_At": "2025-12-28 14:30"}

    COMPLEX COLUMN TYPES
    ====================

    Other complex types require manual encoding:

    Choice List:        ["L", "item1", "item2", ...]

                        Example: {"Tags": ["L", "Urgent", "Planning"]}

    Reference:          row_id (integer)

                        Example: {"Lead": 17}

    Reference List:     ["L", row_id1, row_id2, ...]

                        Example: {"Team": ["L", 15, 16, 17]}

    REGULAR COLUMN TYPES
    ====================

    Use plain values (no encoding needed):

    Text:               "Hello World"
    Numeric:            42 or 3.14
    Choice (single):    "High"
    Boolean:            true or false

    Configuration:

        - Set TIMEZONE_OFFSET in .env file (e.g., TIMEZONE_OFFSET=+8 for Malaysia)

        - Defaults to UTC+0 if not configured.

    COMPLETE EXAMPLE
    ================

    records = [{
        "Name": "Q1 Planning",                      # Text
        "Priority": "High",                         # Choice (single)
        "Tags": ["L", "Urgent", "Planning"],        # Choice List
        "Lead": 17,                                 # Reference
        "Team": ["L", 8, 9, 10],                    # Reference List
        "Start_Date": "2025-01-15",                 # Date (auto-converted)
        "Created_At": "2025-12-28 14:30",           # DateTime (auto-converted)
        "Budget": 50000,                            # Numeric
        "Active": true                              # Boolean
    }]

    Args:

        doc_id: The ID of the Grist document

        table_id: The table ID

        records: List of records to add. Every record is a dictionary where the

                 keys are the column IDs (not labels), and the values are the data.

                 Example: [{"Name": "Smith", "First_Name": "John", "Age": 35}]



    Returns:

    Dict with status, message, and IDs of created records:

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
    -------------------------------

    Datetime strings are automatically converted to Unix timestamps:

        - DateTime with timezone: "2025-12-28 14:30 UTC+8" → Unix timestamp

        - DateTime without timezone: "2025-12-28 14:30" → Unix timestamp (uses TIMEZONE_OFFSET)

        - Date: "2025-12-28" → Unix timestamp (midnight UTC)

    For other column types (Choice List, Reference, Reference List),

    see add_grist_records() docstring for complete documentation.

    Configuration:

        - Set TIMEZONE_OFFSET in .env file (e.g., TIMEZONE_OFFSET=+8)

    Prerequisites:

        - list_tables, list_columns: performed automatically internally

    Typical workflow:

        1. get_table_schema(doc_id, table_id) → understand the types

        2. add_grist_records_safe(doc_id, table_id, records) → validated insertion

        3. list_records(doc_id, table_id, limit=5) → check the result

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        Records: List of records to add. Every record is a dictionary where the

                 keys are the column IDs (not labels), and the values are the data.

                 Column validation with helpful suggestions happens automatically.



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
    -------------------------------

    Datetime strings are automatically converted to Unix timestamps:

        - DateTime with timezone: "2025-12-28 14:30 UTC+8" → Unix timestamp

        - DateTime without timezone: "2025-12-28 14:30" → Unix timestamp (uses TIMEZONE_OFFSET)

        - Date: "2025-12-28" → Unix timestamp (midnight UTC)

    For other column types (Choice List, Reference, Reference List),

    see add_grist_records() docstring for complete documentation.

    Configuration:

        - Set TIMEZONE_OFFSET in .env file (e.g., TIMEZONE_OFFSET=+8)

    Prerequisites:

        - list_records: To obtain the IDs of the records to update

    Typical workflow:

        1. list_records(doc_id, table_id) → get the IDs

        2. update_grist_records(doc_id, table_id, records_with_id) → update

    Args:

        doc_id: The ID of the document

        table_id: The table ID

        records: List of records to update. Each record must contain an 'id' field

                 plus any column IDs to update (use list_records to see structure).

                 Example: [{"id": 5, "Status": "Active", "Expiry_Date": "2027-03-28"}]



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

        record_ids: List of record IDs to delete

                    Example: [77, 78, 79]


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
