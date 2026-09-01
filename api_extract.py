import pandas as pd
import requests
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

url = "https://api.tvmaze.com/schedule"

params = {
    "country": "TR",
    "date": "2026-08-28"
}

response = requests.get(url, params=params)

print("Status Code:", response.status_code)

data = response.json()

print("Kayıt sayısı:", len(data))

print(json.dumps(data, indent=4, ensure_ascii=False))

clean_data = []

for episode in data:
    show = episode["show"]

    network = show.get("network")
    web_channel = show.get("webChannel")
    externals = show.get("externals", {})

    row = {
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
        "network": network.get("name") if network else None,
        "web_channel": web_channel.get("name") if web_channel else None,
        "imdb_id": externals.get("imdb"),
        "thetvdb_id": externals.get("thetvdb")
    }

    clean_data.append(row)

print(clean_data)
df = pd.DataFrame(clean_data)

print("\nTemiz tablo:")
print(df)