"""Bulk upsert TMDB and TVMaze JSON extracts into Oracle staging tables."""

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path

import oracledb
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
load_dotenv(PROJECT_ROOT / ".env")


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Ham veri dosyası bulunamadı: {path}")
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not rows:
        raise RuntimeError(f"Ham veri dosyası boş: {path}")
    return rows


def parse_date(value):
    return date.fromisoformat(value) if value else None


def compact_json(value):
    return json.dumps(value or [], ensure_ascii=False, separators=(",", ":"))


def movie_rows():
    rows = read_json(RAW_DIR / "tmdb" / "tmdb_movies_latest.json")
    load_date = datetime.now()
    return [
        {
            "tmdb_id": row["id"],
            "title": row.get("title"),
            "original_title": row.get("original_title"),
            "overview": row.get("overview"),
            "release_date": parse_date(row.get("release_date")),
            "original_language": row.get("original_language"),
            "popularity": row.get("popularity"),
            "vote_average": row.get("vote_average"),
            "vote_count": row.get("vote_count"),
            "adult": str(bool(row.get("adult"))).lower(),
            "poster_path": row.get("poster_path"),
            "backdrop_path": row.get("backdrop_path"),
            "genre_ids": compact_json(row.get("genre_ids")),
            "load_date": load_date,
            "origin_country_code": row.get("origin_country_code"),
        }
        for row in rows
    ]


def tv_rows():
    rows = read_json(RAW_DIR / "tmdb" / "tmdb_tv_latest.json")
    load_date = datetime.now()
    return [
        {
            "tmdb_id": row["id"],
            "name": row.get("name"),
            "original_name": row.get("original_name"),
            "overview": row.get("overview"),
            "first_air_date": parse_date(row.get("first_air_date")),
            "original_language": row.get("original_language"),
            "origin_country": compact_json(row.get("origin_country")),
            "popularity": row.get("popularity"),
            "vote_average": row.get("vote_average"),
            "vote_count": row.get("vote_count"),
            "poster_path": row.get("poster_path"),
            "backdrop_path": row.get("backdrop_path"),
            "genre_ids": compact_json(row.get("genre_ids")),
            "load_date": load_date,
            "origin_country_code": row.get("origin_country_code"),
        }
        for row in rows
    ]


def tvmaze_rows():
    rows = read_json(RAW_DIR / "tvmaze" / "tvmaze_schedule_latest.json")
    load_date = datetime.now()
    result = []
    for row in rows:
        show = row.get("show") or {}
        network = show.get("network") or {}
        web_channel = show.get("webChannel") or {}
        externals = show.get("externals") or {}
        result.append(
            {
                "show_id": show.get("id"),
                "episode_id": row["id"],
                "show_name": show.get("name"),
                "episode_name": row.get("name"),
                "season": row.get("season"),
                "episode_number": row.get("number"),
                "airdate": parse_date(row.get("airdate")),
                "airtime": row.get("airtime"),
                "runtime": row.get("runtime"),
                "language": show.get("language"),
                "genres": compact_json(show.get("genres")),
                "status": show.get("status"),
                "network": network.get("name"),
                "web_channel": web_channel.get("name"),
                "imdb_id": externals.get("imdb"),
                "thetvdb_id": externals.get("thetvdb"),
                "load_date": load_date,
                "country_code": row.get("country_code"),
            }
        )
    return result


SOURCES = {
    "movies": (
        movie_rows,
        "STG_TMDB_MOVIE",
        "tmdb_id",
        [
            "title", "original_title", "overview", "release_date",
            "original_language", "popularity", "vote_average", "vote_count",
            "adult", "poster_path", "backdrop_path", "genre_ids",
            "load_date", "origin_country_code",
        ],
    ),
    "tv": (
        tv_rows,
        "STG_TMDB_TV",
        "tmdb_id",
        [
            "name", "original_name", "overview", "first_air_date",
            "original_language", "origin_country", "popularity",
            "vote_average", "vote_count", "poster_path", "backdrop_path",
            "genre_ids", "load_date", "origin_country_code",
        ],
    ),
    "tvmaze": (
        tvmaze_rows,
        "STG_TVMAZE_SCHEDULE",
        "episode_id",
        [
            "show_id", "show_name", "episode_name", "season",
            "episode_number", "airdate", "airtime", "runtime", "language",
            "genres", "status", "network", "web_channel", "imdb_id",
            "thetvdb_id", "load_date", "country_code",
        ],
    ),
}


def merge_sql(table, key, columns):
    all_columns = [key, *columns]
    select_list = ",\n    ".join(f":{name} AS {name}" for name in all_columns)
    updates = ",\n  ".join(f"target.{name} = source.{name}" for name in columns)
    insert_columns = ", ".join(all_columns)
    insert_values = ", ".join(f"source.{name}" for name in all_columns)
    return f"""
MERGE INTO {table} target
USING (SELECT {select_list} FROM dual) source
ON (target.{key} = source.{key})
WHEN MATCHED THEN UPDATE SET
  {updates}
WHEN NOT MATCHED THEN INSERT ({insert_columns})
VALUES ({insert_values})
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=sorted(SOURCES))
    args = parser.parse_args()

    row_builder, table, key, columns = SOURCES[args.source]
    rows = row_builder()
    statement = merge_sql(table, key, columns)

    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN"),
    )
    cursor = connection.cursor()
    try:
        cursor.executemany(statement, rows)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    print(f"{table} toplu yükleme tamamlandı: {len(rows)} kayıt")


if __name__ == "__main__":
    main()
