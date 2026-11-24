"""Pruebas del motor del panel Gradio (sin levantar servidor)."""
import tempfile
from pathlib import Path
import unittest
import pandas as pd

from side_b_dashboard_core import POLICIES, REPRESENTATIONS, SideBEngine, GROUPS

ROOT=Path(__file__).resolve().parents[1]

class TestDashboardEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=SideBEngine(ROOT)

    def test_expected_catalog(self):
        self.assertEqual(len(self.engine.tracks),576)
        self.assertEqual(len(self.engine.catalog),72)
        self.assertEqual(len(self.engine.profiles),6)

    def test_reproduces_saved_robustness_rankings(self):
        reference=pd.read_csv(ROOT/'data'/'robustez_v0_2'/'robustness_by_profile.csv')
        for rep_label,representation in REPRESENTATIONS.items():
            rep_name='solo_etiquetas_artista' if representation=='artist_only' else 'original_con_muestreo'
            for policy_idx,policy in enumerate(POLICIES):
                pol='ABCD'[policy_idx]
                for profile in self.engine.profiles:
                    actual,pool,_=self.engine.recommendations(profile,policy,representation,10)
                    expected=reference.loc[(reference.representation==rep_name)&
                                           (reference.profile==profile)&
                                           (reference.policy.str.startswith(pol+'_'))].iloc[0]
                    self.assertEqual(len(pool),int(expected.eligible_total))
                    self.assertEqual(len(actual),int(expected.recommended_n))
                    for group in GROUPS:
                        self.assertEqual(int((actual.pop_group==group).sum()),int(expected[f'topk_{group}']))
                    self.assertAlmostEqual(float(actual.content_similarity.mean()),
                                           float(expected.mean_similarity_proxy),places=5)

    def test_review_block_and_restore_without_touching_dataset(self):
        before=self.engine.dataset_path.read_bytes()
        with tempfile.TemporaryDirectory() as d:
            engine=SideBEngine(ROOT, review_token="TEST_TOKEN_SIDE_B_0123456789")
            engine.audit_log_path=Path(d)/'audit.csv'
            policy=list(POLICIES)[2]
            rep='artist_only'
            before_recs,_,_=engine.recommendations('rock',policy,rep,10)
            first=str(before_recs.iloc[0].artist_mbid)
            text=engine.review('AUDITOR_T1','rock',policy,rep,first,'Bloquear en demo',
                               'Grabación ilustrativa sin validación de calidad musical',
                               'TEST_TOKEN_SIDE_B_0123456789')
            self.assertIn('registrada',text)
            blocked,_,_=engine.recommendations('rock',policy,rep,10,apply_review_blocks=True)
            self.assertNotIn(first,set(blocked.artist_mbid))
            self.assertEqual(len(before_recs),len(blocked))
            engine.review('AUDITOR_T1','rock',policy,rep,first,'Aprobar',
                          'Revisión documentada y aprobada para esta demostración',
                          'TEST_TOKEN_SIDE_B_0123456789')
            unblocked,_,_=engine.recommendations('rock',policy,rep,10,apply_review_blocks=True)
            self.assertIn(first,set(unblocked.artist_mbid))
            self.assertEqual(len(engine.audit_records()),2)
        self.assertEqual(self.engine.dataset_path.read_bytes(),before)

    def test_local_human_evaluation_optional(self):
        real = self.engine.evaluation()
        self.assertIsNotNone(real)
        if not real.empty:
            self.assertIn('complete_participants', real.columns)

    def test_comparison_same_eligible_pool(self):
        p=list(POLICIES)
        frame,tot,ranks,note=self.engine.group_comparison('latin',p[0],p[2],'artist_only',10)
        self.assertEqual(len(ranks),18) # Latin only 9 eligible per policy in this representation
        self.assertEqual(int(tot.iloc[0].Elegibles),9)
        self.assertIn('Solo hay 9',note)
        self.assertEqual(set(ranks['Política']),{'A','C'})

if __name__=='__main__':unittest.main()
