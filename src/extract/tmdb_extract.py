"""Extract a multi-country movie and TV catalogue from TMDB."""

import json
import os
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

TMDB_TOKEN = os.getenv("TMDB_TOKEN")
BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_COUNTRIES = ("TR", "US", "GB", "KR", "FR")
DEFAULT_PAGE_COUNT = 3

HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "tmdb"


def configured_countries():
    raw_value = os.getenv("TMDB_COUNTRIES", ",".join(DEFAULT_COUNTRIES))
    countries = tuple(
        country.strip().upper()
        for country in raw_value.split(",")
        if country.strip()
    )
    return countries or DEFAULT_COUNTRIES


def configured_page_count():
    return max(1, int(os.getenv("TMDB_PAGES_PER_COUNTRY", DEFAULT_PAGE_COUNT)))


def fetch_tmdb(endpoint, params):
    if not TMDB_TOKEN:
        raise RuntimeError("TMDB_TOKEN .env dosyasında tanımlı değil.")

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_country_page(content_type, country, page=1):
    params = {
        "language": "tr-TR",
        "with_origin_country": country,
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "page": page,
    }
    return fetch_tmdb(f"discover/{content_type}", params)


def fetch_turkish_movies(page=1):
    return fetch_country_page("movie", "TR", page)


def fetch_turkish_tv(page=1):
    return fetch_country_page("tv", "TR", page)


def normalize_result(item, requested_country):
    normalized = dict(item)
    origin_countries = list(normalized.get("origin_country") or [])
    if requested_country not in origin_countries:
        origin_countries.append(requested_country)

    normalized["origin_country"] = origin_countries
    normalized["origin_country_code"] = origin_countries[0]
    normalized["extraction_country"] = requested_country
    return normalized


def fetch_multiple_countries(content_type, countries, page_count):
    unique_results = {}

    for country in countries:
        for page in range(1, page_count + 1):
            data = fetch_country_page(content_type, country, page)
            for item in data.get("results", []):
                normalized = normalize_result(item, country)
                content_id = normalized.get("id")
                if content_id not in unique_results:
                    unique_results[content_id] = normalized
                    continue

                previous = unique_results[content_id]
                previous_countries = list(previous.get("origin_country") or [])
                for origin_country in normalized["origin_country"]:
                    if origin_country not in previous_countries:
                        previous_countries.append(origin_country)
                previous["origin_country"] = previous_countries

            print(
                f"{content_type.upper()} | {country} | sayfa {page} çekildi - "
                f"benzersiz kayıt: {len(unique_results)}"
            )

    return list(unique_results.values())


def save_raw_json(data, content_type, target_date):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = RAW_DATA_DIR / f"tmdb_{content_type}_{target_date}.json"
    latest_path = RAW_DATA_DIR / f"tmdb_{content_type}_latest.json"

    for output_path in (dated_path, latest_path):
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    return dated_path, latest_path


def main():
    target_date = date.today().isoformat()
    countries = configured_countries()
    page_count = configured_page_count()

    print("\n=== ÇOK ÜLKELİ TMDB İÇERİK ÇEKİMİ ===")
    print("Ülkeler:", ", ".join(countries))
    print("Ülke başına sayfa:", page_count)

    movies = fetch_multiple_countries("movie", countries, page_count)
    movie_paths = save_raw_json(movies, "movies", target_date)

    tv_shows = fetch_multiple_countries("tv", countries, page_count)
    tv_paths = save_raw_json(tv_shows, "tv", target_date)

    print("\n=== TMDB SONUÇ ===")
    print("Film kayıt sayısı:", len(movies))
    print("Dizi kayıt sayısı:", len(tv_shows))
    print("Film dosyaları:", *movie_paths)
    print("Dizi dosyaları:", *tv_paths)


if __name__ == "__main__":
    main()
