import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from side_b_model_v0 import load_catalog, experiment, greedy_cap_ranking, genre_token


class SideBModelTests(unittest.TestCase):
    def make_catalog(self, folder):
        path=Path(folder)/"tracks.csv"
        names=["Música A","Música B","Música C","Música D","Música E","Música F","Música G","Música H","Música I","Música J","Música K","Música L"]
        keys=["low_observed"]*4+["medium_observed"]*4+["high_observed"]*4
        with path.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["recording_mbid","track_name","artist_mbid","artist_name","sampling_genre","artist_genres","artist_listeners","artist_popularity_group","recording_genres"])
            w.writeheader()
            for i in range(12):
                for j in range(2):
                    w.writerow({"recording_mbid":f"r_{i}_{j}","track_name":f"Song {i} {j}","artist_mbid":f"artist{i}","artist_name":names[i],"sampling_genre":"rock","artist_genres":"rock; classic rock", "artist_listeners":10+i*100, "artist_popularity_group":keys[i], "recording_genres": "rock" if j else ""})
        return path

    def test_tokens_preserve_multiword(self):
        self.assertEqual(genre_token("Hip Hop"),"g_hip_hop")

    def test_catalog_unique_artists_and_tracks(self):
        with TemporaryDirectory() as temp:
            catalog,audit=load_catalog(self.make_catalog(temp))
            self.assertEqual(len(catalog),12)
            self.assertEqual(audit['recordings'],24)
            self.assertEqual(audit['artists_by_pop_group']['low_observed'],4)

    def test_both_policies_same_eligible_pool_and_unique_artists(self):
        with TemporaryDirectory() as temp:
            catalog,_=load_catalog(self.make_catalog(temp))
            rec,comp=experiment(catalog,["rock"],10)
            self.assertEqual(len(rec),20)
            self.assertEqual(comp["eligible_artists"].tolist(),[12,12])
            self.assertTrue(all(n==10 for n in comp["recommended_artists"]))
            for _,group in rec.groupby("policy"):
                self.assertEqual(group["artist_mbid"].nunique(),10)

    def test_group_cap_when_feasible(self):
        with TemporaryDirectory() as temp:
            catalog,_=load_catalog(self.make_catalog(temp))
            _,comp=experiment(catalog,["rock"],9)
            row=comp.loc[comp["policy"]=="mitigated_group_cap"].iloc[0]
            self.assertEqual([row.low_top_k,row.medium_top_k,row.high_top_k],[3,3,3])
            self.assertFalse(row.cap_relaxed)

    def test_mitigation_changes_recommendations_when_bias_excludes_low_group(self):
        with TemporaryDirectory() as temp:
            catalog,_=load_catalog(self.make_catalog(temp))
            rec,comp=experiment(catalog,["rock"],6)
            baseline=comp.loc[comp["policy"]=="baseline_popularity_boost"].iloc[0]
            mitigated=comp.loc[comp["policy"]=="mitigated_group_cap"].iloc[0]
            self.assertEqual(baseline.low_top_k,0)
            self.assertEqual(mitigated.low_top_k,2)
            self.assertEqual(mitigated.high_top_k,2)

    def test_missing_artist_popularity_never_becomes_zero(self):
        with TemporaryDirectory() as temp:
            path=self.make_catalog(temp)
            with path.open(encoding="utf-8", newline="") as stream:
                rows=list(csv.DictReader(stream))
            for row in rows:
                if row['artist_mbid']=="artist0":
                    row['artist_listeners']=""
            with path.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
            catalog,audit=load_catalog(path)
            self.assertEqual(len(catalog),11)
            self.assertEqual(audit['artists_excluded_no_comparable_popularity'],1)

    def test_duplicate_recording_fails(self):
        with TemporaryDirectory() as temp:
            path=self.make_catalog(temp)
            with path.open(encoding="utf-8", newline="") as stream:
                rows=list(csv.DictReader(stream))
            rows[1]['recording_mbid']=rows[0]['recording_mbid']
            with path.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
            with self.assertRaises(ValueError):load_catalog(path)


if __name__ == '__main__': unittest.main()
