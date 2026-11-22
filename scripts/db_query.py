"""Database Query & Inspection Tool for Nueva Ecija Travel Itinerary.

Supports executing SQL queries against either:
1. Local SQLite database (nueva_ecija_travel.db) [default]
2. Docker PostgreSQL database (via DATABASE_URL from .env or --postgres flag)

Usage:
    # 1. Run a single query directly:
    python scripts/db_query.py "SELECT name, category, rating FROM places WHERE rating >= 4.5 LIMIT 10"

    # 2. Open interactive SQL shell:
    python scripts/db_query.py

    # 3. Query PostgreSQL instead of SQLite:
    python scripts/db_query.py --postgres "SELECT count(*) FROM places"
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

DEFAULT_SQLITE_PATH = ROOT_DIR / "nueva_ecija_travel.db"


def format_table(headers: list[str], rows: list[tuple]) -> str:
    """Renders tabular data with aligned borders and columns."""
    if not headers and not rows:
        return "(Empty result set)"

    # Convert all cell values to strings, truncating very long text
    str_rows = []
    for row in rows:
        str_rows.append([
            (str(val)[:45] + "..." if isinstance(val, str) and len(str(val)) > 48 else ("NULL" if val is None else str(val)))
            for val in row
        ])

    # Determine maximum width for each column
    col_widths = [len(str(h)) for h in headers]
    for row in str_rows:
        for idx, val in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(val))
            else:
                col_widths.append(len(val))

    # Build ASCII table
    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"

    lines = [sep, header_line, sep]
    for row in str_rows:
        # Pad row with empty strings if shorter than headers
        padded = list(row) + [""] * (len(col_widths) - len(row))
        lines.append("| " + " | ".join(padded[i].ljust(col_widths[i]) for i in range(len(col_widths))) + " |")
    lines.append(sep)

    return "\n".join(lines)


def get_sqlite_connection(db_path: Path):
    import sqlite3
    if not db_path.exists():
        print(f"[!] Warning: SQLite database file not found at: {db_path}", file=sys.stderr)
    return sqlite3.connect(str(db_path))


def get_postgres_connection():
    from backend.app.core.config import Settings
    from sqlalchemy import create_engine
    settings = Settings()
    engine = create_engine(settings.database_url)
    return engine.connect()


def execute_sqlite_query(conn, query: str):
    cur = conn.cursor()
    start = time.perf_counter()
    cur.execute(query)
    elapsed = time.perf_counter() - start

    if cur.description:
        headers = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return headers, rows, elapsed, len(rows)
    else:
        conn.commit()
        return [], [], elapsed, cur.rowcount


def interactive_sqlite_shell(db_path: Path):
    import sqlite3
    conn = get_sqlite_connection(db_path)
    cur = conn.cursor()
    print("=" * 68)
    print(f" Nueva Ecija Travel Itinerary — SQLite Interactive SQL Shell")
    print(f" Connected to: {db_path.name}")
    print(" Type your SQL statement ending with ';' or type 'exit' / 'quit' to close.")
    print(" Helper commands: .tables | .schema <table> | .help")
    print("=" * 68)

    buffer = []
    while True:
        try:
            prompt = "SQL> " if not buffer else " ... "
            line = input(prompt).strip()
            if not line:
                continue

            lower_line = line.lower()
            if lower_line in ("exit", "quit", "exit;", "quit;", "\\q"):
                print("Exiting SQL shell. Goodbye!")
                break

            if lower_line == ".tables":
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
                tbls = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]
                print("Tables:\n  " + "\n  ".join(tbls))
                continue

            if lower_line.startswith(".schema"):
                parts = line.split()
                if len(parts) > 1:
                    cur.execute("SELECT sql FROM sqlite_master WHERE name = ?;", (parts[1],))
                    res = cur.fetchone()
                    print(res[0] if res else f"Table '{parts[1]}' not found.")
                else:
                    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name;")
                    for r in cur.fetchall():
                        if r[0]:
                            print(r[0] + ";\n")
                continue

            buffer.append(line)
            if line.endswith(";"):
                full_query = " ".join(buffer)
                buffer = []
                try:
                    headers, rows, elapsed, count = execute_sqlite_query(conn, full_query)
                    if headers:
                        print(format_table(headers, rows))
                        print(f"({count} row{'s' if count != 1 else ''} retrieved in {elapsed:.3f}s)\n")
                    else:
                        print(f"Query OK, {count} row{'s' if count != 1 else ''} affected in {elapsed:.3f}s\n")
                except Exception as err:
                    print(f"[!] Error: {err}\n", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting SQL shell.")
            break


def main():
    parser = argparse.ArgumentParser(description="Query Nueva Ecija Travel database")
    parser.add_argument("query", nargs="?", help="SQL query to execute (in quotes)")
    parser.add_argument("--postgres", action="store_true", help="Connect to Docker PostgreSQL instead of SQLite")
    parser.add_argument("--db-file", type=Path, default=DEFAULT_SQLITE_PATH, help="Path to SQLite database file")

    args = parser.parse_args()

    if not args.query:
        if args.postgres:
            print("[!] Interactive mode currently targets SQLite. For PostgreSQL interactive CLI, use:")
            print("    docker exec -it ne_postgres psql -U ne_travel_user -d nueva_ecija_travel")
            sys.exit(1)
        interactive_sqlite_shell(args.db_file)
        return

    query = args.query.strip()
    if not query.endswith(";"):
        query += ";"

    if args.postgres:
        from sqlalchemy import text
        try:
            conn = get_postgres_connection()
            start = time.perf_counter()
            result = conn.execute(text(query))
            elapsed = time.perf_counter() - start
            if result.returns_rows:
                headers = list(result.keys())
                rows = result.fetchall()
                print(format_table(headers, rows))
                print(f"({len(rows)} rows retrieved in {elapsed:.3f}s from PostgreSQL)")
            else:
                conn.commit()
                print(f"Query executed successfully in {elapsed:.3f}s from PostgreSQL.")
            conn.close()
        except Exception as err:
            print(f"[!] PostgreSQL Error: {err}", file=sys.stderr)
            sys.exit(1)
    else:
        conn = get_sqlite_connection(args.db_file)
        try:
            headers, rows, elapsed, count = execute_sqlite_query(conn, query)
            if headers:
                print(format_table(headers, rows))
                print(f"({count} row{'s' if count != 1 else ''} retrieved in {elapsed:.3f}s from SQLite)")
            else:
                print(f"Query OK, {count} row{'s' if count != 1 else ''} affected in {elapsed:.3f}s")
        except Exception as err:
            print(f"[!] SQLite Error: {err}", file=sys.stderr)
            sys.exit(1)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
