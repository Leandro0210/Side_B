"""Pruebas de explicaciones deterministas sin exponer datos personales."""
import unittest
from pathlib import Path
from side_b_dashboard_core import SideBEngine, POLICIES

ROOT=Path(__file__).resolve().parents[1]

class TestExplainPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=SideBEngine(ROOT,review_token="")

    def test_explanation_matches_ranking_score(self):
        for policy in POLICIES:
            ranking,_,_=self.engine.recommendations("rock",policy,"artist_only",10)
            artist=str(ranking.iloc[0].artist_mbid)
            info=self.engine.explain_candidate("rock",policy,"artist_only",artist)
            self.assertAlmostEqual(info["total_score"],float(ranking.iloc[0].ranking_score),places=9)
            self.assertAlmostEqual(info["similarity_contribution"]+info["popularity_contribution"],info["total_score"])
            self.assertIn(info["genre_source"],("artist_fallback","recording"))

    def test_non_ranked_artist_not_explainable(self):
        with self.assertRaises(ValueError):
            self.engine.explain_candidate("rock",list(POLICIES)[0],"artist_only","unknown")

    def test_looks_like_fixed_only_local_privacy_policy(self):
        self.assertNotIn("email",str(self.engine.profiles).lower())
        self.assertFalse(self.engine.audit_log_path.exists())

if __name__ == "__main__": unittest.main()
