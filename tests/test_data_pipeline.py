import random
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "extract"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "db"))

import faker_ratings_generate
import tmdb_extract
import tvmaze_extract
from apply_migrations import split_oracle_script


class TmdbExtractTests(unittest.TestCase):
    def test_country_normalization_adds_requested_country(self):
        item = {"id": 1, "origin_country": ["US"]}
        result = tmdb_extract.normalize_result(item, "GB")
        self.assertEqual(result["origin_country_code"], "US")
        self.assertEqual(result["origin_country"], ["US", "GB"])
        self.assertEqual(result["extraction_country"], "GB")

    @patch("tmdb_extract.fetch_country_page")
    def test_multi_country_results_are_deduplicated(self, fetch_page):
        fetch_page.side_effect = [
            {"results": [{"id": 7, "origin_country": ["TR"]}]},
            {"results": [{"id": 7, "origin_country": ["US"]}]},
        ]
        rows = tmdb_extract.fetch_multiple_countries("tv", ("TR", "US"), 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]["origin_country"]), {"TR", "US"})


class TvMazeExtractTests(unittest.TestCase):
    def test_web_only_episode_has_stable_nested_shape(self):
        episode = {
            "id": 1,
            "show": {
                "id": 2,
                "network": None,
                "webChannel": {"name": "Stream"},
                "externals": None,
            },
        }
        result = tvmaze_extract.enrich_episode(episode, "GB")
        self.assertIsNone(result["show"]["network"]["name"])
        self.assertEqual(result["show"]["webChannel"]["name"], "Stream")
        self.assertIn("imdb", result["show"]["externals"])
        self.assertEqual(result["country_code"], "GB")


class FakerRatingTests(unittest.TestCase):
    def test_generated_ratings_are_reproducible_and_bounded(self):
        catalogue = [
            {
                "source": "TMDB",
                "source_content_id": 10,
                "content_type": "MOVIE",
                "origin_country_code": "TR",
                "popularity": 5,
                "vote_average": 7.5,
            }
        ]
        first = faker_ratings_generate.generate_ratings(
            catalogue, 25, 5, 123, date(2026, 9, 14)
        )
        second = faker_ratings_generate.generate_ratings(
            catalogue, 25, 5, 123, date(2026, 9, 14)
        )
        self.assertEqual(first, second)
        self.assertTrue(all(1 <= row["rating"] <= 10 for row in first))
        self.assertTrue(all(row["is_synthetic"] == 1 for row in first))


class MigrationParserTests(unittest.TestCase):
    def test_oracle_blocks_are_split_on_slash_lines(self):
        script = "BEGIN\nNULL;\nEND;\n/\nCOMMIT\n/\n"
        self.assertEqual(split_oracle_script(script), ["BEGIN\nNULL;\nEND;", "COMMIT"])


if __name__ == "__main__":
    unittest.main()
