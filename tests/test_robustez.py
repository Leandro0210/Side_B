import csv
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluar_robustez_side_b import run_analysis, artist_tags_only

class RobustnessTests(unittest.TestCase):
    def test_genre_tags_keep_multiword(self):
        self.assertIn("g_indie_rock", artist_tags_only("indie rock; rock; indie rock"))
        self.assertEqual(artist_tags_only("indie rock; rock; indie rock"), "g_indie_rock g_rock")
    def test_dataset_not_modified(self):
        rows=[]
        for idx,(g,pop,tag) in enumerate([("rock","low_observed","rock"),("rock","medium_observed","pop"),("rock","high_observed","rock"),("pop","low_observed","pop"),("pop","medium_observed","pop"),("pop","high_observed","rock")]):
            rows.append(dict(recording_mbid=f"r{idx}",track_name=f"T{idx}",artist_mbid=f"a{idx}",artist_name=f"A{idx}",sampling_genre=g,artist_genres=tag,artist_listeners=str((idx+1)*50),artist_popularity_group=pop))
        with tempfile.TemporaryDirectory() as temp:
            csv_path=Path(temp)/"catalog.csv"
            import pandas as pd
            pd.DataFrame(rows).to_csv(csv_path,index=False)
            before=csv_path.read_bytes()
            d,r,s=run_analysis(csv_path,Path(temp)/"report",k=2)
            self.assertEqual(before,csv_path.read_bytes())
            self.assertTrue(len(d)>0 and len(r)>0 and len(s)>0)
            self.assertTrue((Path(temp)/"report/robustness_manifest.json").exists())
            self.assertTrue((d.eligible_total >= d.recommended_n).all())
    def test_small_k_rejected(self):
        with self.assertRaises(ValueError):
            run_analysis(Path("does_not_matter"),Path("/tmp"),0)

if __name__=="__main__":unittest.main()
