"""Initialize only the generic schema used by the public demonstration."""
from __future__ import annotations

import os
import time
from pathlib import Path

import pymysql
from demo_settings import load_ci_settings


def connect_with_retry():
    last_error = None
    for _ in range(30):
        try:
            return pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DATABASE"], autocommit=True)
        except pymysql.MySQLError as error:
            last_error = error
            time.sleep(1)
    raise RuntimeError("local CI MySQL service did not become available") from last_error


def main() -> None:
    load_ci_settings()
    schema = (Path(__file__).parents[2] / "docs" / "schema.sql").read_text(encoding="utf-8")
    with connect_with_retry() as connection:
        with connection.cursor() as cursor:
            for statement in schema.split(";"):
                if statement.strip(): cursor.execute(statement)


if __name__ == "__main__": main()
