"""Load synthetic ratings into the warehouse fact table with one Oracle MERGE."""

import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

MERGE_SQL = """
MERGE INTO FACT_USER_RATING target
USING (
  SELECT
    staging.RATING_ID AS SOURCE_RATING_ID,
    content.CONTENT_KEY,
    calendar.DATE_KEY,
    staging.USER_ID,
    staging.COUNTRY_CODE,
    staging.RATING,
    staging.RATED_AT,
    staging.IS_SYNTHETIC,
    staging.LOAD_DATE
  FROM STG_USER_RATING staging
  JOIN DIM_CONTENT content
    ON content.SOURCE = staging.SOURCE
   AND content.SOURCE_CONTENT_ID = staging.SOURCE_CONTENT_ID
   AND content.CONTENT_TYPE = staging.CONTENT_TYPE
  JOIN DIM_DATE calendar
    ON calendar.FULL_DATE = TRUNC(staging.RATED_AT)
) source
ON (target.SOURCE_RATING_ID = source.SOURCE_RATING_ID)
WHEN MATCHED THEN UPDATE SET
  target.CONTENT_KEY = source.CONTENT_KEY,
  target.DATE_KEY = source.DATE_KEY,
  target.USER_ID = source.USER_ID,
  target.COUNTRY_CODE = source.COUNTRY_CODE,
  target.RATING = source.RATING,
  target.RATED_AT = source.RATED_AT,
  target.IS_SYNTHETIC = source.IS_SYNTHETIC,
  target.LOAD_DATE = source.LOAD_DATE
WHEN NOT MATCHED THEN INSERT (
  SOURCE_RATING_ID, CONTENT_KEY, DATE_KEY, USER_ID, COUNTRY_CODE,
  RATING, RATED_AT, IS_SYNTHETIC, LOAD_DATE
) VALUES (
  source.SOURCE_RATING_ID, source.CONTENT_KEY, source.DATE_KEY,
  source.USER_ID, source.COUNTRY_CODE, source.RATING, source.RATED_AT,
  source.IS_SYNTHETIC, source.LOAD_DATE
)
"""


def main():
    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN"),
    )
    cursor = connection.cursor()

    try:
        cursor.execute(MERGE_SQL)
        affected_rows = cursor.rowcount
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    print(f"Oracle FACT_USER_RATING yükleme tamamlandı: {affected_rows} kayıt işlendi")


if __name__ == "__main__":
    main()
