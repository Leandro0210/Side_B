"""SIDE B: sensibilidad a la etiqueta de muestreo en recomendaciones experimentales.

No evalúa satisfacción humana ni demuestra justicia o discriminación.
No utiliza internet ni modifica el CSV original. Requires sklearn, pandas and numpy.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from side_b_model_v0 import GROUPS, genre_token, greedy_cap_ranking, load_catalog

POLICIES = (
    ("A_pop25_sin_tope", 0.25, False),
    ("B_pop25_con_tope", 0.25, True),
    ("C_pop05_sin_tope", 0.05, False),
    ("D_pop05_con_tope", 0.05, True),
)
MODES = ("original_con_muestreo", "solo_etiquetas_artista")


def artist_tags_only(raw: str) -> str:
    """Do not add sampling_genre; preserve multiword labels as one token."""
    tags = {genre_token(x.strip()) for x in str(raw).split(";") if x.strip()}
    return " ".join(sorted(t for t in tags if t))


def run_analysis(input_csv: Path, out_dir: Path, k: int = 10) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not 1 <= k <= 50:
        raise ValueError("top-k debe estar entre 1 y 50")
    catalog, audit = load_catalog(input_csv)
    profiles = sorted(catalog["sampling_genre"].dropna().unique().tolist())
    text_by_mode = {
        MODES[0]: catalog["tag_text"],
        MODES[1]: catalog["artist_genres"].map(artist_tags_only),
    }
    details, rankings, notes = [], [], []
    for mode in MODES:
        texts = text_by_mode[mode].tolist()
        if not any(t.strip() for t in texts):
            raise ValueError(f"No hay etiquetas de artista para {mode}")
        vec = TfidfVectorizer(analyzer=str.split, lowercase=False, norm="l2")
        vectors = vec.fit_transform(texts)
        for profile in profiles:
            query = genre_token(profile)
            # A profile absent from the vocabulary is not a valid recommendation request here.
            if query not in vec.vocabulary_:
                notes.append({"representation": mode, "profile": profile, "warning": "query_sin_terminos_en_vocabulario"})
                continue
            sims = np.round(cosine_similarity(vec.transform([query]), vectors)[0], 12)
            pool = catalog.copy()
            pool["content_similarity"] = sims
            pool = pool.loc[pool["content_similarity"] > 0].copy()
            if pool.empty:
                notes.append({"representation": mode, "profile": profile, "warning": "sin_candidatos"})
                continue
            eligible = {g: int((pool["pop_group"] == g).sum()) for g in GROUPS}
            for name, w, cap in POLICIES:
                pool["mitigation_score"] = (1-w)*pool["content_similarity"] + w*pool["pop_percentile"]
                if cap:
                    selected, relaxed = greedy_cap_ranking(pool, k)
                else:
                    selected = pool.sort_values(
                        ["mitigation_score", "content_similarity", "artist_mbid"],
                        ascending=[False, False, True], kind="mergesort").head(k)
                    relaxed = False
                selected = selected.reset_index(drop=True)
                dcg = sum(1/math.log2(i+2) for i in range(len(selected)))
                item = {"representation": mode, "profile": profile, "policy": name,
                    "eligible_total": len(pool), "recommended_n": len(selected),
                    "cap_relaxed": bool(relaxed),
                    "mean_similarity_proxy": float(selected["content_similarity"].mean()) if len(selected) else float('nan')}
                for g in GROUPS:
                    n = int((selected["pop_group"] == g).sum())
                    ew = sum(1/math.log2(i+2) for i,x in enumerate(selected["pop_group"]) if x == g)
                    item[f"eligible_{g}"] = eligible[g]
                    item[f"eligible_share_{g}"] = eligible[g] / len(pool)
                    item[f"topk_{g}"] = n
                    item[f"topk_share_{g}"] = n / len(selected) if len(selected) else float('nan')
                    item[f"discounted_exposure_share_{g}"] = ew / dcg if dcg else float('nan')
                    item[f"selection_to_eligibility_ratio_{g}"] = ((n / len(selected)) / (eligible[g] / len(pool))) if eligible[g] and len(selected) else float('nan')
                details.append(item)
                for i, r in enumerate(selected.itertuples(index=False), start=1):
                    rankings.append({"representation": mode, "profile": profile, "policy": name,
                        "position": i, "artist_mbid": r.artist_mbid, "artist_name": r.artist_name,
                        "example_track": r.track_name, "group": r.pop_group,
                        "content_similarity_proxy": float(r.content_similarity),
                        "ranking_score": float(r.mitigation_score)})
    d = pd.DataFrame(details)
    r = pd.DataFrame(rankings)
    summary = []
    for (mode, policy), sub in r.groupby(["representation", "policy"], sort=False):
        counts = sub["group"].value_counts().to_dict()
        eligibility = d.loc[(d.representation == mode) & (d.policy == policy), "eligible_total"]
        summary.append({"representation": mode,"policy": policy,
            "total_positions":len(sub),"profiles_evaluated":int(sub["profile"].nunique()),
            "unique_artists_across_profiles":int(sub["artist_mbid"].nunique()),
            "mean_similarity_proxy":float(sub["content_similarity_proxy"].mean()),
            **{f"positions_{g}":int(counts.get(g,0)) for g in GROUPS}})
    s = pd.DataFrame(summary)
    for f in (d, r, s):
        for col in f.select_dtypes(include=[float]).columns:
            f[col] = f[col].round(6)
    out_dir.mkdir(parents=True, exist_ok=True)
    d.to_csv(out_dir/"robustness_by_profile.csv", index=False, encoding="utf-8-sig")
    r.to_csv(out_dir/"robustness_recommendations.csv", index=False, encoding="utf-8-sig")
    s.to_csv(out_dir/"robustness_overall.csv", index=False, encoding="utf-8-sig")
    # Paired overlap: same policy/profile, rank set under two representations.
    overlaps=[]
    for profile in profiles:
        for name, *_ in POLICIES:
            a=r.loc[(r.representation == MODES[0]) & (r.profile == profile) & (r.policy == name)]
            b=r.loc[(r.representation == MODES[1]) & (r.profile == profile) & (r.policy == name)]
            aa=set(a["artist_mbid"]); bb=set(b["artist_mbid"])
            overlaps.append({"profile":profile,"policy":name,"original_n":len(aa),"without_sampling_n":len(bb),
                "shared_artists":len(aa & bb),"jaccard_overlap":len(aa & bb)/len(aa | bb) if (aa|bb) else float('nan'),
                "same_position_count":sum(x==y for x,y in zip(a.sort_values('position').artist_mbid,b.sort_values('position').artist_mbid))})
    pd.DataFrame(overlaps).to_csv(out_dir/"robustness_overlap.csv",index=False,encoding="utf-8-sig")
    m = {"date_utc":datetime.now(timezone.utc).isoformat(),"source_dataset":str(input_csv),
        "dataset_audit":audit,"top_k":k,"profiles":profiles,"representations":{
            MODES[0]:"artist_genres + sampling_genre (modelo original)",
            MODES[1]:"solo artist_genres; sin agregar sampling_genre"},
        "policies": [{"name":name,"popularity_weight":w,"group_cap":cap} for name,w,cap in POLICIES],
        "warnings":notes,
        "limitations":[
            "La consulta de perfil (rock/pop/etc.) sigue siendo una etiqueta; no es una preferencia verificada de un oyente.",
            "La elegibilidad exige similitud textual > 0, no relevancia demostrada.",
            "La TF-IDF se ajusta por separado en cada representación; las puntuaciones entre representaciones no deben compararse como idéntica escala de relevancia.",
            "La diferencia entre representaciones es sensibilidad metodológica, no prueba de fuga de datos clásica ni de discriminación.",
            "Los terciles son relativos al dataset y no equivalen a condición de artista emergente.",
            "La equidad no implica igual exposición sin tener en cuenta calidad, elegibilidad y objetivos del sistema.",
            "Sin juicios humanos o interacciones, no podemos afirmar satisfacción, precisión ni utilidad real." ]}
    (out_dir/"robustness_manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")
    return d, r, s


def main() -> None:
    parser = argparse.ArgumentParser(description="SIDE B: prueba de robustez sin género de muestreo en el texto del artista")
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--out",type=Path,default=Path("data/robustez_v0_2"))
    parser.add_argument("--top-k",type=int,default=10)
    args=parser.parse_args()
    detail, ranks, overall=run_analysis(args.input,args.out,args.top_k)
    print("SIDE B | Sensibilidad a etiqueta de muestreo")
    print(f"Reportes: {args.out.resolve()}")
    print(overall.to_string(index=False))
    print("\nCandidatos por perfil y representación (modelo A):")
    print(detail.loc[detail.policy == POLICIES[0][0],["representation","profile","eligible_total","recommended_n"]].to_string(index=False))

if __name__=="__main__":
    main()
