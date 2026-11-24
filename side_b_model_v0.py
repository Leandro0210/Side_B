"""SIDE B | Primer experimento reproducible de ranking musical.

NO es una validación de preferencias reales ni una prueba de discriminación.
La unidad recomendada y auditada es el ARTISTA (una canción ilustrativa por artista).
Se trabaja localmente sobre un CSV creado por SIDE B Collector v2.2.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

GROUPS = ("low_observed", "medium_observed", "high_observed")
REQUIRED = {
    "recording_mbid", "track_name", "artist_mbid", "artist_name",
    "sampling_genre", "artist_genres", "artist_listeners",
    "artist_popularity_group",
}


def genre_token(value: str) -> str:
    norm = str(value).casefold().strip()
    norm = re.sub(r"[^\w]+", "_", norm, flags=re.UNICODE).strip("_")
    return "g_" + norm if norm else ""


def load_catalog(csv_file: Path) -> tuple[pd.DataFrame, dict]:
    if not csv_file.is_file():
        raise FileNotFoundError(f"No existe el CSV: {csv_file}")
    tracks = pd.read_csv(csv_file, dtype=str, keep_default_na=False)
    missing = REQUIRED.difference(tracks.columns)
    if missing:
        raise ValueError("Faltan columnas requeridas: " + ", ".join(sorted(missing)))
    if tracks.empty:
        raise ValueError("CSV vacío")
    if tracks["recording_mbid"].duplicated().any():
        raise ValueError("Hay recording_mbid duplicados: revisar el dataset antes de modelar")
    if (tracks["artist_mbid"] == "").any():
        raise ValueError("Hay registros sin artist_mbid")

    audit = {
        "recordings": int(len(tracks)),
        "unique_recordings": int(tracks["recording_mbid"].nunique()),
        "artists": int(tracks["artist_mbid"].nunique()),
        "by_sampling_genre": {str(k): int(v) for k,v in sorted(tracks["sampling_genre"].value_counts().items())},
    }
    if "recording_listeners" in tracks:
        audit["missing_recording_listeners"] = int((tracks["recording_listeners"].str.strip() == "").sum())
    if "recording_genres" in tracks:
        audit["missing_recording_genres"] = int((tracks["recording_genres"].str.strip() == "").sum())
    if "genre_source" in tracks:
        audit["genre_source_counts"] = {str(k):int(v) for k,v in tracks["genre_source"].value_counts().items()}

    # Escogemos una grabación ilustrativa por artista sin usar métricas de popularidad
    # de canciones ni seleccionar el título que dé artificialmente mejor resultado.
    tracks = tracks.copy()
    tracks["_has_recording_tags"] = tracks.get("recording_genres", pd.Series("", index=tracks.index)).str.strip().ne("").astype(int)
    tracks["_has_duration"] = tracks.get("duration_ms", pd.Series("", index=tracks.index)).str.strip().ne("").astype(int)
    tracks = tracks.sort_values(
        ["artist_mbid", "_has_recording_tags", "_has_duration", "recording_mbid"],
        ascending=[True,False,False,True], kind="mergesort"
    )
    catalog = tracks.drop_duplicates("artist_mbid", keep="first").copy()
    catalog["listeners_num"] = pd.to_numeric(catalog["artist_listeners"], errors="coerce")
    catalog["pop_group"] = catalog["artist_popularity_group"].str.strip()
    invalid_group = ~catalog["pop_group"].isin(GROUPS)
    invalid_listeners = catalog["listeners_num"].isna() | catalog["listeners_num"].lt(0)
    audit["artists_excluded_no_comparable_popularity"] = int((invalid_group | invalid_listeners).sum())
    # Nunca convertir popularidad desconocida a 0: excluimos del experimento.
    catalog = catalog.loc[~(invalid_group | invalid_listeners)].copy()
    if len(catalog) < 3:
        raise ValueError("Menos de tres artistas con popularidad comparable")
    catalog["listeners_num"] = catalog["listeners_num"].astype(int)
    catalog["pop_percentile"] = catalog["listeners_num"].rank(pct=True, method="average").astype(float)
    audit["artists_in_experiment"] = int(len(catalog))
    audit["artists_by_pop_group"] = {g: int((catalog["pop_group"]==g).sum()) for g in GROUPS}
    if "artist_country" in catalog:
        audit["artist_country_counts"] = {str(k):int(v) for k,v in catalog["artist_country"].fillna("").value_counts().items()}

    def build_tags(r) -> str:
        tags = {genre_token(g) for g in str(r["artist_genres"]).split(";") if g.strip()}
        tags.add(genre_token(r["sampling_genre"]))
        return " ".join(sorted(x for x in tags if x))

    catalog["tag_text"] = catalog.apply(build_tags, axis=1)
    return catalog.reset_index(drop=True), audit


def greedy_cap_ranking(candidates: pd.DataFrame, k: int) -> tuple[pd.DataFrame,bool]:
    """Máximo ceil(K/3) por grupo si hay suficientes candidatos elegibles.

    Si no alcanzan, relaja el límite para completar K; nunca agrega candidatos
    con similitud = 0 solo para forzar cuotas.
    """
    base = candidates.sort_values(
        ["mitigation_score", "content_similarity", "artist_mbid"],
        ascending=[False, False, True], kind="mergesort"
    )
    cap = math.ceil(k / len(GROUPS))
    chosen_ids: list[str] = []
    counts: Counter = Counter()
    for row in base.itertuples(index=False):
        if len(chosen_ids) >= k:
            break
        if counts[row.pop_group] >= cap:
            continue
        chosen_ids.append(row.artist_mbid)
        counts[row.pop_group] += 1
    relaxed = len(chosen_ids) < min(k, len(base))
    if relaxed:
        for row in base.itertuples(index=False):
            if len(chosen_ids) >= k:
                break
            if row.artist_mbid not in chosen_ids:
                chosen_ids.append(row.artist_mbid)
    order = {artist_id: i for i,artist_id in enumerate(chosen_ids)}
    result = base.loc[base["artist_mbid"].isin(chosen_ids)].copy()
    result["_rank"] = result["artist_mbid"].map(order)
    return result.sort_values("_rank").drop(columns="_rank"), relaxed


def experiment(catalog: pd.DataFrame, profiles: list[str], k: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    vectorizer = TfidfVectorizer(analyzer=str.split, lowercase=False, norm="l2")
    artist_vectors = vectorizer.fit_transform(catalog["tag_text"].tolist())
    recommendations: list[dict] = []
    comparisons: list[dict] = []
    for profile in profiles:
        query = genre_token(profile)
        preferences = vectorizer.transform([query])
        content_scores = cosine_similarity(preferences, artist_vectors)[0]
        pool = catalog.copy()
        pool["content_similarity"] = np.round(content_scores,12)
        # Limitamos el estudio a artistas con similitud textual positiva para
        # no recomendar artistas incompatibles para completar cuotas de equidad.
        pool = pool.loc[pool["content_similarity"] > 0].copy()
        if pool.empty:
            continue
        pool["baseline_score"] = 0.75*pool["content_similarity"] + 0.25*pool["pop_percentile"]
        pool["mitigation_score"] = 0.95*pool["content_similarity"] + 0.05*pool["pop_percentile"]
        baseline = pool.sort_values(
            ["baseline_score", "content_similarity", "artist_mbid"],
            ascending=[False,False,True],kind="mergesort"
        ).head(k)
        mitigated, relaxed = greedy_cap_ranking(pool,k)
        for policy, ranked in (("baseline_popularity_boost",baseline), ("mitigated_group_cap",mitigated)):
            n = len(ranked)
            group_weights = {g:0.0 for g in GROUPS}
            for idx, r in enumerate(ranked.itertuples(index=False),start=1):
                group_weights[r.pop_group] += 1/math.log2(idx+1)
                recommendations.append({
                    "profile":profile, "policy":policy, "position":idx,
                    "artist_name":r.artist_name, "artist_mbid":r.artist_mbid,
                    "example_track":r.track_name, "recording_mbid":r.recording_mbid,
                    "sampling_genre":r.sampling_genre,"popularity_group":r.pop_group,
                    "artist_listeners_observed":int(r.listeners_num),
                    "content_similarity_proxy":round(float(r.content_similarity),6),
                    "popularity_percentile":round(float(r.pop_percentile),6),
                    "score":round(float(r.baseline_score if policy=="baseline_popularity_boost" else r.mitigation_score),6),
                    "musicbrainz_url":getattr(r,"musicbrainz_url", "")
                })
            denom = sum(group_weights.values())
            comparisons.append({
                "profile":profile, "policy":policy, "eligible_artists":len(pool),
                "eligible_low":int((pool["pop_group"]=="low_observed").sum()),
                "eligible_medium":int((pool["pop_group"]=="medium_observed").sum()),
                "eligible_high":int((pool["pop_group"]=="high_observed").sum()),
                "recommended_artists":n,
                "low_top_k":int((ranked["pop_group"]=="low_observed").sum()),
                "medium_top_k":int((ranked["pop_group"]=="medium_observed").sum()),
                "high_top_k":int((ranked["pop_group"]=="high_observed").sum()),
                "low_discounted_exposure_share":round(group_weights["low_observed"]/denom,6) if denom else 0,
                "medium_discounted_exposure_share":round(group_weights["medium_observed"]/denom,6) if denom else 0,
                "high_discounted_exposure_share":round(group_weights["high_observed"]/denom,6) if denom else 0,
                "mean_content_similarity_proxy":round(float(ranked["content_similarity"].mean()),6) if n else 0,
                "cap_relaxed":bool(relaxed) if policy=="mitigated_group_cap" else False
            })
    return pd.DataFrame(recommendations), pd.DataFrame(comparisons)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SIDE B: ranking experimental y auditoría de exposición por popularidad observada")
    p.add_argument("--input", type=Path,default=Path("data/dataset_v1/side_b_dataset.csv"))
    p.add_argument("--out", type=Path,default=Path("data/model_v0"))
    p.add_argument("--top-k",type=int, default=10)
    args=p.parse_args(argv)
    if not 1 <= args.top_k <= 50:
        p.error("--top-k debe estar entre 1 y 50")
    catalog, audit = load_catalog(args.input)
    profiles = sorted(catalog["sampling_genre"].dropna().unique().tolist())
    recommendations, comparisons = experiment(catalog, profiles, args.top_k)
    if recommendations.empty:
        raise RuntimeError("Ningún perfil obtuvo candidatos compatibles")
    args.out.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(args.out/"recommendations.csv",index=False,encoding="utf-8-sig")
    comparisons.to_csv(args.out/"comparison_by_profile.csv",index=False,encoding="utf-8-sig")
    audit.update({
        "date_utc":datetime.now(timezone.utc).isoformat(),
        "source_file":str(args.input),
        "profiles":profiles,
        "top_k":args.top_k,
        "method":"TF-IDF sobre etiquetas del artista y género de muestreo, similitud coseno; una grabación ilustrativa por artista",
        "baseline":"0.75*similitud + 0.25*percentil_popularidad",
        "mitigation":"0.95*similitud + 0.05*percentil_popularidad, máximo ceil(K/3) por tercil cuando es posible",
        "exposure_metric":"sum(1/log2(posicion+1)) por grupo, normalizada por exposición total en top K",
        "caveats":[
            "No se han recogido preferencias reales ni juicios de relevancia.",
            "La similitud calculada no es una medida validada de calidad de recomendaciones.",
            "Los terciles de popularidad son relativos al dataset de esta ejecución.",
            "Los géneros del artista no describen necesariamente cada grabación.",
            "Comparar cantidad de recomendaciones no demuestra discriminación ni injusticia por sí solo.",
            "La intervención propuesta es ilustrativa y debe evaluarse ante otras preferencias, umbrales y poblaciones.",
            "No interpretar los resultados como auditoría de plataformas comerciales reales."
        ]
    })
    with (args.out/"experiment_manifest.json").open("w",encoding="utf-8") as f:
        json.dump(audit,f,ensure_ascii=False,indent=2)
    print("SIDE B | Modelo experimental v0")
    print(f"Artistas comparables: {audit['artists_in_experiment']}/{audit['artists']}")
    print(f"Perfiles evaluados: {len(comparisons['profile'].unique())}, Top K: {args.top_k}")
    print(f"Resultados: {args.out.resolve()}")
    print("\nComparación de perfiles y políticas:")
    cols=["profile","policy","eligible_artists","low_top_k","medium_top_k","high_top_k","mean_content_similarity_proxy"]
    print(comparisons[cols].to_string(index=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
