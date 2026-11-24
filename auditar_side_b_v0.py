"""SIDE B: experimento de ablación reproducible a partir del dataset v1.

Requiere el archivo original side_b_model_v0.py en la misma carpeta y las
mismas dependencias del modelo. No realiza llamadas a Internet.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from side_b_model_v0 import load_catalog, genre_token, greedy_cap_ranking

GROUPS = ("low_observed", "medium_observed", "high_observed")
POLICIES = (
    ("A_pop25_sin_tope", 0.25, False),
    ("B_pop25_con_tope", 0.25, True),
    ("C_pop05_sin_tope", 0.05, False),
    ("D_pop05_con_tope", 0.05, True),
)


def analyze(input_csv: Path, output_dir: Path, top_k: int = 10, reference_csv: Path | None = None) -> dict:
    catalog, catalog_audit = load_catalog(input_csv)
    profiles = sorted(catalog["sampling_genre"].dropna().unique())
    vectorizer = TfidfVectorizer(analyzer=str.split, lowercase=False, norm="l2")
    artist_vectors = vectorizer.fit_transform(catalog["tag_text"].tolist())
    metrics, selections = [], []
    for profile in profiles:
        query = vectorizer.transform([genre_token(profile)])
        pool = catalog.copy()
        pool["content_similarity"] = np.round(cosine_similarity(query, artist_vectors)[0], 12)
        pool = pool.loc[pool["content_similarity"] > 0].copy()
        if pool.empty:
            continue
        eligible = {g: int((pool.pop_group == g).sum()) for g in GROUPS}
        for policy, pop_weight, cap in POLICIES:
            pool["mitigation_score"] = (1-pop_weight)*pool["content_similarity"] + pop_weight*pool["pop_percentile"]
            if cap:
                selected, relaxed = greedy_cap_ranking(pool, top_k)
            else:
                selected = pool.sort_values(
                    ["mitigation_score", "content_similarity", "artist_mbid"],
                    ascending=[False, False, True], kind="mergesort").head(top_k)
                relaxed = False
            selected = selected.reset_index(drop=True)
            discount_total = sum(1 / math.log2(i+2) for i in range(len(selected)))
            row = {
                "profile":profile, "policy":policy, "eligible_total":len(pool),
                **{f"eligible_{g}": eligible[g] for g in GROUPS},
                "mean_content_similarity_proxy":round(float(selected["content_similarity"].mean()), 6),
                "cap_relaxed":bool(relaxed),
                "recommended_n":len(selected),
            }
            for g in GROUPS:
                subset = selected.loc[selected.pop_group==g]
                group_indices = [i for i,x in enumerate(selected.pop_group) if x==g]
                weight = sum(1/math.log2(i+2) for i in group_indices)
                row[f"topk_{g}"] = len(subset)
                row[f"topk_share_{g}"] = len(subset)/len(selected)
                row[f"eligibility_share_{g}"] = eligible[g]/len(pool)
                row[f"exposure_share_{g}"] = weight/discount_total
            metrics.append(row)
            for i, x in enumerate(selected.itertuples(index=False),start=1):
                selections.append({
                    "profile":profile,"policy":policy,"position":i,
                    "artist_mbid":x.artist_mbid,"artist_name":x.artist_name,
                    "popularity_group":x.pop_group,"content_similarity_proxy":round(float(x.content_similarity),6),
                    "score":round(float(x.mitigation_score),6)
                })
    output_dir.mkdir(parents=True,exist_ok=True)
    m = pd.DataFrame(metrics)
    s = pd.DataFrame(selections)
    m.to_csv(output_dir/"ablation_by_profile.csv",index=False,encoding="utf-8-sig")
    s.to_csv(output_dir/"ablation_recommendations.csv",index=False,encoding="utf-8-sig")
    overall=[]
    for pol, subset in s.groupby("policy",sort=False):
        counts=subset["popularity_group"].value_counts().to_dict()
        overall.append({
            "policy":pol,
            "total_positions":len(subset),
            "unique_artists_across_profiles":subset.artist_mbid.nunique(),
            "mean_similarity_proxy":round(float(subset.content_similarity_proxy.mean()),6),
            **{f"positions_{g}":int(counts.get(g,0)) for g in GROUPS}
        })
    pd.DataFrame(overall).to_csv(output_dir/"ablation_overall.csv",index=False,encoding="utf-8-sig")
    ref_verification = None
    if reference_csv:
        reference=pd.read_csv(reference_csv)
        expected={"baseline_popularity_boost":"A_pop25_sin_tope", "mitigated_group_cap":"D_pop05_con_tope"}
        mismatches=[]
        for policy, ablation_policy in expected.items():
            a=reference.loc[reference.policy==policy, ["profile","position","artist_mbid"]].sort_values(["profile","position"]).reset_index(drop=True)
            b=s.loc[s.policy==ablation_policy,["profile","position","artist_mbid"]].sort_values(["profile","position"]).reset_index(drop=True)
            if len(a)!=len(b):
                mismatches.append({"policy":policy,"length_expected":len(a),"length_actual":len(b)})
            else:
                for idx in range(len(a)):
                    if not a.iloc[idx].equals(b.iloc[idx]):
                        mismatches.append({"policy":policy,"expected":a.iloc[idx].to_dict(),"actual":b.iloc[idx].to_dict()})
        ref_verification={"comparison_positions":int(len(reference)),"mismatches":len(mismatches),"mismatch_examples":mismatches[:5]}
    manifest = {
        "purpose":"Ablación de popularidad (5% vs 25%) y tope por grupo (sí/no) por separado",
        "inputs":{"dataset":str(input_csv),"reference":str(reference_csv) if reference_csv else None},
        "catalog_audit":catalog_audit,
        "top_k":top_k,"profiles":list(profiles),"policies":POLICIES,
        "reference_check":ref_verification,
        "limitations":[
            "Perfiles construidos a partir de géneros de muestreo, no oyentes reales",
            "Eligibilidad basada en similitud > 0, no en relevancia confirmada",
            "Los terciles son relativos a una muestra con sesgo de origen",
            "La posición y el tope por grupo no prueban por sí solos equidad normativa",
            "Una canción por artista es solo ilustrativa; el modelo puntúa artistas",
            "La matriz no es una evaluación de plataformas comerciales",
        ],
    }
    (output_dir/"ablation_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",type=Path,default=Path("data/auditoria_v0_1"))
    p.add_argument("--reference",type=Path)
    p.add_argument("--top-k",type=int,default=10)
    a=p.parse_args()
    if not 1<=a.top_k<=50:
        p.error("top-k debe estar entre 1 y 50")
    result=analyze(a.input,a.out,a.top_k,a.reference)
    print(f"Resultados de ablación guardados en: {a.out}")
    print(pd.read_csv(a.out/"ablation_overall.csv").to_string(index=False))
    if result["reference_check"]: print("Coincidencias con experimento original:",result["reference_check"])

if __name__=="__main__":main()
