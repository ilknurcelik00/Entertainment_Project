"""Run all daily source extractions in a single, fail-fast process."""

from tmdb_extract import main as extract_tmdb_content
from tmdb_genre_extract import main as extract_tmdb_genres
from tvmaze_extract import main as extract_tvmaze_schedule
from faker_ratings_generate import main as generate_faker_ratings


def main():
    print("\n=== GÜNLÜK VERİ ÇEKME BAŞLADI ===")

    extract_tmdb_content()
    extract_tmdb_genres()
    extract_tvmaze_schedule()
    generate_faker_ratings()

    print("\n=== GÜNLÜK VERİ ÇEKME TAMAMLANDI ===")


if __name__ == "__main__":
    main()
