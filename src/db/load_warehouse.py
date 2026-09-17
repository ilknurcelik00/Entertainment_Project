"""Load the entertainment warehouse with set-based Oracle MERGE statements."""

import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv

from load_fact_user_ratings import MERGE_SQL as FACT_USER_RATING_MERGE


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


MERGES = [
    (
        "DIM_CONTENT Movie",
        """
        MERGE INTO DIM_CONTENT target
        USING (
          SELECT 'TMDB' AS source, tmdb_id AS source_content_id,
                 'MOVIE' AS content_type, title, original_title, overview,
                 original_language, release_date, load_date,
                 NVL(origin_country_code, 'TR') AS origin_country_code
          FROM STG_TMDB_MOVIE
        ) source
        ON (target.source = source.source
            AND target.source_content_id = source.source_content_id
            AND target.content_type = source.content_type)
        WHEN MATCHED THEN UPDATE SET
          target.title = source.title,
          target.original_title = source.original_title,
          target.overview = source.overview,
          target.original_language = source.original_language,
          target.release_date = source.release_date,
          target.load_date = source.load_date,
          target.origin_country_code = source.origin_country_code
        WHEN NOT MATCHED THEN INSERT (
          source, source_content_id, content_type, title, original_title,
          overview, original_language, release_date, load_date,
          origin_country_code
        ) VALUES (
          source.source, source.source_content_id, source.content_type,
          source.title, source.original_title, source.overview,
          source.original_language, source.release_date, source.load_date,
          source.origin_country_code
        )
        """,
    ),
    (
        "DIM_CONTENT TV",
        """
        MERGE INTO DIM_CONTENT target
        USING (
          SELECT 'TMDB' AS source, tmdb_id AS source_content_id,
                 'TV' AS content_type, name AS title,
                 original_name AS original_title, overview,
                 original_language, first_air_date AS release_date,
                 load_date, NVL(origin_country_code, 'TR') AS origin_country_code
          FROM STG_TMDB_TV
        ) source
        ON (target.source = source.source
            AND target.source_content_id = source.source_content_id
            AND target.content_type = source.content_type)
        WHEN MATCHED THEN UPDATE SET
          target.title = source.title,
          target.original_title = source.original_title,
          target.overview = source.overview,
          target.original_language = source.original_language,
          target.release_date = source.release_date,
          target.load_date = source.load_date,
          target.origin_country_code = source.origin_country_code
        WHEN NOT MATCHED THEN INSERT (
          source, source_content_id, content_type, title, original_title,
          overview, original_language, release_date, load_date,
          origin_country_code
        ) VALUES (
          source.source, source.source_content_id, source.content_type,
          source.title, source.original_title, source.overview,
          source.original_language, source.release_date, source.load_date,
          source.origin_country_code
        )
        """,
    ),
    (
        "DIM_CHANNEL",
        """
        MERGE INTO DIM_CHANNEL target
        USING (
          SELECT 'TVMAZE' AS source,
                 NVL(network, web_channel) AS channel_name,
                 MAX(country_code) KEEP (
                   DENSE_RANK FIRST ORDER BY load_date DESC
                 ) AS country_code,
                 MAX(load_date) AS load_date
          FROM STG_TVMAZE_SCHEDULE
          WHERE NVL(network, web_channel) IS NOT NULL
          GROUP BY NVL(network, web_channel)
        ) source
        ON (target.source = source.source
            AND target.channel_name = source.channel_name)
        WHEN MATCHED THEN UPDATE SET
          target.country_code = source.country_code,
          target.load_date = source.load_date
        WHEN NOT MATCHED THEN INSERT (
          source, source_channel_id, channel_name, slug, logo_url,
          country_code, load_date
        ) VALUES (
          source.source, NULL, source.channel_name, NULL, NULL,
          source.country_code, source.load_date
        )
        """,
    ),
    (
        "BRIDGE_CONTENT_GENRE",
        """
        MERGE INTO BRIDGE_CONTENT_GENRE target
        USING (
          SELECT DISTINCT content.content_key, genre.genre_key
          FROM (
            SELECT 'MOVIE' AS content_type, movie.tmdb_id AS source_content_id,
                   genre_ids.genre_id
            FROM STG_TMDB_MOVIE movie
            CROSS APPLY JSON_TABLE(
              movie.genre_ids, '$[*]'
              COLUMNS (genre_id NUMBER PATH '$')
            ) genre_ids
            UNION ALL
            SELECT 'TV' AS content_type, television.tmdb_id AS source_content_id,
                   genre_ids.genre_id
            FROM STG_TMDB_TV television
            CROSS APPLY JSON_TABLE(
              television.genre_ids, '$[*]'
              COLUMNS (genre_id NUMBER PATH '$')
            ) genre_ids
          ) staging
          JOIN DIM_CONTENT content
            ON content.source = 'TMDB'
           AND content.content_type = staging.content_type
           AND content.source_content_id = staging.source_content_id
          JOIN DIM_GENRE genre
            ON genre.source = 'TMDB'
           AND genre.source_genre_id = staging.genre_id
        ) source
        ON (target.content_key = source.content_key
            AND target.genre_key = source.genre_key)
        WHEN NOT MATCHED THEN INSERT (content_key, genre_key)
        VALUES (source.content_key, source.genre_key)
        """,
    ),
    (
        "FACT_CONTENT_METRICS",
        """
        MERGE INTO FACT_CONTENT_METRICS target
        USING (
          SELECT content.content_key, calendar.date_key,
                 staging.popularity, staging.vote_average,
                 staging.vote_count, staging.load_date
          FROM (
            SELECT 'MOVIE' AS content_type, tmdb_id AS source_content_id,
                   popularity, vote_average, vote_count, load_date
            FROM STG_TMDB_MOVIE
            UNION ALL
            SELECT 'TV' AS content_type, tmdb_id AS source_content_id,
                   popularity, vote_average, vote_count, load_date
            FROM STG_TMDB_TV
          ) staging
          JOIN DIM_CONTENT content
            ON content.source = 'TMDB'
           AND content.content_type = staging.content_type
           AND content.source_content_id = staging.source_content_id
          JOIN DIM_DATE calendar
            ON calendar.full_date = TRUNC(staging.load_date)
        ) source
        ON (target.content_key = source.content_key
            AND target.date_key = source.date_key)
        WHEN MATCHED THEN UPDATE SET
          target.popularity = source.popularity,
          target.vote_average = source.vote_average,
          target.vote_count = source.vote_count,
          target.load_date = source.load_date
        WHEN NOT MATCHED THEN INSERT (
          content_key, date_key, popularity, vote_average, vote_count, load_date
        ) VALUES (
          source.content_key, source.date_key, source.popularity,
          source.vote_average, source.vote_count, source.load_date
        )
        """,
    ),
    (
        "FACT_BROADCAST",
        """
        MERGE INTO FACT_BROADCAST target
        USING (
          SELECT content.content_key, channel.channel_key,
                 calendar.date_key, 'TVMAZE' AS source,
                 staging.episode_id AS source_episode_id,
                 staging.episode_name, staging.season AS season_number,
                 staging.episode_number, staging.airtime,
                 staging.runtime, staging.load_date
          FROM STG_TVMAZE_SCHEDULE staging
          LEFT JOIN (
            SELECT UPPER(TRIM(title)) AS normalized_title,
                   MIN(content_key) AS content_key
            FROM DIM_CONTENT
            WHERE content_type = 'TV'
            GROUP BY UPPER(TRIM(title))
          ) content
            ON content.normalized_title = UPPER(TRIM(staging.show_name))
          LEFT JOIN DIM_CHANNEL channel
            ON channel.source = 'TVMAZE'
           AND UPPER(TRIM(channel.channel_name)) =
               UPPER(TRIM(NVL(staging.network, staging.web_channel)))
          JOIN DIM_DATE calendar
            ON calendar.full_date = TRUNC(staging.airdate)
        ) source
        ON (target.source = source.source
            AND target.source_episode_id = source.source_episode_id)
        WHEN MATCHED THEN UPDATE SET
          target.content_key = source.content_key,
          target.channel_key = source.channel_key,
          target.date_key = source.date_key,
          target.episode_name = source.episode_name,
          target.season_number = source.season_number,
          target.episode_number = source.episode_number,
          target.airtime = source.airtime,
          target.runtime = source.runtime,
          target.load_date = source.load_date
        WHEN NOT MATCHED THEN INSERT (
          content_key, channel_key, date_key, source, source_episode_id,
          episode_name, season_number, episode_number, airtime, runtime,
          load_date
        ) VALUES (
          source.content_key, source.channel_key, source.date_key,
          source.source, source.source_episode_id, source.episode_name,
          source.season_number, source.episode_number, source.airtime,
          source.runtime, source.load_date
        )
        """,
    ),
    ("FACT_USER_RATING", FACT_USER_RATING_MERGE),
]


def main():
    connection = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN"),
    )
    cursor = connection.cursor()

    try:
        for name, statement in MERGES:
            cursor.execute(statement)
            print(f"{name}: {cursor.rowcount} kayıt işlendi")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    print("Oracle veri ambarı toplu yükleme tamamlandı.")


if __name__ == "__main__":
    main()
