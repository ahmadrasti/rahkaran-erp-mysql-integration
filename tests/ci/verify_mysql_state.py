"""Fail CI unless the synthetic workflow persisted and preserved its state."""
from __future__ import annotations

import argparse
import os

import pymysql


def scalar(cursor, statement: str) -> int:
    cursor.execute(statement)
    return int(cursor.fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--expected-audits", type=int, required=True)
    args = parser.parse_args()
    connection = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DATABASE"], autocommit=True)
    with connection:
        with connection.cursor() as cursor:
            for table in ("erp_customers", "erp_products", "erp_orders"):
                total = scalar(cursor, f"SELECT COUNT(*) FROM {table}")
                distinct = scalar(cursor, f"SELECT COUNT(DISTINCT {table[4:-1]}_id) FROM {table}")
                assert total == 7 and distinct == 7, f"synthetic {table} rows are not idempotent"
            assert scalar(cursor, "SELECT COUNT(*) FROM sync_state WHERE checkpoint_value <> ''") == 3, "missing checkpoints"
            assert scalar(cursor, "SELECT COUNT(*) FROM api_audit_log WHERE outcome='success'") == args.expected_audits, "unexpected synthetic audit count"


if __name__ == "__main__": main()
