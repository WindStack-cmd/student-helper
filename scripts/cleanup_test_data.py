import os
from collections import defaultdict

import mysql.connector
from dotenv import load_dotenv

TEST_EMAILS = ("john@test.com", "usera@gmail.com", "userb@gmail.com")


def load_db_config(env_path: str) -> dict:
    load_dotenv(env_path)
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "student_helper"),
        "port": int(os.getenv("DB_PORT", "3306")),
    }


def pick_column(cursor, database_name: str, table_name: str, candidates: tuple[str, ...]) -> str:
    query = (
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
    )
    cursor.execute(query, (database_name, table_name))
    table_columns = {row[0] for row in cursor.fetchall()}

    for col in candidates:
        if col in table_columns:
            return col

    raise RuntimeError(
        f"None of the expected columns {candidates} were found in table '{table_name}'."
    )


def main() -> None:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(project_root, "backend", ".env")

    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Missing environment file: {env_path}")

    db_config = load_db_config(env_path)

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    database_name = db_config["database"]
    claims_email_col = pick_column(cursor, database_name, "claims", ("user_email", "email"))
    notifications_email_col = pick_column(cursor, database_name, "notifications", ("user_email", "email"))
    requests_email_col = pick_column(cursor, database_name, "requests", ("user_email", "email"))
    answers_email_col = pick_column(cursor, database_name, "answers", ("user_email", "email", "helper_email"))
    posts_email_col = pick_column(cursor, database_name, "posts", ("user_email", "email"))

    ordered_deletions = [
        (
            "Step 1",
            "claims",
            f"DELETE FROM claims WHERE {claims_email_col} IN (%s, %s, %s)",
            TEST_EMAILS,
        ),
        (
            "Step 2",
            "notifications",
            f"DELETE FROM notifications WHERE {notifications_email_col} IN (%s, %s, %s)",
            TEST_EMAILS,
        ),
        (
            "Step 3",
            "answers",
            "DELETE FROM answers WHERE request_id IN ("
            f"SELECT id FROM requests WHERE {requests_email_col} IN (%s, %s, %s)"
            ")",
            TEST_EMAILS,
        ),
        (
            "Step 4",
            "answers",
            f"DELETE FROM answers WHERE {answers_email_col} IN (%s, %s, %s)",
            TEST_EMAILS,
        ),
        (
            "Step 5",
            "requests",
            f"DELETE FROM requests WHERE {requests_email_col} IN (%s, %s, %s)",
            TEST_EMAILS,
        ),
        (
            "Step 6",
            "posts",
            f"DELETE FROM posts WHERE {posts_email_col} IN (%s, %s, %s)",
            TEST_EMAILS,
        ),
        (
            "Step 7",
            "users",
            "DELETE FROM users WHERE email IN (%s, %s, %s)",
            TEST_EMAILS,
        ),
    ]

    deleted_by_table = defaultdict(int)

    try:
        for step_label, table_name, query, params in ordered_deletions:
            cursor.execute(query, params)
            step_deleted = cursor.rowcount if cursor.rowcount > 0 else 0
            deleted_by_table[table_name] += step_deleted
            print(f"{step_label} ({table_name}): deleted {step_deleted} rows")

        connection.commit()

        print("\nDeletion summary by table:")
        for table_name in ["claims", "notifications", "answers", "requests", "posts", "users"]:
            print(f"- {table_name}: {deleted_by_table[table_name]}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
