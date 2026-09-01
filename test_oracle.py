import os
import requests
import oracledb
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


today = datetime.now().strftime("%Y-%m-%d")

url = f"https://api.tvmaze.com/schedule?country=TR&date={today}"

print(f"Çekilen tarih: {today}")

response = requests.get(url)
data = response.json()

connection = oracledb.connect(
    user=os.getenv("ORACLE_USER"),
    password=os.getenv("ORACLE_PASSWORD"),
    dsn=os.getenv("ORACLE_DSN")
)

cursor = connection.cursor()


for episode in data:
    show = episode["show"]

    genres = ", ".join(show.get("genres", []))

    network = show.get("network")
    network_name = network.get("name") if network else None

    country = None
    if network and network.get("country"):
        country = network["country"].get("name")

    imdb_id = show.get("externals", {}).get("imdb")

    premiered = show.get("premiered")
    premiered_date = (
        datetime.strptime(premiered, "%Y-%m-%d")
        if premiered
        else None
    )

    airdate = episode.get("airdate")
    airdate_value = (
        datetime.strptime(airdate, "%Y-%m-%d")
        if airdate
        else None
    )

    cursor.execute(
        """
        MERGE INTO TVMAZE_SCHEDULE t

        USING (
            SELECT
                :1 AS EPISODE_ID,
                :2 AS SHOW_ID,
                :3 AS SHOW_NAME,
                :4 AS LANGUAGE,
                :5 AS GENRES,
                :6 AS RUNTIME,
                :7 AS PREMIERED,
                :8 AS STATUS,
                :9 AS COUNTRY,
                :10 AS NETWORK,
                :11 AS IMDB_ID,
                :12 AS EPISODE_NAME,
                :13 AS SEASON,
                :14 AS EPISODE_NUMBER,
                :15 AS AIRDATE
            FROM DUAL
        ) s

        ON (
            t.EPISODE_ID = s.EPISODE_ID
        )

        WHEN NOT MATCHED THEN
            INSERT (
                EPISODE_ID,
                SHOW_ID,
                SHOW_NAME,
                LANGUAGE,
                GENRES,
                RUNTIME,
                PREMIERED,
                STATUS,
                COUNTRY,
                NETWORK,
                IMDB_ID,
                EPISODE_NAME,
                SEASON,
                EPISODE_NUMBER,
                AIRDATE
            )
            VALUES (
                s.EPISODE_ID,
                s.SHOW_ID,
                s.SHOW_NAME,
                s.LANGUAGE,
                s.GENRES,
                s.RUNTIME,
                s.PREMIERED,
                s.STATUS,
                s.COUNTRY,
                s.NETWORK,
                s.IMDB_ID,
                s.EPISODE_NAME,
                s.SEASON,
                s.EPISODE_NUMBER,
                s.AIRDATE
            )
        """,
        (
            episode.get("id"),
            show.get("id"),
            show.get("name"),
            show.get("language"),
            genres,
            show.get("runtime"),
            premiered_date,
            show.get("status"),
            country,
            network_name,
            imdb_id,
            episode.get("name"),
            episode.get("season"),
            episode.get("number"),
            airdate_value,
        ),
    )


connection.commit()

print(f"{len(data)} API kaydı işlendi.")

cursor.close()
connection.close()