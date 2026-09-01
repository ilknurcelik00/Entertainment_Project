import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TMDB_TOKEN")

#url = "https://api.themoviedb.org/3/discover/movie"
url = "https://api.themoviedb.org/3/discover/tv"

headers = {
    "Authorization": f"Bearer {token}",
    "accept": "application/json"
}

params = {
    "language": "tr-TR",
    "with_origin_country": "TR",
    "sort_by": "popularity.desc",
    "page": 1
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=15
)

response.raise_for_status()

data = response.json()

print("Toplam sonuç:", data["total_results"])
print("Toplam sayfa:", data["total_pages"])
print("Bu sayfadaki kayıt:", len(data["results"]))

print("\nİlk 10 dizi:\n")

"""for movie in data["results"][:10]:
    print(
        movie.get("id"),
        "-",
        movie.get("title"),
        "-",
        movie.get("release_date"),
        "- popularity:",
        movie.get("popularity")
    )
"""
for show in data["results"][:10]:
    print(
        show.get("id"),
        "-",
        show.get("name"),
        "-",
        show.get("first_air_date"),
        "- popularity:",
        show.get("popularity")
    )