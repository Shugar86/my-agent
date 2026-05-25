import sqlite3, json, os
try:
    import asyncpg
except ImportError:
    asyncpg = None


def query_sqlite(db_path: str, query: str, params: list = None) -> dict:
    from core.validation import validate_safe_path, validate_sql
    if not validate_safe_path(db_path, "db_path"):
        return {"error": f"Invalid db_path: {db_path}"}
    if not validate_sql(query):
        return {"error": f"Invalid SQL query: {query}"}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params or [])
        # Safe: cursor.description is not None for SELECT-like statements
        if cur.description is not None:
            rows = [dict(r) for r in cur.fetchall()]
            result = {"rows": rows, "count": len(rows)}
        else:
            conn.commit()
            result = {"affected": cur.rowcount, "last_id": cur.lastrowid}
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}


async def query_postgres(conn_string: str, query: str, params: list = None) -> dict:
    try:
        conn = await asyncpg.connect(conn_string)
        # Security: always use prepared statements, never string-based SELECT detection
        stmt = await conn.prepare(query)
        if stmt.get_rows_count() if hasattr(stmt, 'get_rows_count') else True:
            # Heuristic: if statement returns rows, fetch them
            try:
                rows = await stmt.fetch(*(params or []))
                result = {"rows": [dict(r) for r in rows], "count": len(rows)}
            except asyncpg.exceptions.PostgresError:
                # Non-SELECT: execute instead
                r = await conn.execute(query, *(params or []))
                result = {"affected": r}
        await conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}


def list_tables(db_path: str, db_type: str = "sqlite") -> dict:
    if db_type == "sqlite":
        return query_sqlite(db_path, "SELECT name FROM sqlite_master WHERE type='table'")
    return {"error": "Unsupported db_type"}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="query_sqlite",
        description="Execute SQL query on a SQLite database file. Supports SELECT, INSERT, UPDATE, DELETE.",
        parameters={"type": "object", "properties": {
            "db_path": {"type": "string"},
            "query": {"type": "string"},
            "params": {"type": "array", "items": {"type": "string"}},
        }},
        execute_fn=lambda db_path="", query="", params=None: query_sqlite(db_path, query, params),
    )
    registry.register(
        name="list_tables",
        description="List all tables in a SQLite database",
        parameters={"type": "object", "properties": {
            "db_path": {"type": "string"},
        }},
        execute_fn=lambda db_path="": list_tables(db_path),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["query_sqlite", "list_tables"]:
        registry.unregister(name)
