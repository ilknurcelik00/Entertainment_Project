"""Extract a seven-day, multi-country broadcast schedule from TVMaze."""

import json
import os
from datetime import date, timedelta
from pathlib import Path

import requests


BASE_URL = "https://api.tvmaze.com/schedule"
DEFAULT_COUNTRIES = ("TR", "US", "GB", "KR", "FR")
DEFAULT_DAYS_BACK = 6

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "tvmaze"


def configured_countries():
    raw_value = os.getenv("TVMAZE_COUNTRIES", ",".join(DEFAULT_COUNTRIES))
    countries = tuple(
        country.strip().upper()
        for country in raw_value.split(",")
        if country.strip()
    )
    return countries or DEFAULT_COUNTRIES


def configured_days_back():
    return max(0, int(os.getenv("TVMAZE_DAYS_BACK", DEFAULT_DAYS_BACK)))


def fetch_schedule(country="TR", target_date=None):
    target_date = target_date or date.today().isoformat()
    response = requests.get(
        BASE_URL,
        params={"country": country, "date": target_date},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def enrich_episode(episode, requested_country):
    enriched = dict(episode)
    show = dict(enriched.get("show") or {})
    network = dict(show.get("network") or {})
    web_channel = dict(show.get("webChannel") or {})
    externals = dict(show.get("externals") or {})
    network_country = dict(network.get("country") or {})

    # Apache Hop's JSON Input transform expects every JSONPath to return the
    # same number of values. TVMaze omits these nested objects for web-only or
    # network-only programmes, so keep the shape stable and let Hop read nulls.
    network.setdefault("name", None)
    network_country.setdefault("code", None)
    network["country"] = network_country
    web_channel.setdefault("name", None)
    externals.setdefault("imdb", None)
    externals.setdefault("thetvdb", None)

    show["network"] = network
    show["webChannel"] = web_channel
    show["externals"] = externals
    show.setdefault("language", None)
    show.setdefault("status", None)
    show.setdefault("genres", [])
    enriched["show"] = show

    enriched["source_country"] = requested_country
    enriched["country_code"] = network_country.get("code") or requested_country
    return enriched


def fetch_schedule_window(countries, end_date, days_back):
    episodes_by_id = {}
    start_date = end_date - timedelta(days=days_back)

    current_date = start_date
    while current_date <= end_date:
        target_date = current_date.isoformat()
        for country in countries:
            episodes = fetch_schedule(country=country, target_date=target_date)
            for episode in episodes:
                enriched = enrich_episode(episode, country)
                episode_id = enriched.get("id")
                if episode_id is not None:
                    episodes_by_id[episode_id] = enriched

            print(
                f"TVMaze | {country} | {target_date} - "
                f"{len(episodes)} kayıt"
            )
        current_date += timedelta(days=1)

    return list(episodes_by_id.values())


def save_raw_json(data, target_date):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = RAW_DATA_DIR / f"tvmaze_schedule_{target_date}.json"
    latest_path = RAW_DATA_DIR / "tvmaze_schedule_latest.json"

    for output_path in (dated_path, latest_path):
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    return dated_path, latest_path


def transform_schedule(data):
    clean_data = []
    for episode in data:
        show = episode.get("show") or {}
        network = show.get("network") or {}
        web_channel = show.get("webChannel") or {}
        externals = show.get("externals") or {}
        clean_data.append(
            {
                "show_id": show.get("id"),
                "episode_id": episode.get("id"),
                "show_name": show.get("name"),
                "episode_name": episode.get("name"),
                "season": episode.get("season"),
                "episode_number": episode.get("number"),
                "airdate": episode.get("airdate"),
                "airtime": episode.get("airtime"),
                "runtime": episode.get("runtime"),
                "language": show.get("language"),
                "genres": show.get("genres"),
                "status": show.get("status"),
                "network": network.get("name"),
                "web_channel": web_channel.get("name"),
                "imdb_id": externals.get("imdb"),
                "thetvdb_id": externals.get("thetvdb"),
                "country_code": episode.get("country_code"),
            }
        )
    return clean_data


def main():
    end_date = date.today()
    countries = configured_countries()
    days_back = configured_days_back()

    print("\n=== ÇOK ÜLKELİ TVMAZE YAYIN ÇEKİMİ ===")
    print("Ülkeler:", ", ".join(countries))
    print("Tarih aralığı:", end_date - timedelta(days=days_back), "-", end_date)

    raw_data = fetch_schedule_window(countries, end_date, days_back)
    dated_path, latest_path = save_raw_json(raw_data, end_date.isoformat())

    country_counts = {}
    for row in transform_schedule(raw_data):
        country = row["country_code"] or "UNKNOWN"
        country_counts[country] = country_counts.get(country, 0) + 1

    print("\n=== TVMAZE SONUÇ ===")
    print("Benzersiz bölüm sayısı:", len(raw_data))
    print("Ülke dağılımı:", country_counts)
    print("Dosyalar:", dated_path, latest_path)


if __name__ == "__main__":
    main()
