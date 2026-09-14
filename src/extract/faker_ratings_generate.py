"""Generate reproducible, clearly labelled synthetic user ratings."""

import json
import os
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

from faker import Faker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TMDB_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "tmdb"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "faker"

DEFAULT_RATING_COUNT = 10_000
DEFAULT_USER_COUNT = 1_200
DEFAULT_SEED = 20260911
COUNTRY_WEIGHTS = {
    "TR": 35,
    "US": 25,
    "GB": 15,
    "KR": 15,
    "FR": 10,
}


def read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_catalogue():
    catalogue = []
    sources = (
        ("tmdb_movies_latest.json", "MOVIE"),
        ("tmdb_tv_latest.json", "TV"),
    )

    for filename, content_type in sources:
        for item in read_json(TMDB_DATA_DIR / filename):
            catalogue.append(
                {
                    "source": "TMDB",
                    "source_content_id": item["id"],
                    "content_type": content_type,
                    "origin_country_code": item.get("origin_country_code")
                    or (item.get("origin_country") or [None])[0],
                    "popularity": max(float(item.get("popularity") or 0), 0),
                    "vote_average": float(item.get("vote_average") or 0),
                }
            )

    if not catalogue:
        raise RuntimeError("Faker reytingi üretmek için TMDB kataloğu boş olamaz.")
    return catalogue


def build_user_pool(fake, user_count, randomizer):
    country_codes = tuple(COUNTRY_WEIGHTS)
    weights = tuple(COUNTRY_WEIGHTS.values())
    return [
        {
            "user_id": fake.uuid4(),
            "country_code": randomizer.choices(country_codes, weights=weights, k=1)[0],
        }
        for _ in range(user_count)
    ]


def generate_rating(base_score, randomizer):
    center = base_score if base_score > 0 else 6.5
    score = randomizer.gauss(center, 1.35)
    return round(min(10.0, max(1.0, score)), 1)


def generate_ratings(catalogue, rating_count, user_count, seed, target_date):
    Faker.seed(seed)
    fake = Faker()
    randomizer = random.Random(seed)
    users = build_user_pool(fake, user_count, randomizer)

    popularity_weights = [item["popularity"] + 1 for item in catalogue]
    end_datetime = datetime.combine(target_date, time(23, 59, 59))
    start_datetime = end_datetime - timedelta(days=364)
    ratings = []

    for rating_id in range(1, rating_count + 1):
        content = randomizer.choices(catalogue, weights=popularity_weights, k=1)[0]
        user = randomizer.choice(users)
        rated_at = fake.date_time_between(
            start_date=start_datetime,
            end_date=end_datetime,
        )
        ratings.append(
            {
                "rating_id": rating_id,
                "source": content["source"],
                "source_content_id": content["source_content_id"],
                "content_type": content["content_type"],
                "user_id": user["user_id"],
                "country_code": user["country_code"],
                "rating": generate_rating(content["vote_average"], randomizer),
                "rated_at": rated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_synthetic": 1,
            }
        )

    return ratings


def save_ratings(ratings, target_date):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = OUTPUT_DIR / f"faker_user_ratings_{target_date}.json"
    latest_path = OUTPUT_DIR / "faker_user_ratings_latest.json"

    for output_path in (dated_path, latest_path):
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(ratings, file, ensure_ascii=False, indent=2)
    return dated_path, latest_path


def main():
    target_date = date.today()
    rating_count = max(1, int(os.getenv("FAKER_RATING_COUNT", DEFAULT_RATING_COUNT)))
    user_count = max(1, int(os.getenv("FAKER_USER_COUNT", DEFAULT_USER_COUNT)))
    seed = int(os.getenv("FAKER_SEED", DEFAULT_SEED))

    catalogue = load_catalogue()
    ratings = generate_ratings(
        catalogue,
        rating_count=rating_count,
        user_count=user_count,
        seed=seed,
        target_date=target_date,
    )
    dated_path, latest_path = save_ratings(ratings, target_date.isoformat())

    print("\n=== FAKER REYTİNG SONUÇ ===")
    print("İçerik havuzu:", len(catalogue))
    print("Sentetik kullanıcı havuzu:", user_count)
    print("Sentetik reyting sayısı:", len(ratings))
    print("Dosyalar:", dated_path, latest_path)


if __name__ == "__main__":
    main()
