import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_TOKEN = os.getenv("TMDB_TOKEN")
BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json"
}


def fetch_tmdb(endpoint, params):
    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def fetch_turkish_movies(page=1):
    params = {
        "language": "tr-TR",
        "with_origin_country": "TR",
        "sort_by": "popularity.desc",
        "page": page
    }

    return fetch_tmdb("discover/movie", params)


def fetch_turkish_tv(page=1):
    params = {
        "language": "tr-TR",
        "with_origin_country": "TR",
        "sort_by": "popularity.desc",
        "page": page
    }

    return fetch_tmdb("discover/tv", params)


def fetch_multiple_pages(fetch_function, page_count=5):
    all_results = []

    for page in range(1, page_count + 1):
        data = fetch_function(page)

        all_results.extend(data["results"])

        print(
            f"Sayfa {page} çekildi - "
            f"Toplam kayıt: {len(all_results)}"
        )

    return all_results


def main():
    print("\n--- TÜRKİYE MENŞELİ FİLMLER ÇEKİLİYOR ---")

    movies = fetch_multiple_pages(
        fetch_turkish_movies,
        page_count=5
    )

    print("\n--- TÜRKİYE MENŞELİ DİZİLER ÇEKİLİYOR ---")

    tv_shows = fetch_multiple_pages(
        fetch_turkish_tv,
        page_count=5
    )

    print("\n--- SONUÇ ---")
    print("Film kayıt sayısı:", len(movies))
    print("Dizi kayıt sayısı:", len(tv_shows))


if __name__ == "__main__":
    main()