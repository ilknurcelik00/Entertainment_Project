import json
import os
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

TMDB_TOKEN = os.getenv("TMDB_TOKEN")
BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "tmdb"


def fetch_genres(endpoint):
    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        params={"language": "tr-TR"},
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


def save_json(data, file_name):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / file_name

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return file_path


def main():
    target_date = date.today().isoformat()

    print("\n--- MOVIE GENRES ÇEKİLİYOR ---")

    movie_genres = fetch_genres("genre/movie/list")

    movie_file = save_json(
        movie_genres,
        f"tmdb_movie_genres_{target_date}.json",
    )

    movie_latest_file = save_json(
        movie_genres,
        "tmdb_movie_genres_latest.json",
    )

    print("Movie genre dosyası:", movie_file)
    print("Güncel movie genre dosyası:", movie_latest_file)

    print("\n--- TV GENRES ÇEKİLİYOR ---")

    tv_genres = fetch_genres("genre/tv/list")

    tv_file = save_json(
        tv_genres,
        f"tmdb_tv_genres_{target_date}.json",
    )

    tv_latest_file = save_json(
        tv_genres,
        "tmdb_tv_genres_latest.json",
    )

    print("TV genre dosyası:", tv_file)
    print("Güncel TV genre dosyası:", tv_latest_file)


if __name__ == "__main__":
    main()
