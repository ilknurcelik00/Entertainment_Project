"""Apply the project's idempotent Oracle SQL migrations."""

import os
import re
from pathlib import Path

import oracledb
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql"
load_dotenv(PROJECT_ROOT / ".env")


def split_oracle_script(script_text):
    return [
        statement.strip()
        for statement in re.split(r"(?m)^\s*/\s*$", script_text)
        if statement.strip()
    ]


def execute_statement(cursor, statement):
    statement = re.sub(r"(?m)^\s*--.*(?:\r?\n|$)", "", statement).strip()
    if not statement:
        return
    if statement.upper() == "COMMIT":
        return
    if statement.endswith(";") and not statement.lstrip().upper().startswith(
        ("BEGIN", "DECLARE", "CREATE OR REPLACE TRIGGER")
    ):
        statement = statement[:-1]
    cursor.execute(statement)


def main():
    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN"),
    )
    cursor = connection.cursor()

    try:
        for migration_path in sorted(SQL_DIR.glob("[0-9][0-9][0-9]_*.sql")):
            print(f"Migration uygulanıyor: {migration_path.name}")
            script_text = migration_path.read_text(encoding="utf-8")
            for statement in split_oracle_script(script_text):
                execute_statement(cursor, statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    print("Oracle migration işlemleri tamamlandı.")


if __name__ == "__main__":
    main()
