"""Control de calidad de GRABACIONES ILUSTRATIVAS para SIDE B.

El ranking experimental recomienda ARTISTAS y conserva intactas sus evidencias.
La canción mostrada es una muestra opcional del mismo artista, sin promesa de
correspondencia de género ni validación por escucha. Esta capa no modifica el
CSV original, las métricas A/B/C/D ni los formularios de evaluación existentes.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import unicodedata

import pandas as pd

from side_b_model_v0 import load_catalog

ROOT = Path(__file__).resolve().parent

# Señales fuertes, utilizadas únicamente para seleccionar la grabación a mostrar.
# No son una clasificación automática definitiva de contenido de audio.
NON_SONG = re.compile(
    r"\b(?:interview|interlude|skit|intro|outro|trailer|promo|applause|"
    r"encore\s+(?:break|applause)|soundcheck|radio\s+spot|drum\s+solo)\b|"
    r"\bbgm\s*\d+\b|\bboss\s+scene\b|^bonus$",
    flags=re.IGNORECASE,
)
VERSION_CUE = re.compile(r"\b(?:remix|mix|live|version|demo|take|edit|alternate|overdub)\b|\(#\d+\)", re.I)
SPEECH_TAG = re.compile(r"(?:^|;)\s*(?:speech|spoken\s+word|interview|spoken)\s*(?:;|$)", re.I)


def _clean_text(value: str) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _genre_tokens(value: str) -> set[str]:
    return {g.casefold().strip() for g in str(value or "").split(";") if g.strip()}


def track_assessment(row: pd.Series) -> tuple[str, str, int]:
    """Devuelve (estado, observación, puntuación de selección ilustrativa).

    Estado: 'no_apta' para señales fuertes; 'revisar' para incertidumbre;
    'candidata' si no hay señales detectadas. No certifica que sea una canción.
    """
    title = _clean_text(row.get("track_name", ""))
    genre = str(row.get("recording_genres", ""))
    flags = str(row.get("quality_flags", ""))
    duration_raw = str(row.get("duration_ms", "")).strip()
    duration = float(duration_raw) if duration_raw and duration_raw.isdigit() else None

    if not title:
        return "no_apta", "Título ausente", -100
    if SPEECH_TAG.search(genre):
        return "no_apta", "Etiquetas de grabación indican voz hablada; no usar como canción", -100
    if NON_SONG.search(title):
        return "no_apta", "Título indica segmento, introducción, anuncio o entrevista", -100
    if duration is not None and duration < 30_000:
        return "no_apta", "Duración inferior a 30 segundos; requiere revisión", -100

    remarks = []
    score = 10
    if duration is None:
        remarks.append("Duración desconocida")
        score -= 3
    elif duration < 90_000:
        remarks.append("Duración inferior a 90 segundos")
        score -= 4
    elif duration > 600_000:
        remarks.append("Duración superior a 10 minutos")
        score -= 4
    else:
        score += 3
    if VERSION_CUE.search(title) or VERSION_CUE.search(str(row.get("recording_disambiguation", ""))):
        remarks.append("Versión o grabación especial")
        score -= 3
    if "version_review" in flags:
        remarks.append("Versión marcada para revisar en el dataset")
        score -= 2

    # Si MusicBrainz sí aporta etiquetas de grabación, detectamos discrepancia
    # con la CATEGORÍA DE MUESTREO, no con un supuesto gusto individual.
    record_tags = _genre_tokens(genre)
    sample_genre = str(row.get("sampling_genre", "")).casefold().strip()
    if record_tags:
        if sample_genre and any(sample_genre in g.split() or g == sample_genre for g in record_tags):
            score += 2
        elif sample_genre:
            score -= 4
            remarks.append("Las etiquetas de esta grabación no coinciden exactamente con el género de muestreo")
    else:
        remarks.append("Sin etiquetas específicas de la grabación")

    # Solo nos preocupa si la explicación necesita revisión; nunca 'apta verificada'.
    status = "revisar" if remarks else "candidata"
    note = "; ".join(remarks) if remarks else "Sin alertas automáticas; audio no verificado"
    return status, note, score


def build_illustration_catalog(tracks: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    """Una propuesta por artista, sin cambiar ninguna recomendación científica."""
    rows = []
    groups = {name: frame for name, frame in tracks.groupby("artist_mbid", sort=False)}
    for original in catalog.itertuples(index=False):
        group = groups.get(original.artist_mbid)
        if group is None or group.empty:
            raise ValueError("Artista sin grabaciones en el dataset")
        candidates = []
        for _, t in group.iterrows():
            status, note, score = track_assessment(t)
            if status != "no_apta":
                candidates.append((score, str(t["recording_mbid"]), t, status, note))
        candidates.sort(key=lambda x: (-x[0], x[1]))
        original_row = group.loc[group["recording_mbid"] == original.recording_mbid].iloc[0]
        original_status, original_note, original_score = track_assessment(original_row)
        # Cambios mínimos: se conserva el ejemplo ORIGINAL salvo señal fuerte
        # de segmento no musical. De otro modo se cambiarían muchas canciones
        # asociadas a los 28 ítems de formularios históricos.
        if original_status != "no_apta":
            selected = (original_score, str(original.recording_mbid), original_row,
                        original_status, original_note)
        else:
            selected = candidates[0] if candidates else None
        if selected is None:
            presentation = "Sin grabación ilustrativa apta en la muestra"
            new_mbid = ""
            status = "sin_ejemplo"
            note = "Todas las grabaciones disponibles requieren revisión; no inventamos una canción"
        else:
            _, new_mbid, row, status, note = selected
            presentation = str(row["track_name"])
        rows.append({
            "artist_mbid": str(original.artist_mbid),
            "artist_name": str(original.artist_name),
            "sampling_genre": str(original.sampling_genre),
            "original_recording_mbid": str(original.recording_mbid),
            "original_example": str(original.track_name),
            "original_quality": original_status,
            "original_reason": original_note,
            "display_recording_mbid": new_mbid,
            "display_example": presentation,
            "display_quality": status,
            "display_reason": note,
            "example_changed": bool(new_mbid != str(original.recording_mbid)),
            "sampled_recordings": int(len(group)),
        })
    result = pd.DataFrame(rows)
    if result.artist_mbid.duplicated().any():
        raise ValueError("Error interno: artista duplicado en catálogo ilustrativo")
    return result.sort_values(["artist_name", "artist_mbid"], kind="mergesort").reset_index(drop=True)


def prepare(root: Path = ROOT) -> pd.DataFrame:
    root = Path(root)
    tracks = pd.read_csv(root / "data/dataset_v1/side_b_dataset.csv", dtype=str, keep_default_na=False)
    catalog, _ = load_catalog(root / "data/dataset_v1/side_b_dataset.csv")
    return build_illustration_catalog(tracks, catalog)


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisión trazable de canciones ilustrativas sin alterar rankings")
    parser.add_argument("--out", type=Path, help="Archivo CSV de propuestas, optativo")
    args = parser.parse_args()
    table = prepare()
    counts = table.display_quality.value_counts().to_dict()
    print(f"Artistas: {len(table)}; ejemplos reemplazados/no disponibles: {int(table.example_changed.sum())}")
    print("Estados:", counts)
    print("Sin ejemplo: ", ", ".join(table.loc[table.display_quality=="sin_ejemplo", "artist_name"]))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.out, index=False, encoding="utf-8-sig")
        print("Reporte:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
