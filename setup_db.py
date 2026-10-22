"""
Database Setup & Verification Utility for Oracle Database
Executes all SQL and PL/SQL scripts in chronological sequence:
1. 01_schema.sql
2. 02_constraints.sql
3. 03_sample_data.sql
4. 04_views.sql
5. 05_procedures.sql
6. 06_functions.sql
7. 07_triggers.sql
8. 08_queries.sql (Verification)
"""
import os
import sys
import re
from config import Config

try:
    import oracledb

    # Default "thin mode" connects directly to Oracle Database 12.1+ (including
    # 19c/21c/23ai) in pure Python - no Oracle Client / Instant Client needed.
    # Thick mode (which needs Instant Client) is only required for older
    # servers like Oracle 11g, so it is intentionally not enabled here.

except ImportError:
    print("Warning: python-oracledb is not installed.")

def split_oracle_statements(sql_content):
    """
    Splits an Oracle SQL script into individual statements.

    PL/SQL blocks (anonymous BEGIN...END; blocks, or CREATE OR REPLACE
    PROCEDURE/FUNCTION/TRIGGER) are terminated by a line containing only a
    forward slash ("/") and are executed as ONE statement, kept exactly as
    written (their internal semicolons are part of PL/SQL syntax).

    Everything else is plain SQL (DDL/DML) separated by semicolons; each
    one is executed on its own, WITHOUT a trailing semicolon (Oracle's
    execute() call - unlike SQL*Plus - does not want one).

    Splitting is done line-by-line (not with a single multiline regex) so it
    is not sensitive to \r\n vs \n line endings.
    """
    lines = sql_content.splitlines()
    blocks = []
    current = []
    for line in lines:
        if line.strip() == "/":
            blocks.append("\n".join(current))
            current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    plsql_markers = ("CREATE OR REPLACE PROCEDURE", "CREATE OR REPLACE FUNCTION", "CREATE OR REPLACE TRIGGER")

    statements = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Find the first line that isn't blank or a "--" comment, to decide
        # whether this block IS a PL/SQL block (as opposed to merely
        # containing the word BEGIN somewhere, e.g. inside a later comment).
        first_code_line = ""
        for line in block.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("--"):
                first_code_line = stripped.upper()
                break

        upper_block = block.upper()
        is_plsql_block = (
            first_code_line.startswith("BEGIN")
            or first_code_line.startswith("DECLARE")
            or any(marker in upper_block for marker in plsql_markers)
        )

        if is_plsql_block:
            statements.append(block)
        else:
            # Plain SQL statements separated by semicolons.
            for stmt in block.split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                # Skip chunks that are comment-only (no actual SQL left after
                # stripping "--" comment lines) - these are section headers
                # sitting between two semicolons.
                code_lines = [l for l in stmt.splitlines() if l.strip() and not l.strip().startswith("--")]
                if code_lines:
                    statements.append(stmt)
    return statements

def run_oracle_setup():
    print("=" * 70)
    print("SMART HOTEL RESERVATION - ORACLE DATABASE SETUP UTILITY")
    print("=" * 70)
    print(f"Connecting to Oracle DSN: {Config.ORACLE_DSN} as user: {Config.ORACLE_USER}")

    try:
        if Config.ORACLE_WALLET_DIR:
            conn = oracledb.connect(
                user=Config.ORACLE_USER,
                password=Config.ORACLE_PASSWORD,
                dsn=Config.ORACLE_DSN,
                wallet_location=Config.ORACLE_WALLET_DIR,
                wallet_password=Config.ORACLE_WALLET_PASSWORD
            )
        else:
            conn = oracledb.connect(
                user=Config.ORACLE_USER,
                password=Config.ORACLE_PASSWORD,
                dsn=Config.ORACLE_DSN
            )
        print(" Connected to Oracle Database successfully.")
    except Exception as e:
        print(f" Could not connect to Oracle Database: {e}")
        print("\nPlease check your .env settings or start your Oracle XE / 19c service.")
        return False

    script_files = [
        "01_schema.sql",
        "02_constraints.sql",
        "03_sample_data.sql",
        "04_views.sql",
        "05_procedures.sql",
        "06_functions.sql",
        "07_triggers.sql"
    ]

    db_dir = os.path.join(os.path.dirname(__file__), "db")

    for filename in script_files:
        filepath = os.path.join(db_dir, filename)
        if not os.path.exists(filepath):
            print(f" Script {filename} not found at {filepath}")
            continue

        print(f"\nExecuting {filename}...")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        statements = split_oracle_statements(content)
        print(f"  Found {len(statements)} statement(s) to run.")
        success_count = 0
        error_count = 0

        cursor = conn.cursor()
        for i, stmt in enumerate(statements, start=1):
            stmt = stmt.strip()
            if not stmt:
                continue
            # Skip only if EVERY line is blank or a "--" comment (a comment-only
            # chunk). A statement that merely STARTS with a header comment
            # above real SQL must still run - checking just the first line
            # (as this used to) was silently discarding almost every
            # statement in this project's SQL files.
            code_lines = [l for l in stmt.splitlines() if l.strip() and not l.strip().startswith("--")]
            if not code_lines:
                continue
            # SQL*Plus-only directives (SET, PROMPT, WHENEVER, SPOOL, ...) are not
            # valid SQL and mean nothing outside SQL*Plus itself - skip them rather
            # than sending them to the database and reporting a spurious error.
            first_word = code_lines[0].strip().split(None, 1)[0].upper() if code_lines[0].strip() else ""
            if first_word in ("SET", "PROMPT", "WHENEVER", "SPOOL"):
                continue
            try:
                cursor.execute(stmt)
                success_count += 1
            except Exception as ex:
                # Ignore drop table/sequence not found errors (expected on first run)
                err_msg = str(ex)
                if "ORA-00942" in err_msg or "ORA-02289" in err_msg:
                    continue
                preview = " ".join(stmt.split())[:80]
                print(f"  [ERROR in {filename}, statement {i}/{len(statements)}: {preview}...]")
                print(f"    {err_msg}")
                error_count += 1

        conn.commit()
        cursor.close()
        print(f" {filename} completed. ({success_count} statements OK, {error_count} errors)")

    # Run verification check
    cursor = conn.cursor()
    print("\n" + "=" * 70)
    print("VERIFYING CREATED ORACLE OBJECTS:")
    print("=" * 70)
    cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables Created ({len(tables)}): {', '.join(tables)}")

    cursor.execute("SELECT view_name FROM user_views ORDER BY view_name")
    views = [row[0] for row in cursor.fetchall()]
    print(f"Views Created ({len(views)}): {', '.join(views)}")

    cursor.execute("SELECT object_name, object_type FROM user_objects WHERE object_type IN ('PROCEDURE', 'FUNCTION', 'TRIGGER') ORDER BY object_type, object_name")
    objects = cursor.fetchall()
    print(f"PL/SQL Objects Created ({len(objects)}):")
    for obj_name, obj_type in objects:
        print(f"  - [{obj_type}] {obj_name}")

    conn.close()
    print("\n Oracle Database initialization and validation complete!")
    return True

if __name__ == "__main__":
    run_oracle_setup()
