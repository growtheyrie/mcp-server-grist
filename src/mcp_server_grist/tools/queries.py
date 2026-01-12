"""
SQL query tools for the Grist API.

This module contains MCP tools for running SQL queries on
Grist data, allowing filtering, sorting, and analysis.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from ..client import get_client

# Configure the logger
logger = logging.getLogger("grist_mcp_server")


def register_query_tools(mcp_server):
    """
    Registers all SQL query tools in the MCP server.

    Args:
        mcp_server: The instance of the MCP server to save the tools to.
    """
    # Registering tools in the MCP server
    mcp_server.tool()(filter_sql_query)
    mcp_server.tool()(execute_sql_query)


async def filter_sql_query(
    doc_id: str,
    table_id: str,
    columns: Optional[List[str]] = None,
    where_conditions: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    ctx=None
) -> Dict[str, Any]:
    """
    Executes a filtering SQL query on a Grist table.

    Simplified version for common SQL queries without writing SQL.
    For complex queries, use execute_sql_query.

    Recommended prerequisites:
        - list_tables(doc_id): Check if the table exists
        - list_columns(doc_id, table_id): Get correct column IDs

    Alternative to:
        - list_records: When you need to filter/sort
        - execute_sql_query: Simplified version for common cases

    Typical workflow:
        1. list_columns(doc_id, table_id) → get column IDs
        2. filter_sql_query(doc_id, table_id, where_conditions={"Status": "Active"},
               order_by="Creation_Date DESC", limit=10)
        3. Process the returned records

    Use case:
        - Simple filtering: where_conditions={"Status": "Active"}
        - Multiple filtering: where_conditions={"Status": "Active", "Type": "A"}
        - Datetime filtering: where_conditions={"Created_At": "2025-01-08 14:30"}
        - Date filtering: where_conditions={"Start_Date": "2025-01-15"}
        - Sort: order_by="Name" or order_by="Value DESC"
        - Pagination: limit=20
        - Specific columns: columns=["Name", "Value", "Expiry_Date"]

    Datetime handling:
        - Use human-readable datetime strings: "2025-01-08 14:30"
        - Use date strings for date columns: "2025-01-15"
        - Automatic conversion to/from Unix timestamps happens internally
        - Result columns ending with "At" or "Date" are converted to readable strings

    Args:
        - doc_id: Document ID
        - table_id: ID of the table to query
        - columns: List of column IDs to return (None = all); use column IDs
              (e.g., "Start_Date"), not labels ("Start Date")
        - where_conditions: 
              - Dict of exact-match filters
              - Implicit AND between conditions
              - No operators (>, <, LIKE) permitted
              - Datetime strings are automatically converted
              - Format: {"Column_ID": value}; Text: {"Status": "Active"} (case-sensitive);
                    Numeric: {"Budget": 50000}; Datetime: {"Created_At": "2025-01-08 14:30"};
                    Date: {"Start_Date": "2025-01-15"}; Boolean: {"Active": 1} for true,
                    {"Active": 0} for false (SQLite uses integers)
        - order_by: Sort specification using column ID (e.g., "Start_Date DESC")
        - limit: Maximum number of results

    Returns:
        Dict with filtered records (timestamps converted to readable strings) and query metadata

 Examples:
        # Filter by status
        filter_sql_query(
            doc_id="abc123",
            table_id="Projects",
            where_conditions={"Status": "Active"}
        )

        # Filter by datetime
        filter_sql_query(
            doc_id="abc123",
            table_id="Sessions",
            where_conditions={"Scheduled_At": "2025-01-15 14:30"}
        )

        # Multiple conditions with sorting
        filter_sql_query(
            doc_id="abc123",
            table_id="Projects",
            where_conditions={"Status": "Active", "Priority": "High"},
            order_by="Created_At DESC",
            limit=10
        )
    """
    logger.info(f"Tool called: filter_sql_query for doc_id: {doc_id}, table_id: {table_id}")

    try:
        # Import preprocessing function from records module
        from .records import preprocess_datetime_values

        # Build SQL query
        columns_str = "*"
        if columns:
            columns_str = ", ".join([f'"{col}"' for col in columns])

        sql_query = f'SELECT {columns_str} FROM "{table_id}"'

        params = []

        # Add WHERE conditions
        if where_conditions:
            # Preprocess where_conditions: convert datetime strings to timestamps
            wrapped_conditions = [where_conditions]
            processed_conditions = preprocess_datetime_values(wrapped_conditions)[0]

            conditions = []
            for col, value in processed_conditions.items():
                conditions.append(f'"{col}" = ?')
                params.append(value)

            if conditions:
                sql_query += f" WHERE {' AND '.join(conditions)}"

        # Add ORDER BY
        if order_by:
            sql_query += f" ORDER BY {order_by}"

        # Add LIMIT
        if limit is not None:
            sql_query += f" LIMIT {limit}"

        # Run the SQL query generated via execute_sql_query
        # Note: execute_sql_query handles both parameter preprocessing and result postprocessing
        return await execute_sql_query(
            doc_id=doc_id,
            sql_query=sql_query,
            parameters=params,
            ctx=ctx
        )

    except Exception as e:
        logger.error(f"Error in filter_sql_query: {str(e)}")
        return {
            "success": False,
            "message": f"Error filtering data in SQL: {str(e)}",
            "query": "",
            "records": [],
            "record_count": 0
        }


async def execute_sql_query(
    doc_id: str,
    sql_query: str,
    parameters: Optional[List[Union[str, int, float]]] = None,
    timeout_ms: Optional[int] = 1000,
    ctx=None
) -> Dict[str, Any]:
    """
    Executes a custom SQL query on a Grist document.

    Allows complex SQL queries with joins, aggregations, and subqueries.
    Grist documents are SQLite databases - queries are run by SQLite.

    Prerequisites:
        - list_tables: See available table names
        - list_columns: See column names to query

    Typical workflow:
        1. list_tables(doc_id) → get table IDs
        2. list_columns(doc_id, table_id) → get columns IDs
        3. execute_sql_query(doc_id, '''SELECT t1."Name", t2."Email" FROM "Projects" t1
                                        JOIN "Users" t2 ON t1."Lead_ID" = t2."id"
                                        WHERE t1."Status" = ?''',
                             parameters=["Active"])

    Table and column identifiers:
        - Use table IDs (e.g., Project_Tracker), not table names (Project Tracker)
        - Use column IDs (e.g., Project_Name), not column labels (Project Name)
        - Quote identifiers with double quotes (SQL best practice)
        - Example: SELECT "Project_Name", "Start_Date" FROM "Project_Tracker"
              WHERE "Status" = ?

    Datetime handling:
        - Use human-readable datetime strings in parameters: "2025-01-08 14:30"
        - Use date strings for date columns: "2025-01-15"
        - Automatic conversion to/from Unix timestamps happens internally
        - Result columns ending with "At" or "Date" are converted to readable strings

    Security:
        - Always use bound parameters (?) for variable values
        - Example: WHERE Status = ? with parameters=["Active"]
        - Never interpolate values directly into SQL string

    Limitations:
        - Only SELECT statements allowed (no INSERT, UPDATE, DELETE)
        - No trailing semicolons
        - WITH clauses permitted for CTEs
        - Modify operations not supported

    Args:
        - doc_id: Document ID
        - sql_query: SQL query to execute (SELECT only, no semicolon)
        - parameters: Bound parameters for the '?' placeholders;
              array of strings, numbers, or None;
              example: ["Active", 50000] for WHERE Status = ? AND Budget > ?
        - timeout_ms: Query timeout in milliseconds (default: 1000, cannot exceed default)

    Returns:
        Dict with query results (timestamps converted to readable strings) and metadata

    Examples:
        # Simple query with filter
        execute_sql_query(
            doc_id="abc123",
            sql_query='SELECT "Name", "Created_At" FROM "Projects" WHERE "Created_At" > ?',
            parameters=["2025-01-01 00:00"]
        )

        # Join with aliases
        execute_sql_query(
            doc_id="abc123",
            sql_query='''
                SELECT p."Name", p."Start_Date", u."Email"
                FROM "Projects" p
                JOIN "Users" u ON p."Lead" = u."id"
                WHERE p."Budget" > ? AND p."Status" = ?
            ''',
            parameters=[50000, "Active"]
        )

        # Aggregation with datetime
        execute_sql_query(
            doc_id="abc123",
            sql_query='''
                SELECT "Priority", MAX("Created_At") as "Latest_Created_At"
                FROM "Projects"
                WHERE "Status" = ?
                GROUP BY "Priority"
            ''',
            parameters=["Active"]
        )
    """
    logger.info(f"Tool called: execute_sql_query for doc_id: {doc_id}")

    try:
        # Import preprocessing/postprocessing functions from records module
        from .records import preprocess_datetime_values, postprocess_datetime_values
        import os

        # Get timezone from environment
        timezone_name = os.environ.get("TIMEZONE", "Europe/London")

        # Verify that the query is a SELECT query
        sql_query = sql_query.strip()
        if not re.match(r'^SELECT\s', sql_query, re.IGNORECASE):
            return {
                "success": False,
                "message": "Only SELECT requests are allowed for security reasons.",
                "query": sql_query,
                "records": [],
                "record_count": 0
            }

        # Preprocess parameters: convert datetime strings to timestamps
        processed_params = parameters or []
        if processed_params:
            # Wrap parameters in dict format for preprocessing
            wrapped_params = [{"val": p} for p in processed_params]
            processed_wrapped = preprocess_datetime_values(wrapped_params)
            processed_params = [d["val"] for d in processed_wrapped]

        client = get_client(ctx)
        if not client:
            return {
                "success": False,
                "message": "Grist client not configured",
                "query": sql_query,
                "records": [],
                "record_count": 0
            }

        # Prepare SQL query
        query_data = {
            "sql": sql_query,
            "args": processed_params
        }

        if timeout_ms:
            query_data["timeout"] = timeout_ms

        # Run SQL query
        response = await client._request(
            method="POST",
            endpoint=f"/docs/{doc_id}/sql",
            json_data=query_data
        )

        # Extract and format results
        statement = response.get("statement", sql_query)
        records = response.get("records", [])

        # Add IDs if needed
        for i, record in enumerate(records):
            if "id" not in record:
                record["id"] = i + 1

        # Postprocess records: convert timestamps to readable datetime strings
        records = postprocess_datetime_values(records, timezone_name)
        
        return {
            "success": True,
            "message": f"SQL query executed successfully. {len(records)} records found.",
            "query": sql_query,
            "statement": statement,
            "records": records,
            "record_count": len(records)
        }

    except Exception as e:
        logger.error(f"Error in execute_sql_query: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing SQL query: {str(e)}",
            "query": sql_query,
            "records": [],
            "record_count": 0
        }
