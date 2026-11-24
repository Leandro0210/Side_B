"""Comprobar curación estrictamente de presentación, sin alterar el experimento."""
from pathlib import Path
import unittest

import pandas as pd

from side_b_catalog_quality import build_illustration_catalog, prepare, track_assessment
from side_b_dashboard_core import SideBEngine, POLICIES, REPRESENTATIONS
from validar_integral_side_b import run_audit

ROOT = Path(__file__).resolve().parents[1]


class TestCatalogQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SideBEngine(ROOT, review_token="")
        cls.table = prepare(ROOT)

    def test_one_illustration_per_artist_and_source(self):
        self.assertEqual(len(self.table), 72)
        self.assertFalse(self.table.artist_mbid.duplicated().any())
        for r in self.table.itertuples(index=False):
            if r.display_quality != "sin_ejemplo":
                tracks = self.engine.tracks
                self.assertEqual(len(tracks.loc[
                    (tracks.artist_mbid == r.artist_mbid) &
                    (tracks.recording_mbid == r.display_recording_mbid)]), 1)

    def test_known_non_music_not_shown_as_song(self):
        for name in ("Buddy Holly", "Lupe Fiasco", "Necro", "ZUNTATA"):
            row = self.table.loc[self.table.artist_name == name].iloc[0]
            self.assertTrue(row.example_changed, name)
            self.assertEqual(row.original_quality, "no_apta")
            self.assertNotEqual(row.display_quality, "no_apta")
            self.assertNotEqual(row.original_recording_mbid, row.display_recording_mbid)

    def test_no_song_does_not_remove_artist(self):
        item = self.table.loc[self.table.artist_name == "The E Street Band"].iloc[0]
        self.assertEqual(item.display_quality, "sin_ejemplo")
        self.assertEqual(item.display_recording_mbid, "")
        for policy in POLICIES:
            ranked, _, _ = self.engine.recommendations("rock", policy, "with_sampling")
            if item.artist_mbid in ranked.artist_mbid.values:
                self.assertEqual(self.engine.illustration(item.artist_mbid)["display_quality"],"sin_ejemplo")

    def test_no_spurious_replacement(self):
        replaced = self.table.loc[self.table.example_changed]
        self.assertEqual(len(replaced), 5)
        self.assertTrue(replaced.original_quality.eq("no_apta").all())
        unchanged = self.table.loc[~self.table.example_changed]
        self.assertTrue((unchanged.original_recording_mbid == unchanged.display_recording_mbid).all())

    def test_original_model_rankings_are_unchanged(self):
        reference=pd.read_csv(ROOT / "data/robustez_v0_2/robustness_recommendations.csv")
        for representation_label, representation in REPRESENTATIONS.items():
            rep_name = 'solo_etiquetas_artista' if representation == 'artist_only' else 'original_con_muestreo'
            for profile in self.engine.profiles:
                for index, policy in enumerate(POLICIES):
                    ranked, _, _ = self.engine.recommendations(profile, policy, representation)
                    expected = reference.loc[(reference.representation == rep_name) &
                                             (reference.profile == profile) &
                                             (reference.policy.str.startswith('ABCD'[index] + '_'))]
                    self.assertEqual(ranked.artist_mbid.tolist(), expected.artist_mbid.tolist())
                    self.assertEqual(ranked.track_name.tolist(), expected.example_track.tolist())
                    self.assertEqual(ranked.position.tolist(), expected.position.tolist())
                    self.assertTrue({"position", "artist_mbid", "track_name", "recording_mbid",
                                     "ranking_score", "content_similarity"}.issubset(ranked.columns))
        self.assertEqual(len(reference), 476)  # evidencia histórica preservada

    def test_comparison_shows_illustration_with_quality_status(self):
        policies=list(POLICIES)
        _,_,detail,_=self.engine.group_comparison('rock',policies[0],policies[2],"with_sampling",10)
        self.assertIn("Estado de ejemplo", detail.columns)
        self.assertIn("Grabación mostrada", detail.columns)
        row=detail.loc[detail.Artista=="The E Street Band"]
        self.assertFalse(row.empty)
        self.assertTrue(row["Estado de ejemplo"].eq("sin_ejemplo").all())
        self.assertFalse(detail["Grabación mostrada"].str.contains("encore break",case=False).any())

    def test_heuristics_avoid_claim_of_audio_verification(self):
        for candidate in self.table.to_dict("records"):
            self.assertNotIn("audio verificado", candidate["display_reason"].lower().replace("no verificado", ""))
        row=pd.Series({"track_name":"Don Passerby Promo 1", "recording_genres":"speech", "duration_ms":"15000"})
        self.assertEqual(track_assessment(row)[0],"no_apta")
        neutral=pd.Series({"track_name":"Canción normal", "recording_genres":"", "duration_ms":"225000"})
        self.assertNotEqual(track_assessment(neutral)[0],"no_apta")

    def test_gradio_cards_and_explanations_hide_non_song(self):
        from app_gradio import _discover, _explain
        from side_b_dashboard_core import REPRESENTATIONS
        representation_name = "Artista + etiqueta de muestreo"
        cards, note, fig, dropdown = _discover(
            "rock", "Descubrir música menos conocida", representation_name, 10)
        self.assertIn("Sin canción ilustrativa", cards)
        self.assertNotIn("encore break", cards.casefold())
        target = self.table.loc[self.table.artist_name == "The E Street Band"].iloc[0]
        explanation = _explain("rock", "Descubrir música menos conocida",
                               representation_name, 10, target.artist_mbid)
        self.assertIn("sin_ejemplo", explanation)
        self.assertNotIn("[encore break]", explanation)
        self.assertIn("72", str(len(self.table)))

    def test_determinism_and_integral_diagnostic(self):
        a=prepare(ROOT)
        pd.testing.assert_frame_equal(self.table,a)
        report=run_audit(ROOT)
        checks={x['id']:x for x in report['checks']}
        self.assertTrue(report['technical_checks_pass'], checks)
        self.assertEqual(checks['calidad_grabaciones_ilustrativas']['status'],'PENDIENTE')
        self.assertIn('72 artistas',checks['calidad_grabaciones_ilustrativas']['detail'])
        self.assertIn('1 sin canción',checks['calidad_grabaciones_ilustrativas']['detail'])


if __name__ == '__main__':
    unittest.main()
