"""Pruebas SIN red para SIDE B Collector v2.2.
Ejecutar: python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collect_side_b as sb


def uid(n):
    return f"{n:08x}-0000-4000-8000-000000000000"


class FakeClient:
    def __init__(self):
        self.errors = []
        self.cache_hits = 0
        self.cache_saved = 0
        self.failed_popularity_ids = {"artist": set(), "recording": set()}
        self.artist_search_offsets = []
        self.recording_offsets = []

    def mb_get(self, entity, params=None):
        params = params or {}
        if entity == "artist":
            offset = params["offset"]
            self.artist_search_offsets.append(offset)
            if offset >= 200:
                return {"artists": [], "count": 200}
            return {"artists": [
                {"id": uid(1000 + offset + i), "name": f"Artist{i}"}
                for i in range(100)
            ], "count": 200}
        if entity.startswith("artist/"):
            return {"name": "Test Artist", "country": "BO", "type": "Person",
                    "genres": [{"name": "rock"}]}
        if entity == "recording":
            offset = params["offset"]
            self.recording_offsets.append(offset)
            recs = [{"id": uid(5000 + offset + i),
                     "title": f"Song {offset+i}", "length": 190000,
                     "genres": [{"name": "indie rock"}]} for i in range(100)]
            if offset == 0:
                recs[0]["title"] = "[announcements]"
                recs[1]["title"] = "An Album Trailer"
                recs[2]["title"] = "Demo Version (live)"
                recs[3]["title"] = "Missing Duration"
                recs[3]["length"] = None
            return {"recording-count": 950, "recordings": recs}
        raise ValueError(entity)

    def lb_popularity(self, entity, ids):
        field = "artist_mbid" if entity == "artist" else "recording_mbid"
        return {mbid: {field: mbid, "total_listen_count": 20,
                       "total_user_count": 10} for mbid in ids}


class TestCollector(unittest.TestCase):
    def test_pages_spread_and_bounded(self):
        self.assertEqual(sb.spaced_pages(10, 3), [0, 4, 9])
        self.assertEqual(sb.spaced_pages(2, 4), [0, 1])
        self.assertEqual(sb.spaced_pages(1, 2), [0])
        self.assertEqual(sb.spaced_pages(10, 1), [0])

    def test_nonmusical_filters_are_conservative(self):
        for bad in ("[announcements]", "[discography]", "[video excerpts]", "An Album Trailer"):
            self.assertEqual(sb.reject_reason(bad, 190000), "clearly_nonmusical_title")
        for okay in ("Intro", "Outro", "Live Forever", "Demo Version", "[live]"):
            self.assertIsNone(sb.reject_reason(okay, None))
        self.assertEqual(sb.reject_reason("Song", -50), "invalid_negative_duration")
        self.assertIn("missing_duration", sb.quality_flags("Demo", None, ""))
        self.assertIn("version_review", sb.quality_flags("Demo", None, ""))

    def test_artist_search_no_deep_offset_and_reproducible(self):
        c1, c2 = FakeClient(), FakeClient()
        a1, prov1 = sb.select_artists(c1, ["rock"], 6, 42, 2)
        a2, prov2 = sb.select_artists(c2, ["rock"], 6, 42, 2)
        self.assertEqual(a1, a2)
        self.assertEqual(prov1, prov2)
        self.assertEqual(c1.artist_search_offsets, [0, 100])
        self.assertEqual(len(a1), 6)
        self.assertEqual(len(prov1), 200)

    def test_recording_sampling_uses_more_than_first_page(self):
        client = FakeClient()
        selected = {uid(99): {"artist_mbid": uid(99), "sampling_genre": "rock",
                              "artist_search_rank": 10, "artist_search_offset": 0}}
        artists, recs, excluded, unselected = sb.fetch_artist_and_recordings(
            client, selected, 80, 42, recording_pages=2, max_recording_offset=900,
        )
        self.assertEqual(len(artists), 1)
        self.assertIn(0, client.recording_offsets)  # Consulta inicial para el recuento
        self.assertIn(len(set(client.recording_offsets)), (2, 3))
        self.assertTrue(all(0 <= o <= 900 for o in client.recording_offsets))
        self.assertEqual(len(recs), 80)
        self.assertTrue(all(item["reason"] != "duplicate_title_for_artist" for item in excluded))
        self.assertTrue(any(rec["recording_genres"] == "indie rock" for rec in recs))
        self.assertTrue(any(rec["recording_browse_offset"] != 0 for rec in recs))
        self.assertGreater(len(unselected), 0)

    def test_same_title_versions_are_eligible_and_not_false_rejections(self):
        class DuplicateClient(FakeClient):
            def mb_get(self, entity, params=None):
                if entity == "recording":
                    return {"recording-count": 6, "recordings": [
                        {"id": uid(100 + i), "title": "Same song" if i < 4 else
                         ("Another song" if i == 4 else "[interview]"),
                         "length": 180000 + i * 100, "genres": []} for i in range(6)
                    ]}
                return super().mb_get(entity, params)
        client = DuplicateClient()
        artist_id = uid(1)
        selected = {artist_id: {"artist_mbid": artist_id, "sampling_genre": "rock",
                                "artist_search_rank": 5, "artist_search_offset": 0}}
        artists, recordings, excluded, unselected = sb.fetch_artist_and_recordings(
            client, selected, 4, 42, recording_pages=1, max_recording_offset=900,
        )
        self.assertEqual(len(recordings), 4)
        self.assertEqual(len({r["recording_mbid"] for r in recordings}), 4)
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0]["reason"], "clearly_nonmusical_title")
        self.assertEqual(len(unselected), 1)
        self.assertEqual(unselected[0]["reason"], "same_title_not_selected")
        self.assertTrue(all(r["effective_genres"] == "rock" for r in recordings))
        self.assertTrue(all(r["genre_source"] == "artist_fallback" for r in recordings))

    def test_selection_windows_reproducible(self):
        selected = {uid(22): {"artist_mbid": uid(22), "sampling_genre": "rock",
                              "artist_search_rank": 1, "artist_search_offset": 0}}
        c1, c2 = FakeClient(), FakeClient()
        _, recs1, exc1, uns1 = sb.fetch_artist_and_recordings(
            c1, selected, 10, 42, recording_pages=2, max_recording_offset=900,
        )
        _, recs2, exc2, uns2 = sb.fetch_artist_and_recordings(
            c2, selected, 10, 42, recording_pages=2, max_recording_offset=900,
        )
        self.assertEqual(c1.recording_offsets, c2.recording_offsets)
        self.assertEqual([r["recording_mbid"] for r in recs1],
                         [r["recording_mbid"] for r in recs2])

    def test_popularity_missing_is_not_zero(self):
        artist_id = uid(1)
        recording_id = uid(2)
        artists = {artist_id: {"artist_mbid": artist_id, "artist_name": "A",
                               "artist_country": "BO", "artist_type": "Person",
                               "artist_genres": "rock", "sampling_genre": "rock",
                               "artist_search_rank": 5, "artist_search_offset": 0}}
        recordings = [{"recording_mbid": recording_id, "track_name": "Song",
                       "artist_mbid": artist_id, "duration_ms": None,
                       "recording_genres": "", "quality_flags": "missing_duration",
                       "recording_browse_offset": 0}]
        rows, definition = sb.build_dataset(artists, recordings,
                                             ap={artist_id: {"total_user_count": 3,
                                                             "total_listen_count": 10}},
                                             rp={recording_id: {"total_user_count": None,
                                                                "total_listen_count": None}},
                                             failed_ap=set(), failed_rp=set(), date="2026-11-03")
        self.assertIsNone(rows[0]["recording_listeners"])
        self.assertEqual(rows[0]["recording_popularity_status"], "not_available")
        self.assertEqual(rows[0]["artist_popularity_status"], "available")
        self.assertEqual(rows[0]["artist_popularity_group"], "insufficient_data")
        self.assertEqual(definition["method"], "not_classified")

    def test_request_failed_not_conflated_with_no_data(self):
        self.assertEqual(sb.popularity_status("x", {}, {"x"}), "request_failed")
        self.assertEqual(sb.popularity_status("x", {}, set()), "not_returned")
        self.assertEqual(sb.popularity_status("x", {"x": {"total_user_count": None}}, set()), "not_available")
        self.assertEqual(sb.popularity_status("x", {"x": {"total_user_count": 0}}, set()), "available")

    def test_groups_relative_not_emergence(self):
        artists = {uid(i): {"artist_listeners": i * 100} for i in range(1, 10)}
        group_def = sb.popularity_groups(artists)
        self.assertEqual(group_def["method"], "sample_tertiles_of_artist_listeners")
        groups = set(a["artist_popularity_group"] for a in artists.values())
        self.assertEqual(groups, {"low_observed", "medium_observed", "high_observed"})

    def test_quality_report_by_genre(self):
        rows = [{"recording_mbid": uid(i), "artist_mbid": uid(i // 2), "sampling_genre": "pop",
                 "recording_popularity_status": "not_available", "recording_listeners": None,
                 "duration_ms": None, "recording_genres": "", "track_name": "Another song"}
                for i in range(4)]
        artists = {uid(i): {"sampling_genre": "pop", "artist_country": "BO",
                            "artist_popularity_status": "available", "artist_popularity_group": "unknown"}
                   for i in range(2)}
        q = sb.quality_report(rows, artists, [], {}, [])
        self.assertEqual(q["records_by_genre"]["pop"]["missing_recording_popularity_pct"], 100.0)
        self.assertEqual(q["missing_duration_pct"], 100.0)
        self.assertEqual(q["title_initial_a_pct"], 100.0)

    def test_end_to_end_offline_main(self):
        # Patch constructor with fake service, avoid API and writing any real contact value.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "trial"
            with patch.dict(os.environ, {"SIDEB_CONTACT": "contact@example.org"}):
                with patch.object(sb, "APIClient", return_value=FakeClient()):
                    result = sb.main(["--genres", "rock", "--artists-per-genre", "2",
                                      "--recordings-per-artist", "4", "--out", str(path)])
            self.assertEqual(result, 0)
            self.assertTrue((path / "side_b_dataset.csv").is_file())
            self.assertTrue((path / "artists.csv").is_file())
            self.assertTrue((path / "excluded_recordings.csv").is_file())
            self.assertTrue((path / "unselected_recordings.csv").is_file())
            self.assertTrue((path / "quality_report.json").is_file())
            quality = json.loads((path / "quality_report.json").read_text(encoding="utf-8"))
            self.assertEqual(quality["records"], 8)
            self.assertEqual(quality["genre_source_counts"]["recording"], 8)
            self.assertEqual(quality["version"], sb.VERSION)
            self.assertGreater(quality["valid_candidates_not_selected"], 0)
            self.assertNotIn("contact@example.org", (path / "manifest.json").read_text(encoding="utf-8"))


    def test_musicbrainz_cache_reuses_data_after_restart(self):
        class Response:
            status_code = 200
            headers = {}
            def raise_for_status(self):
                pass
            def json(self):
                return {"artists": [{"id": uid(42)}], "count": 1}

        with tempfile.TemporaryDirectory() as d:
            directory = Path(d) / "cache"
            query = {"query": 'tag:"rock"', "offset": 0, "limit": 100}
            first = sb.APIClient("private-contact@example.org", mb_delay=0, cache_dir=directory)
            with patch.object(first.session, "request", return_value=Response()) as first_request:
                actual = first.mb_get("artist", query)
                self.assertEqual(first_request.call_count, 1)
            self.assertEqual(first.cache_saved, 1)
            self.assertEqual(len(list(directory.glob("*.json"))), 1)
            cache_text = next(directory.glob("*.json")).read_text(encoding="utf-8")
            self.assertNotIn("private-contact@example.org", cache_text)

            second = sb.APIClient("another-contact@example.org", mb_delay=0, cache_dir=directory)
            with patch.object(second.session, "request", side_effect=AssertionError("No debe llamar a la red")):
                recovered = second.mb_get("artist", query)
            self.assertEqual(recovered, actual)
            self.assertEqual(second.cache_hits, 1)
            self.assertEqual(second.cache_saved, 0)

    def test_cache_is_isolated_by_parameters_and_not_applied_to_listenbrainz(self):
        class Response:
            status_code = 200
            headers = {}
            def raise_for_status(self):
                pass
            def json(self):
                return {"artists": [{"id": uid(42)}]}
        with tempfile.TemporaryDirectory() as d:
            client = sb.APIClient("public@example.org", mb_delay=0, cache_dir=Path(d))
            with patch.object(client.session, "request", return_value=Response()) as req:
                client.mb_get("artist", {"query": 'tag:"rock"', "offset": 0})
                client.mb_get("artist", {"query": 'tag:"rock"', "offset": 100})
                self.assertEqual(req.call_count, 2)
            self.assertEqual(len(list(Path(d).glob("*.json"))), 2)
            self.assertIsNone(client._cache_path("POST", sb.LB_BASE + "/popularity/artist", {"json": {}}))

    def test_incomplete_collection_does_not_claim_success_and_preserves_cache(self):
        class OneErrorClient(FakeClient):
            def __init__(self, contact=None, cache_dir=None):
                super().__init__()
                self.cache_saved = 1
                self.cache_hits = 0
            def mb_get(self, entity, params=None):
                if entity == "artist":
                    raise RuntimeError("API temporalmente inaccesible")
                return super().mb_get(entity, params)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot"
            with patch.dict(os.environ, {"SIDEB_CONTACT": "contact@example.org"}):
                with patch.object(sb, "APIClient", side_effect=OneErrorClient):
                    result = sb.main(["--genres", "rock", "--out", str(path)])
            self.assertEqual(result, 2)
            self.assertFalse((path / "side_b_dataset.csv").exists())


if __name__ == "__main__":
    unittest.main()
