import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import validacion_humana_side_b as h

class TestHumanEval(unittest.TestCase):
    def test_key_union_and_blinding(self):
        rows = [
            {'representation':'solo_etiquetas_artista','profile':'rock','policy':p,'position':str(i),
             'artist_mbid':aid,'artist_name':aid,'example_track':'Track','group':'low_observed'}
            for p,artists in [('A_pop25_sin_tope',['A','B']),('C_pop05_sin_tope',['B','C'])]
            for i,aid in enumerate(artists,1)]
        key=h.build_key(rows)
        self.assertEqual(len(key),3)
        self.assertEqual(sum(bool(r['A_position']) for r in key),2)
        self.assertEqual(sum(bool(r['C_position']) for r in key),2)
        self.assertFalse({'policy','group','ranking_score'} & set(h.RATING_FIELDS))
    def test_missing_score_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ratings'/'P01.csv'
            h.write_csv(p,h.RATING_FIELDS,[dict.fromkeys(h.RATING_FIELDS,'')])
            self.assertEqual(h.read_csv(p)[0]['relevance_1_5'],'')
    def test_blank_notes_are_allowed_in_real_mode(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            h.write_csv(out/'private'/'evaluation_key.csv',h.KEY_FIELDS,[
                {'profile':'pop','item_id':'SB01','artist_mbid':'x','artist_name':'x',
                 'example_track':'track','popularity_group':'low_observed','A_position':1,'C_position':1}])
            h.write_csv(out/'ratings'/'P01.csv',h.RATING_FIELDS,[
                {'participant_id':'P01','profile':'pop','item_id':'SB01',
                 'relevance_1_5':'4','notes':None}])
            h.analyze(SimpleNamespace(out=str(out),simulated=False))
            self.assertTrue((out/'analysis'/'summary_by_profile.csv').exists())

    def test_real_file_integrity(self):
        path=Path('/mnt/data/SIDE_B_Robustez_v0_2/example_results/robustness_recommendations.csv')
        if not path.exists():self.skipTest('no local sample')
        key=h.build_key(h.read_csv(path))
        self.assertEqual(len({r['profile'] for r in key}),6)
        self.assertEqual(len(key),75)

if __name__=='__main__':unittest.main()
