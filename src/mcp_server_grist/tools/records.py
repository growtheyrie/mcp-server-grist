"""
Record management tools for the Grist API.

This module contains MCP tools for manipulating records
in Grist tables: add, update, and delete.
"""

import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

from ..client import get_client

# Cofingure the logger
logger = logging.getLogger("grist_mcp_server")

# Load environment variables
load_dotenv()

# Curate list of major IANA timezones with their UTC offsets
TIMEZONE_OFFSETS = {
    "Australia/Sydney": 11.0,
    "Asia/Tokyo": 9.0,
    "Asia/Shanghai": 8.0,
    "Asia/Kuala_Lumpur": 8.0,
    "Asia/Kolkata": 5.5,
    "Asia/Dubai": 4.0,
    "Europe/Paris": 1.0,
    "Europe/London": 0.0,
    "America/New_York": -5.0,
    "America/Los_Angeles": -8.0,
}

def register_record_tools(mcp_server):
    """
    Registers all record management tools on the MCP server.
    
    Args:
        mcp_server: The instance of the MCP server to save the tools to.
    """
    # Registering tools on the MCP server
    mcp_server.tool()(add_grist_records)
    mcp_server.tool()(add_grist_records_safe)
    mcp_server.tool()(update_grist_records)
    mcp_server.tool()(delete_grist_records)


# --- Helper Method for DateTime Conversion ---
def parse_datetime_to_unix(datetime_str: str) -> int:
    """
    Convert a datetime or date string to a Unix timestamp (seconds).

    Supported input formats:
        - "YYYY-MM-DD HH:MM"        (datetime; uses TIMEZONE environment variable)
        - "YYYY-MM-DD"              (date only; interpreted as midnight UTC)

    Environment Variables:
        TIMEZONE: IANA timezone name (e.g., "Asia/Kuala_Lumpur", "America/New_York").
                  Defaults to "Europe/London" if not set or not in curated timezone list.

    Args:
        - datetime_str: Datetime or date string to convert into a timestamp

    Returns:
        Unix timestamp in seconds (UTC-aware)

    Raises:
        ValueError: If format is invalid
    """
    datetime_str = datetime_str.strip()

    # Get timezone from environment and look up offset
    timezone_name = os.environ.get("TIMEZONE", "Europe/London")
    default_offset = TIMEZONE_OFFSETS.get(timezone_name, 0.0)
    
    # Pattern 1: DateTime "YYYY-MM-DD HH:MM"
    pattern_datetime_no_tz = r'^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})$'
    match = re.match(pattern_datetime_no_tz, datetime_str)
    
    if match:
        date_part, time_part = match.groups()
        dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        offset = timedelta(hours=default_offset) # Use fractional offset from IANA timezone
        tz = timezone(offset)
        dt_aware = dt.replace(tzinfo=tz)
        logger.debug(f"Using timezone {timezone_name} (UTC{default_offset:+.1f}) for datetime: {datetime_str}")
        return int(dt_aware.timestamp())
    
    # Pattern 2: Date only "YYYY-MM-DD"
    pattern_date = r'^(\d{4}-\d{2}-\d{2})$'
    match = re.match(pattern_date, datetime_str)
    
    if match:
        date_part = match.groups()[0]
        dt = datetime.strptime(f"{date_part} 00:00", "%Y-%m-%d %H:%M")
        tz = timezone(timedelta(hours=0)) # Dates are always midnight UTC+0
        dt_aware = dt.replace(tzinfo=tz)
        logger.debug(f"Converting date to midnight UTC: {datetime_str}")
        return int(dt_aware.timestamp())
    
    raise ValueError(
        f"Invalid datetime format. Expected formats:\n"
        f"  - DateTime: 'YYYY-MM-DD HH:MM' (e.g., '2025-12-28 14:30')\n"
        f"  - Date only: 'YYYY-MM-DD' (e.g., '2025-12-28')\n"
        f"Got: '{datetime_str}'"
    )


def convert_unix_to_datetime(timestamp: int, timezone_name: str, is_date_only: bool = False) -> str:
    """
    Convert a Unix timestamp (seconds) to a human-readable datetime or date string.
    
    Internal helper function - reverse of parse_datetime_to_unix.
    
    Args:
        - timestamp: Unix timestamp in seconds (UTC)
        - timezone_name: IANA timezone name (e.g., "Asia/Kuala_Lumpur")
        - is_date_only: If True, return date only "YYYY-MM-DD", otherwise "YYYY-MM-DD HH:MM"
    
    Returns:
        Formatted datetime string in local timezone
    """
    # Look up timezone offset
    offset_hours = TIMEZONE_OFFSETS.get(timezone_name, 0.0)
    offset = timedelta(hours=offset_hours)
    tz = timezone(offset)
    
    # Convert timestamp to datetime in the specified timezone
    dt = datetime.fromtimestamp(timestamp, tz=tz)
    
    if is_date_only:
        # Return date only "YYYY-MM-DD"
        return dt.strftime("%Y-%m-%d")
    else:
        # Return datetime "YYYY-MM-DD HH:MM"
        return dt.strftime("%Y-%m-%d %H:%M")


