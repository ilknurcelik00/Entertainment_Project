"""Bulk upsert the generated Faker rating snapshot into Oracle staging."""

import json
import os
from datetime import datetime
from pathlib import Path

import oracledb
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = (
    PROJECT_ROOT / "data" / "raw" / "faker" / "faker_user_ratings_latest.json"
)
load_dotenv(PROJECT_ROOT / ".env")

MERGE_SQL = """
MERGE INTO STG_USER_RATING target
USING (
  SELECT
    :rating_id AS rating_id,
    :source AS source,
    :source_content_id AS source_content_id,
    :content_type AS content_type,
    :user_id AS user_id,
    :country_code AS country_code,
    :rating AS rating,
    :rated_at AS rated_at,
    :is_synthetic AS is_synthetic
  FROM dual
) source
ON (target.rating_id = source.rating_id)
WHEN MATCHED THEN UPDATE SET
  target.source = source.source,
  target.source_content_id = source.source_content_id,
  target.content_type = source.content_type,
  target.user_id = source.user_id,
  target.country_code = source.country_code,
  target.rating = source.rating,
  target.rated_at = source.rated_at,
  target.is_synthetic = source.is_synthetic,
  target.load_date = SYSDATE
WHEN NOT MATCHED THEN INSERT (
  rating_id, source, source_content_id, content_type, user_id,
  country_code, rating, rated_at, is_synthetic, load_date
) VALUES (
  source.rating_id, source.source, source.source_content_id,
  source.content_type, source.user_id, source.country_code,
  source.rating, source.rated_at, source.is_synthetic, SYSDATE
)
"""


def load_rows():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Faker reyting dosyası bulunamadı. Önce günlük veri çekimini çalıştırın: "
            f"{INPUT_PATH}"
        )

    raw_rows = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    if not raw_rows:
        raise RuntimeError("Faker reyting dosyası boş olamaz.")

    return [
        {
            "rating_id": row["rating_id"],
            "source": row["source"],
            "source_content_id": row["source_content_id"],
            "content_type": row["content_type"],
            "user_id": row["user_id"],
            "country_code": row.get("country_code"),
            "rating": row["rating"],
            "rated_at": datetime.strptime(row["rated_at"], "%Y-%m-%d %H:%M:%S"),
            "is_synthetic": row["is_synthetic"],
        }
        for row in raw_rows
    ]


def main():
    rows = load_rows()
    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN"),
    )
    cursor = connection.cursor()

    try:
        cursor.executemany(MERGE_SQL, rows)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    print(f"Oracle STG_USER_RATING toplu yükleme tamamlandı: {len(rows)} kayıt")


if __name__ == "__main__":
    main()
