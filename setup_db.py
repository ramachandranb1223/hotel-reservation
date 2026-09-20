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

    # Enable Thick mode for Oracle Database 11g
    oracledb.init_oracle_client(
        lib_dir=r"C:\oracle\instantclient_19_32"
    )

except ImportError:
    print("Warning: python-oracledb is not installed.")

def split_oracle_statements(sql_content):
    """Splits SQL script into distinct statements, respecting PL/SQL blocks ending in /"""
    statements = []
    # If script contains PL/SQL blocks delimited by / on a new line
    blocks = re.split(r'^\s*/\s*$', sql_content, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Check if block is a PL/SQL block or regular SQL
        upper_block = block.upper()
        if any(keyword in upper_block for keyword in ("BEGIN", "DECLARE", "CREATE OR REPLACE PROCEDURE", "CREATE OR REPLACE FUNCTION", "CREATE OR REPLACE TRIGGER")):
            statements.append(block)
        else:
            # Regular SQL statements separated by semicolon
            for stmt in block.split(';'):
                stmt = stmt.strip()
                if stmt:
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
        success_count = 0
        error_count = 0

        cursor = conn.cursor()
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue
            try:
                cursor.execute(stmt)
                success_count += 1
            except Exception as ex:
                # Ignore drop table not found errors
                err_msg = str(ex)
                if "ORA-00942" in err_msg or "ORA-02289" in err_msg:
                    continue
                print(f"  [Warning in {filename}]: {err_msg[:120]}")
                error_count += 1
        
        conn.commit()
        cursor.close()
        print(f" {filename} completed. ({success_count} statements OK, {error_count} warnings)")

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