def preprocess_datetime_values(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scan a list of record dicts and convert datetime strings to Unix timestamps.

    Detects and converts:
        - "YYYY-MM-DD HH:MM" → Unix timestamp (uses TIMEZONE env var)
        - "YYYY-MM-DD" → Unix timestamp (midnight UTC)

    Leaves other values unchanged, including:
        - Reference Lists: ["L", row_id1, row_id2, ...]
        - Choice Lists: ["L", "item1", "item2", ...]
        - All other column types
    """
    # Patterns for detection
    datetime_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    processed = []
    for record in records:
        new_record = {}
        for key, value in record.items():
            if isinstance(value, str):
                if (re.match(datetime_pattern, value) or 
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


def postprocess_datetime_values(records: List[Dict[str, Any]], timezone_name: str) -> List[Dict[str, Any]]:
    """
    Scan a list of record dicts and convert Unix timestamps to human-readable strings.
    
    Internal helper function that handles both flat structure and nested "fields" structure.
    Uses naming convention to detect datetime/date columns:
        - Columns ending with "At" → DateTime (converted to "YYYY-MM-DD HH:MM")
        - Columns ending with "Date" → Date (converted to "YYYY-MM-DD")
    
    Args:
        - records: List of record dicts from Grist API
        - timezone_name: IANA timezone name for conversion
    
    Returns:
        Modified records with timestamps converted to human-readable strings
    """
    processed = []

    for record in records:
        new_record = {}
        for key, value in record.items():
            if key == "fields" and isinstance(value, dict):
                # Process nested fields dict
                new_fields = {}
                for field_key, field_value in value.items():
                    # Check if this is a datetime/date column by naming convention
                    is_datetime = field_key.endswith("At")
                    is_date = field_key.endswith("Date")
                    
                    if (is_datetime or is_date) and isinstance(field_value, (int, float)) and field_value is not None:
                        # Convert timestamp to human-readable string
                        try:
                            new_fields[field_key] = convert_unix_to_datetime(
                                int(field_value), 
                                timezone_name, 
                                is_date_only=is_date
                            )
                        except Exception as e:
                            # If conversion fails, keep original value
                            logger.warning(f"Failed to convert timestamp for column {field_key}: {e}")
                            new_fields[field_key] = field_value
                    else:
                        # Not a datetime/date column, or value is None, keep as-is
                        new_fields[field_key] = field_value
                new_record[key] = new_fields
            else:
                # Process top-level fields (original behavior)
                is_datetime = key.endswith("At")
                is_date = key.endswith("Date")
                
                if (is_datetime or is_date) and isinstance(value, (int, float)) and value is not None:
                    try:
                        new_record[key] = convert_unix_to_datetime(
                            int(value), 
                            timezone_name, 
                            is_date_only=is_date
                        )
                    except Exception as e:
                        logger.warning(f"Failed to convert timestamp for column {key}: {e}")
                        new_record[key] = value
                else:
                    new_record[key] = value
        
        processed.append(new_record)
    
    return processed

async def add_grist_records(doc_id: str,
                            table_id: str,
                            records: List[Dict[str, Any]],
                            ctx=None) -> Dict[str, Any]:
    """
    Adds records to a Grist table.

    Column type and encoding brief:
        - Text: plain string, e.g. `"Name": "Alice"`
        - Numeric: int/float, e.g. `"Budget": 50000`
        - Boolean: true/false, e.g. `"Active": true`
        - Choice (single): string, e.g. `"Priority": "High"`
        - Choice list: array of strings with "L" prefix, e.g. `"Tags": ["L", "Urgent", "Planning"]`
        - Reference (single): integer row id, e.g. `"Lead": 17`
        - Reference list: array of integer row ids with "L" prefix, e.g. `"Team": ["L", 8, 9, 10]`
        - Datetime (with timezone): string, e.g. `"Created_At": "2025-12-28 14:30 UTC+8"`
        - Datetime (without timezone): string, e.g. `"Tested_At": "2025-12-28 14:30"`
        - Date (date only): string, e.g. `"Due_Date": "2025-12-30"`

    Datetime and date brief:
        - String values will automatically be converted into Unix timestamps in seconds UTC
              for storage in Grist.
        - Datetimes without timezones will automatically be assigned a timezone. This timezone
              is determined by the TIMEZONE_OFFSET (e.g., "+8", "-5") from UTC, an environment
              variable that defaults to "+0" if not set by the user.

    Args:
        - doc_id: The ID of the Grist document
        - table_id: The table ID
        - records: List of records to add. Every record is a dictionary where the
              keys are the column IDs (not labels), and the values are the data.
              Example:
                  records = [{
                      "Name": "Q1 Planning",
                      "Priority": "High",
                      "Tags": ["L", "Urgent", "Planning"],
                      "Lead": 17,
                      "Team": ["L", 8, 9, 10],
                      "Start_Date": "2025-01-15",
                      "Created_At": "2025-12-28 14:30",
                      "Budget": 50000,
                      "Active": true
                  }]

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
                "message": "Grist client not configured",
                "record_ids": []
            }

       # Preprocess datetime strings
        records = preprocess_datetime_values(records)

        record_ids = await client.add_records(doc_id, table_id, records)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} records successfully added",
            "record_ids": record_ids
        }
    except Exception as e:
        logger.error(f"Error in add_grist_records: {str(e)}")
        return {
            "success": False,
            "message": f"Error adding records: {str(e)}",
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

    References:
        - add_grist_records docstring: See column type encoding, datetime handling
              details, and complete example for records argument.

    Prerequisites:
        - list_tables, list_columns: performed automatically internally

    Typical workflow:
        1. get_table_schema(doc_id, table_id) → understand column types
        2. add_grist_records_safe(doc_id, table_id, records) → validated insertion
        3. list_records(doc_id, table_id, limit=5) → check the result

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID
        - records: List of records to add. Every record is a dictionary where the
              keys are the column IDs (not labels), and the values are the data.
              Column validation with helpful suggestions happens automatically.

    Returns:
        Dict with status, message, possible correction suggestions,
        and IDs of the records created if the operation was successful.
    """
    logger.info(
        f"Tool called: add_grist_records_safe for doc_id: {doc_id}, table_id: {table_id}"
    )

    try:
        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured",
                "record_ids": []
            }

        # Validation 1: Check if the table exists
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

        # Validation 2: Check column names if records are provided
        if records and isinstance(records, list) and len(records) > 0:
            # Extract all column names in use
            column_names = set()
            for record in records:
                column_names.update(record.keys())

            # Validate the existence of columns
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

        # If everything is valid, add the records
        record_ids = await client.add_records(doc_id, table_id, records)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} records successfully added after validation",
            "record_ids": record_ids
        }
    except Exception as e:
        logger.error(f"Error in add_grist_records_safe: {str(e)}")
        return {
            "success": False,
            "message":
            f"Error when securely adding records: {str(e)}",
            "record_ids": []
        }


async def update_grist_records(doc_id: str,
                               table_id: str,
                               records: List[Dict[str, Any]],
                               ctx=None) -> Dict[str, Any]:
    """
    Updates existing records in a Grist table.

    References:
        - add_grist_records docstring: See column type encoding and datetime handling
             details.

    Prerequisites:
        - list_records: To obtain the IDs of the records to update

    Typical workflow:
        1. list_records(doc_id, table_id) → get the IDs
        2. update_grist_records(doc_id, table_id, records_with_id) → update

    Args:
        - doc_id: The ID of the document
        - table_id: The table ID
        - records: List of records to update. Each record must contain an 'id' field
              plus any column IDs to update (keys are column IDs, not labels).
              Example:
                  [{
                      "id": 5,
                      "Status": "Active",
                      "Expiry_Date": "2027-03-28"
                  }]

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
                "message": "Grist client not configured",
                "record_ids": []
            }

        # Vérify that all records have IDs
        for i, record in enumerate(records):
            if "id" not in record:
                return {
                    "success": False,
                    "message":
                    f"The ID in index {i} is not an integer. IDs must be integers.",
                    "record_ids": []
                }

        # Preprocess datetime strings
        records = preprocess_datetime_values(records)

        record_ids = await client.update_records(doc_id, table_id, records)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} records successfully updated",
            "record_ids": record_ids
        }
    except Exception as e:
        logger.error(f"Error in update_grist_records: {str(e)}")
        return {
            "success": False,
            "message":
            f"Error when updating records: {str(e)}",
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
        - doc_id: The ID of the document
        - table_id: The table ID
        - record_ids: List of record IDs to delete
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
            return {"success": False, "message": "Grist client not configured"}

        # Check that all IDs are integers
        for i, record_id in enumerate(record_ids):
            if not isinstance(record_id, int):
                return {
                    "success":
                    False,
                    "message":
                    f"L'ID à l'index {i} ({record_id}) is not an integer. IDs must be integers."
                }

        await client.delete_records(doc_id, table_id, record_ids)

        return {
            "success": True,
            "message":
            f"{len(record_ids)} records successfully deleted"
        }
    except Exception as e:
        logger.error(f"Error in delete_grist_records: {str(e)}")
        return {
            "success": False,
            "message":
            f"Error when deleting records: {str(e)}"
        }
