#!/usr/bin/env python3
"""SIDE B Collector v2.2: extracción reproducible, auditable y reanudable.

Fuentes: MusicBrainz (metadatos) y ListenBrainz (popularidad observada).
No usa datos privados ni presupone que datos faltantes equivalen a cero.
La v2.2 conserva respuestas válidas de MusicBrainz para reanudar tras errores temporales.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
from typing import Any

import requests

VERSION = "2.2.0"
MB_BASE = "https://musicbrainz.org/ws/2"
LB_BASE = "https://api.listenbrainz.org/1"
DEFAULT_GENRES = ["rock", "pop", "indie rock", "hip hop", "electronic", "latin"]
PAGE_SIZE = 100

ARTIST_COLUMNS = [
    "artist_mbid", "artist_name", "artist_country", "artist_type", "artist_genres",
    "sampling_genre", "artist_search_rank", "artist_search_offset",
    "artist_listens", "artist_listeners", "artist_popularity_status",
    "artist_popularity_group",
]
DATASET_COLUMNS = [
    "recording_mbid", "track_name", "duration_ms", "recording_genres",
    "effective_genres", "genre_source", "recording_disambiguation", "quality_flags", "recording_browse_offset",
    "artist_mbid", "artist_name", "artist_country", "artist_type",
    "artist_genres", "sampling_genre", "artist_search_rank", "artist_search_offset",
    "recording_listens", "recording_listeners", "recording_popularity_status",
    "artist_listens", "artist_listeners", "artist_popularity_status",
    "artist_popularity_group", "extracted_at", "musicbrainz_url", "data_sources",
]
EXCLUSION_COLUMNS = [
    "artist_mbid", "artist_name", "sampling_genre", "recording_mbid", "track_name",
    "duration_ms", "recording_browse_offset", "reason",
]
UNSELECTED_COLUMNS = EXCLUSION_COLUMNS

# Filtros conservadores: NO excluimos automáticamente intros, directos,
# remixes, demos ni pistas sin duración. Se pueden auditar manualmente.
BRACKET_NONMUSICAL = re.compile(
    r"^\[\s*(?:announcements?|discography|video excerpts?|interviews?|"
    r"podcasts?|advertisements?|commercials?|press conferences?)\s*\]$",
    re.IGNORECASE,
)
EXPLICIT_NONMUSICAL = re.compile(
    r"\b(?:album trailers?|album teasers?|official trailers?|"
    r"behind the scenes|making of the album|press conferences?|"
    r"interview with|interview about|promotional trailers?)\b",
    re.IGNORECASE,
)
REVIEW_VERSION = re.compile(
    r"\b(?:live(?: at| in| version)?|demo|remix|instrumental version|"
    r"alternate take|radio edit)\b",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm_title(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().casefold())


def chunks(seq: list[str], size: int):
    for idx in range(0, len(seq), size):
        yield seq[idx:idx + size]


def spaced_pages(total_pages: int, requested_pages: int) -> list[int]:
    """Ventanas deterministas de la discografía, sin offset > máximo configurado."""
    if total_pages < 1 or requested_pages < 1:
        return []
    if requested_pages >= total_pages:
        return list(range(total_pages))
    if requested_pages == 1:
        return [0]
    return sorted({round(i * (total_pages - 1) / (requested_pages - 1))
                   for i in range(requested_pages)})


def reject_reason(title: str, duration_ms: Any) -> str | None:
    title = (title or "").strip()
    if not title:
        return "empty_title"
    if BRACKET_NONMUSICAL.search(title) or EXPLICIT_NONMUSICAL.search(title):
        return "clearly_nonmusical_title"
    if duration_ms is not None:
        try:
            if float(duration_ms) < 0:
                return "invalid_negative_duration"
        except (TypeError, ValueError):
            return "invalid_duration_value"
    return None


def quality_flags(title: str, duration_ms: Any, recording_genres: str) -> str:
    flags = []
    if duration_ms is None:
        flags.append("missing_duration")
    elif duration_ms < 60000:
        flags.append("short_duration_review")
    elif duration_ms > 1200000:
        flags.append("long_duration_review")
    if not recording_genres:
        flags.append("missing_recording_genres")
    if REVIEW_VERSION.search(title or ""):
        flags.append("version_review")
    return "; ".join(flags)


class APIClient:
    def __init__(self, contact: str, mb_delay: float = 1.5, cache_dir: Path | None = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"SideB-Academic/{VERSION} ({contact})",
            "Accept": "application/json",
        })
        self.mb_delay = mb_delay  # Por debajo de 1 solicitud/segundo de MusicBrainz.
        self.last_mb_request = 0.0
        self.failed_popularity_ids: dict[str, set[str]] = {"artist": set(), "recording": set()}
        self.errors: list[dict] = []
        # Al repetir el mismo comando con el mismo --out, no solicitamos otra vez
        # respuestas exitosas de MusicBrainz. Solo se guardan datos públicos;
        # el contacto del User-Agent no se escribe en el caché.
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hits = 0
        self.cache_saved = 0

    def _cache_path(self, method: str, url: str, kwargs: dict) -> Path | None:
        if self.cache_dir is None or method.upper() != "GET" or not url.startswith(MB_BASE + "/"):
            return None
        # La clave NO incorpora credenciales, User-Agent ni correo de contacto.
        identity = {"method": method.upper(), "url": url, "params": kwargs.get("params") or {}}
        signature = json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return self.cache_dir / f"{hashlib.sha256(signature.encode('utf-8')).hexdigest()}.json"

    def request(self, method: str, url: str, **kwargs) -> Any:
        cache_path = self._cache_path(method, url, kwargs)
        if cache_path is not None and cache_path.exists():
            try:
                with cache_path.open(encoding="utf-8") as fh:
                    cached = json.load(fh)
                if isinstance(cached, (dict, list)):
                    self.cache_hits += 1
                    return cached
            except (OSError, ValueError):
                print("  Aviso: caché ilegible, se consultará de nuevo", file=sys.stderr)

        last_error = None
        for attempt in range(5):
            if url.startswith(MB_BASE + "/"):
                remaining = self.mb_delay - (time.monotonic() - self.last_mb_request)
                if remaining > 0:
                    time.sleep(remaining)
                self.last_mb_request = time.monotonic()
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                if response.status_code in (429, 500, 502, 503, 504):
                    raw_wait = response.headers.get("Retry-After", "")
                    try:
                        wait = min(60.0, max(2.0, float(raw_wait)))
                    except (TypeError, ValueError):
                        wait = min(60.0, 2.0 * (2 ** attempt))
                    print(f"  HTTP {response.status_code}; reintento en {wait:g}s", file=sys.stderr)
                    time.sleep(wait)
                    last_error = f"HTTP {response.status_code}"
                    continue
                response.raise_for_status()
                data = response.json()
                if cache_path is not None and isinstance(data, (dict, list)):
                    # Guardado atómico: un corte de luz no deja archivos parciales válidos.
                    temp_path = cache_path.with_suffix(".writing")
                    with temp_path.open("w", encoding="utf-8") as fh:
                        json.dump(data, fh, ensure_ascii=False)
                    os.replace(temp_path, cache_path)
                    self.cache_saved += 1
                return data
            except (requests.Timeout, requests.ConnectionError, ValueError) as exc:
                last_error = str(exc)
                print(f"  Error temporal: {last_error}", file=sys.stderr)
                time.sleep(min(60.0, 2.0 * (2 ** attempt)))
            except requests.HTTPError as exc:
                raise RuntimeError(f"Error de API {method} {url}: {exc}") from exc
        raise RuntimeError(f"No se pudo completar {method} {url}: {last_error}")

    def mb_get(self, entity: str, params: dict | None = None) -> Any:
        return self.request("GET", f"{MB_BASE}/{entity}", params={"fmt": "json", **(params or {})})

    def lb_popularity(self, entity: str, ids: list[str]) -> dict[str, dict]:
        if not ids:
            return {}
        ids = list(dict.fromkeys(ids))
        field = "artist_mbids" if entity == "artist" else "recording_mbids"
        id_field = "artist_mbid" if entity == "artist" else "recording_mbid"
        output = {}
        for batch in chunks(ids, 20):
            try:
                response = self.request("POST", f"{LB_BASE}/popularity/{entity}", json={field: batch})
                if not isinstance(response, list):
                    raise ValueError("ListenBrainz devolvió respuesta que no es lista")
                for element in response:
                    if isinstance(element, dict) and element.get(id_field) in batch:
                        output[element[id_field]] = element
            except (RuntimeError, ValueError) as exc:
                self.failed_popularity_ids[entity].update(batch)
                self.errors.append({"stage": f"listenbrainz_{entity}", "count": len(batch), "error": str(exc)})
                print(f"  Aviso: error en lote de popularidad {entity}: {exc}", file=sys.stderr)
        return output


def select_artists(client: APIClient, genres: list[str], per_genre: int,
                   seed: int, artist_pages: int) -> tuple[dict[str, dict], list[dict]]:
    rng = random.Random(seed)
    selected: dict[str, dict] = {}
    candidate_provenance: list[dict] = []
    for genre in genres:
        print(f"Buscando artistas: {genre}", flush=True)
        pool: dict[str, dict] = {}
        # Páginas pequeñas consecutivas; evitamos saltos extremos (HTTP 400 en piloto original).
        for page_idx in range(artist_pages):
            offset = page_idx * PAGE_SIZE
            try:
                data = client.mb_get("artist", {
                    "query": f'tag:"{genre}"', "limit": PAGE_SIZE, "offset": offset,
                })
            except RuntimeError as exc:
                if page_idx == 0:
                    raise RuntimeError(f"No se pudo buscar artistas de {genre}: {exc}") from exc
                client.errors.append({"stage": "artist_search", "genre": genre, "offset": offset, "error": str(exc)})
                break
            entries = data.get("artists") or []
            for i, artist in enumerate(entries):
                mbid = artist.get("id")
                if not mbid or mbid in pool:
                    continue
                record = {
                    "artist_mbid": mbid, "sampling_genre": genre,
                    "artist_search_rank": offset + i + 1, "artist_search_offset": offset,
                }
                pool[mbid] = record
                candidate_provenance.append(record)
            if len(entries) < PAGE_SIZE:
                break
            total = int(data.get("count") or 0)
            if total and offset + len(entries) >= total:
                break
        candidates = list(pool.values())
        rng.shuffle(candidates)
        added = 0
        for artist in candidates:
            if artist["artist_mbid"] in selected:
                continue
            selected[artist["artist_mbid"]] = artist
            added += 1
            if added >= per_genre:
                break
        print(f"  Seleccionados: {added}; candidatos consultados: {len(pool)}", flush=True)
        if added < per_genre:
            client.errors.append({"stage": "artist_search", "genre": genre,
                                  "warning": f"Solo {added} artistas únicos de {per_genre} solicitados"})
    return selected, candidate_provenance


def fetch_artist_and_recordings(
    client: APIClient, selected: dict[str, dict], n_per_artist: int,
    seed: int, recording_pages: int, max_recording_offset: int,
) -> tuple[dict[str, dict], list[dict], list[dict], list[dict]]:
    """Extrae candidatos válidos sin descartar versiones por compartir título.

    Mantiene diversidad de títulos AL SELECCIONAR, pero nunca presenta
    alternativas musicales legítimas como descartes de calidad.
    """
    rng = random.Random(seed + 1)
    artists: dict[str, dict] = {}
    recordings: list[dict] = []
    excluded: list[dict] = []
    unselected: list[dict] = []
    for i, (artist_id, meta) in enumerate(selected.items(), start=1):
        print(f"Artista {i}/{len(selected)}: {artist_id}", flush=True)
        try:
            artist = client.mb_get(f"artist/{artist_id}", {"inc": "genres"})
            initial = client.mb_get("recording", {
                "artist": artist_id, "inc": "genres", "limit": PAGE_SIZE, "offset": 0,
            })
        except RuntimeError as exc:
            client.errors.append({"stage": "artist_metadata", "artist_mbid": artist_id, "error": str(exc)})
            print(f"  Artista omitido por error: {exc}", file=sys.stderr)
            continue
        artist_genres = sorted({g.get("name", "").strip() for g in artist.get("genres", []) if g.get("name")})
        artist_row = {
            **meta, "artist_name": artist.get("name") or "",
            "artist_country": artist.get("country") or "",
            "artist_type": artist.get("type") or "",
            "artist_genres": "; ".join(artist_genres),
        }
        artists[artist_id] = artist_row
        count = int(initial.get("recording-count") or len(initial.get("recordings", [])))
        page_count = min(math.ceil(max(count, 1) / PAGE_SIZE), max_recording_offset // PAGE_SIZE + 1)
        # Seleccionamos ventanas de forma reproducible entre las páginas permitidas.
        # La primera página se consulta para conocer el total, pero NO se privilegia al muestrear.
        page_rng = random.Random(f"{seed}:{artist_id}")
        chosen_pages = sorted(page_rng.sample(range(page_count), min(recording_pages, page_count)))
        offsets = [idx * PAGE_SIZE for idx in chosen_pages]
        pages = {}
        for offset in offsets:
            if offset == 0:
                pages[offset] = initial
                continue
            try:
                pages[offset] = client.mb_get("recording", {
                    "artist": artist_id, "inc": "genres", "limit": PAGE_SIZE, "offset": offset,
                })
            except RuntimeError as exc:
                client.errors.append({"stage": "recording_page", "artist_mbid": artist_id,
                                      "offset": offset, "error": str(exc)})
                print(f"  Se omite página {offset}: {exc}", file=sys.stderr)
        candidate_rows = []
        seen_mbids: set[str] = set()
        for offset, payload in sorted(pages.items()):
            for r in payload.get("recordings", []):
                rid, title = r.get("id"), r.get("title") or ""
                common = {
                    "artist_mbid": artist_id, "artist_name": artist_row["artist_name"],
                    "sampling_genre": meta["sampling_genre"],
                    "recording_mbid": rid or "", "track_name": title,
                    "duration_ms": r.get("length"), "recording_browse_offset": offset,
                }
                reason = "missing_recording_mbid" if not rid else reject_reason(title, r.get("length"))
                if not reason and rid in seen_mbids:
                    reason = "duplicate_recording_mbid_in_pages"
                if reason:
                    excluded.append({**common, "reason": reason})
                    continue
                seen_mbids.add(rid)
                genres = sorted({g.get("name", "").strip() for g in r.get("genres", []) if g.get("name")})
                genre_text = "; ".join(genres)
                candidate_rows.append({
                    **common, "recording_genres": genre_text,
                    "effective_genres": genre_text or artist_row["artist_genres"],
                    "genre_source": "recording" if genre_text else
                                    ("artist_fallback" if artist_row["artist_genres"] else "missing"),
                    "recording_disambiguation": r.get("disambiguation") or "",
                    "quality_flags": quality_flags(title, r.get("length"), genre_text),
                })
        rng.shuffle(candidate_rows)
        chosen: list[dict] = []
        selected_ids: set[str] = set()
        selected_titles: set[str] = set()
        # Diversidad por nombre en la salida (sin desechar versiones antes de muestrear).
        for rec in candidate_rows:
            key = norm_title(rec["track_name"])
            if key in selected_titles:
                continue
            chosen.append(rec)
            selected_ids.add(rec["recording_mbid"])
            selected_titles.add(key)
            if len(chosen) >= n_per_artist:
                break
        # Si no existen suficientes títulos distintos, podemos usar otras versiones.
        if len(chosen) < n_per_artist:
            for rec in candidate_rows:
                if rec["recording_mbid"] in selected_ids:
                    continue
                chosen.append(rec)
                selected_ids.add(rec["recording_mbid"])
                if len(chosen) >= n_per_artist:
                    break
        recordings.extend(chosen)
        for rec in candidate_rows:
            if rec["recording_mbid"] in selected_ids:
                continue
            reason = ("same_title_not_selected" if norm_title(rec["track_name"]) in selected_titles
                      else "sampling_limit")
            unselected.append({**rec, "reason": reason})
        if len(chosen) < n_per_artist:
            client.errors.append({"stage": "recording_selection", "artist_mbid": artist_id,
                                  "warning": f"Solo {len(chosen)} de {n_per_artist} grabaciones válidas"})
    # De-duplicación global por identificador. Puede existir una grabación con varios artistas.
    dedup: list[dict] = []
    seen_ids: set[str] = set()
    for recording in recordings:
        rid = recording["recording_mbid"]
        if rid in seen_ids:
            unselected.append({**recording, "reason": "already_selected_recording_mbid"})
            continue
        seen_ids.add(rid)
        dedup.append(recording)
    return artists, dedup, excluded, unselected

def popularity_status(mbid: str, payload: dict[str, dict],
                      failed_ids: set[str]) -> str:
    if mbid in failed_ids:
        return "request_failed"
    if mbid not in payload:
        return "not_returned"
    value = payload[mbid].get("total_user_count")
    return "available" if value is not None else "not_available"


def quantile(sorted_values: list[int], frac: float) -> float:
    if not sorted_values:
        raise ValueError("No hay valores para calcular cuantiles")
    position = (len(sorted_values) - 1) * frac
    lo, hi = math.floor(position), math.ceil(position)
    return (sorted_values[lo] * (hi - position) + sorted_values[hi] * (position - lo)) if lo != hi else sorted_values[lo]


def popularity_groups(artists: dict[str, dict]) -> dict[str, Any]:
    vals = sorted(int(a["artist_listeners"]) for a in artists.values() if a.get("artist_listeners") is not None)
    if len(vals) < 3 or min(vals) == max(vals):
        for a in artists.values():
            a["artist_popularity_group"] = "insufficient_data" if a.get("artist_listeners") is not None else "unknown"
        return {"method": "not_classified", "reason": "Menos de 3 valores o sin variación"}
    low, high = quantile(vals, 1/3), quantile(vals, 2/3)
    for a in artists.values():
        value = a.get("artist_listeners")
        if value is None:
            group = "unknown"
        elif value <= low:
            group = "low_observed"
        elif value <= high:
            group = "medium_observed"
        else:
            group = "high_observed"
        a["artist_popularity_group"] = group
    return {"method": "sample_tertiles_of_artist_listeners", "low_threshold": low,
            "high_threshold": high, "n_known_artists": len(vals),
            "interpretation": "Terciles relativos a esta muestra, no umbrales universales ni condición de artista emergente"}


def build_dataset(artists: dict[str, dict], recordings: list[dict],
                  ap: dict[str, dict], rp: dict[str, dict],
                  failed_ap: set[str], failed_rp: set[str], date: str) -> tuple[list[dict], dict]:
    for artist_id, artist in artists.items():
        payload = ap.get(artist_id, {})
        artist.update({
            "artist_listens": payload.get("total_listen_count"),
            "artist_listeners": payload.get("total_user_count"),
            "artist_popularity_status": popularity_status(artist_id, ap, failed_ap),
        })
    groups = popularity_groups(artists)
    rows = []
    for recording in recordings:
        artist = artists[recording["artist_mbid"]]
        rid = recording["recording_mbid"]
        pop = rp.get(rid, {})
        rows.append({
            **recording, **artist,
            "recording_listens": pop.get("total_listen_count"),
            "recording_listeners": pop.get("total_user_count"),
            "recording_popularity_status": popularity_status(rid, rp, failed_rp),
            "extracted_at": date,
            "musicbrainz_url": f"https://musicbrainz.org/recording/{rid}",
            "data_sources": "MusicBrainz; ListenBrainz queried",
        })
    return rows, groups


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def percent(n: int, total: int) -> float | None:
    return round(100.0 * n / total, 2) if total else None


def quality_report(rows: list[dict], artists: dict[str, dict], excluded: list[dict],
                   group_def: dict, errors: list[dict], unselected: list[dict] | None = None) -> dict:
    count = len(rows)
    unselected = unselected or []
    by_genre = {}
    for genre in sorted({a["sampling_genre"] for a in artists.values()}):
        subset = [r for r in rows if r["sampling_genre"] == genre]
        missing = sum(r["recording_listeners"] is None for r in subset)
        by_genre[genre] = {
            "recordings": len(subset), "artists_with_recordings": len({r["artist_mbid"] for r in subset}),
            "missing_recording_popularity": missing, "missing_recording_popularity_pct": percent(missing, len(subset)),
        }
    rec_status = Counter(r["recording_popularity_status"] for r in rows)
    artist_status = Counter(a["artist_popularity_status"] for a in artists.values())
    return {
        "version": VERSION,
        "records": count,
        "unique_recordings": len({r["recording_mbid"] for r in rows}),
        "artists_loaded": len(artists),
        "unique_artists_with_recordings": len({r["artist_mbid"] for r in rows}),
        "genre_strata": list(by_genre),
        "records_by_genre": by_genre,
        "recording_popularity_status": dict(rec_status),
        "artist_popularity_status": dict(artist_status),
        "missing_recording_listeners": sum(r["recording_listeners"] is None for r in rows),
        "missing_recording_listeners_pct": percent(sum(r["recording_listeners"] is None for r in rows), count),
        "missing_duration": sum(r["duration_ms"] is None for r in rows),
        "missing_duration_pct": percent(sum(r["duration_ms"] is None for r in rows), count),
        "missing_recording_genres": sum(not r["recording_genres"] for r in rows),
        "missing_recording_genres_pct": percent(sum(not r["recording_genres"] for r in rows), count),
        "effective_genres_available_pct": percent(sum(bool(r.get("effective_genres")) for r in rows), count),
        "genre_source_counts": dict(Counter(r.get("genre_source", "not_provided") for r in rows)),
        "title_initial_a_pct": percent(sum((r["track_name"] or "").strip().casefold().startswith("a") for r in rows), count),
        "artist_countries": dict(Counter(a.get("artist_country") or "unknown" for a in artists.values())),
        "artist_popularity_groups": dict(Counter(a.get("artist_popularity_group", "unknown") for a in artists.values())),
        "group_definition": group_def,
        "valid_candidates_not_selected": len(unselected),
        "unselected_by_reason": dict(Counter(r["reason"] for r in unselected)),
        "exclusions_total": len(excluded),
        "exclusions_by_reason": dict(Counter(r["reason"] for r in excluded)),
        "warnings_and_errors_count": len(errors),
        "limitations": [
            "No es una muestra representativa de la industria musical.",
            "sampling_genre es la etiqueta de búsqueda, no el género exclusivo de cada grabación.",
            "Popularidad ListenBrainz no equivale a popularidad global ni a emergente.",
            "Un valor faltante de popularidad nunca debe imputarse como cero sin justificación.",
            "Las etiquetas por grabación pueden faltar; las de artista no sustituyen características acústicas.",
            "No hay preferencias verificadas de usuarios ni relevancia musical evaluada todavía.",
            "Las reglas de exclusión de títulos son heurísticas y requieren revisión manual.",
            "Candidatos musicales con el mismo título no son rechazos de calidad: pueden ser versiones distintas.",
            "effective_genres usa etiquetas de artista cuando faltan etiquetas de grabación; no implica género verificado por canción.",
            "Las ventanas exploradas son un subconjunto del catálogo (máximo offset configurable).",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SIDE B Collector v2.2 (MusicBrainz y ListenBrainz; caché reanudable)")
    parser.add_argument("--artists-per-genre", type=int, default=3)
    parser.add_argument("--recordings-per-artist", type=int, default=5)
    parser.add_argument("--artist-pages", type=int, default=2, help="Páginas consecutivas de búsqueda por género; máximo 5")
    parser.add_argument("--recording-pages", type=int, default=2, help="Ventanas separadas de grabaciones por artista; máximo 5")
    parser.add_argument("--max-recording-offset", type=int, default=900,
                        help="Máximo desplazamiento para explorar grabaciones, múltiplo de 100")
    parser.add_argument("--genres", nargs="+", default=DEFAULT_GENRES)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/pilot_v2"))
    args = parser.parse_args(argv)
    if args.artists_per_genre < 1 or args.recordings_per_artist < 1:
        parser.error("Las cantidades de artistas y grabaciones deben ser positivas")
    if not 1 <= args.artist_pages <= 5 or not 1 <= args.recording_pages <= 5:
        parser.error("--artist-pages y --recording-pages deben estar entre 1 y 5")
    if args.max_recording_offset < 0 or args.max_recording_offset % 100 != 0:
        parser.error("--max-recording-offset debe ser un múltiplo no negativo de 100")
    if len(set(args.genres)) != len(args.genres):
        parser.error("No repitas géneros en --genres")
    contact = os.environ.get("SIDEB_CONTACT", "").strip()
    if not contact or contact == "tu_correo@dominio.com":
        parser.error("Configura SIDEB_CONTACT con tu correo o URL pública de contacto")
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    (output / "raw").mkdir(exist_ok=True)
    date = utc_now()
    client = APIClient(contact, cache_dir=output / "raw" / "musicbrainz_cache")
    try:
        selected, candidate_provenance = select_artists(
            client, args.genres, args.artists_per_genre, args.seed, args.artist_pages,
        )
        artists, recordings, excluded, unselected = fetch_artist_and_recordings(
            client, selected, args.recordings_per_artist, args.seed,
            args.recording_pages, args.max_recording_offset,
        )
    except RuntimeError as exc:
        print(f"\nRecolección interrumpida por servicio externo: {exc}", file=sys.stderr)
        print(f"Respuestas MusicBrainz guardadas: {client.cache_saved}; "
              f"reutilizadas: {client.cache_hits}.", file=sys.stderr)
        print("Repite el MISMO comando, conservando la misma ruta --out: "
              "se recuperarán las consultas exitosas guardadas en raw/musicbrainz_cache/.",
              file=sys.stderr)
        return 2
    if not recordings:
        print("No se obtuvieron grabaciones válidas. Revisa los avisos.", file=sys.stderr)
        return 1
    print(f"Consultando popularidad: {len(artists)} artistas y {len(recordings)} grabaciones", flush=True)
    ap = client.lb_popularity("artist", list(artists))
    rp = client.lb_popularity("recording", [r["recording_mbid"] for r in recordings])
    dataset, groups = build_dataset(
        artists, recordings, ap, rp,
        client.failed_popularity_ids["artist"], client.failed_popularity_ids["recording"], date,
    )
    quality = quality_report(dataset, artists, excluded, groups, client.errors, unselected)
    write_csv(output / "side_b_dataset.csv", dataset, DATASET_COLUMNS)
    write_csv(output / "artists.csv", list(artists.values()), ARTIST_COLUMNS)
    write_csv(output / "excluded_recordings.csv", excluded, EXCLUSION_COLUMNS)
    write_csv(output / "unselected_recordings.csv", unselected, UNSELECTED_COLUMNS)
    for filename, data in [
        ("raw/selected_artists.json", selected),
        ("raw/artist_search_candidates.json", candidate_provenance),
        ("raw/artist_popularity.json", ap),
        ("raw/recording_popularity.json", rp),
        ("collection_errors.json", client.errors),
        ("quality_report.json", quality),
    ]:
        with (output / filename).open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    manifest = {
        "project": "SIDE B", "collector_version": VERSION,
        "cached_musicbrainz_responses_reused": client.cache_hits,
        "cached_musicbrainz_responses_saved": client.cache_saved,
        "musicbrainz_cache_path": "raw/musicbrainz_cache",

        "collected_at_utc": date, "seed": args.seed, "genres": args.genres,
        "artists_per_genre": args.artists_per_genre,
        "recordings_per_artist": args.recordings_per_artist,
        "artist_pages": args.artist_pages, "recording_pages": args.recording_pages,
        "max_recording_offset": args.max_recording_offset,
        "selection_method": "Muestreo pseudoaleatorio reproducible; ventanas aleatorias acotadas; preferencia por títulos distintos al seleccionar",
        "exclusion_rules": "Solo títulos explícitamente no musicales, registros inválidos y MBIDs repetidos; títulos iguales válidos se registran como no seleccionados",
        "sources": ["https://musicbrainz.org", "https://api.listenbrainz.org"],
        "notes": "No hay historial ni identificadores de oyentes individuales; no incluye contacto personal del recolector",
    }
    with (output / "manifest.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    print(f"\nCaché MusicBrainz: {client.cache_hits} consultas reutilizadas, "
          f"{client.cache_saved} respuestas guardadas")
    print(f"\nDataset creado: {(output / 'side_b_dataset.csv').resolve()}")
    print("Reporte:", json.dumps(quality, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
