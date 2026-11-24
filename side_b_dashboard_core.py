"""Motor del panel local SIDE B, con cálculos reproducibles y sin red.

Trabaja sobre la misma muestra de artistas que el modelo experimental.
Las decisiones del auditor se conservan APARTE del dataset y de los CSV académicos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import math
import re
import json
import hashlib
import hmac
import os
import secrets
import tempfile
import threading

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from side_b_model_v0 import GROUPS, genre_token, greedy_cap_ranking, load_catalog

POLICIES = {
    "A · 25 % popularidad · sin límite": (0.25, False),
    "B · 25 % popularidad · con límite": (0.25, True),
    "C · 5 % popularidad · sin límite": (0.05, False),
    "D · 5 % popularidad · con límite": (0.05, True),
}
REPRESENTATIONS = {
    "Solo etiquetas del artista": "artist_only",
    "Artista + etiqueta de muestreo": "with_sampling",
}
GROUP_LABELS = {"low_observed": "Baja", "medium_observed": "Media", "high_observed": "Alta"}
AUDIT_BASE_FIELDS = ["event_id", "timestamp_utc", "reviewer_alias", "representation", "profile", "policy",
                     "artist_mbid", "artist_name", "decision", "reason"]
AUDIT_FIELDS = AUDIT_BASE_FIELDS + ["previous_mac", "entry_mac"]
VALID_DECISIONS = {"Aprobar", "Solicitar revisión", "Bloquear en demo"}


def _artist_only_text(genre_string: str) -> str:
    tokens = {genre_token(value) for value in str(genre_string).split(";") if value.strip()}
    return " ".join(sorted(t for t in tokens if t))


def csv_semicolon(path: Path) -> pd.DataFrame:
    """Leer archivos del evaluador, que usan ;, sin mezclar fuentes."""
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, sep=";", encoding="utf-8-sig")


def numeric_summary(df: pd.DataFrame, label: str) -> dict:
    if df.empty:
        return {"fuente": label, "participantes_pop": 0, "participantes_rock": 0,
                "A_pop": None, "C_pop": None, "A_rock": None, "C_rock": None}
    result = {"fuente": label, "participantes_pop": 0, "participantes_rock": 0,
              "A_pop": None, "C_pop": None, "A_rock": None, "C_rock": None}
    for r in df.to_dict("records"):
        name = str(r.get("profile", ""))
        if name in ("pop", "rock"):
            result[f"participantes_{name}"] = int(r["complete_participants"])
            result[f"A_{name}"] = round(float(r["mean_A"]), 3)
            result[f"C_{name}"] = round(float(r["mean_C"]), 3)
    return result


class SideBEngine:
    def __init__(self, root: Path, review_token: str | None = None):
        self.root = Path(root).resolve()
        self.review_token = (review_token if review_token is not None else os.getenv("SIDEB_REVIEW_TOKEN", "")).strip()
        self._review_lock = threading.RLock()
        self.dataset_path = self.root / "data" / "dataset_v1" / "side_b_dataset.csv"
        self.tracks = pd.read_csv(self.dataset_path, dtype=str, keep_default_na=False)
        self.catalog, self.audit = load_catalog(self.dataset_path)
        self.profiles = sorted(self.catalog["sampling_genre"].dropna().unique().tolist())
        self.audit_log_path = self.root / "data" / "supervision" / "revisiones_demo.csv"
        self._repr = {}
        for mode in REPRESENTATIONS.values():
            c = self.catalog.copy()
            if mode == "artist_only":
                c["tag_text"] = c["artist_genres"].map(_artist_only_text)
            vectorizer = TfidfVectorizer(analyzer=str.split, lowercase=False, norm="l2")
            vectors = vectorizer.fit_transform(c["tag_text"].tolist())
            self._repr[mode] = (c, vectorizer, vectors)

    def available(self, profile: str, representation: str, block: set[str] | None = None) -> pd.DataFrame:
        if profile not in self.profiles:
            raise ValueError("Perfil musical no reconocido")
        if representation not in REPRESENTATIONS.values():
            raise ValueError("Representación no reconocida")
        catalog, vec, artist_vecs = self._repr[representation]
        queries = vec.transform([genre_token(profile)])
        similarity = cosine_similarity(queries, artist_vecs)[0]
        pool = catalog.copy()
        pool["content_similarity"] = np.round(similarity, 12)
        pool = pool.loc[pool["content_similarity"] > 0].copy()
        if block:
            pool = pool.loc[~pool["artist_mbid"].isin(block)].copy()
        return pool

    def recommendations(self, profile: str, policy: str, representation: str,
                        k: int = 10, apply_review_blocks: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
        if policy not in POLICIES:
            raise ValueError("Política desconocida")
        if not 1 <= int(k) <= 30:
            raise ValueError("El número de recomendaciones debe estar entre 1 y 30")
        blocked = self.blocked_for(profile, policy, representation) if apply_review_blocks else set()
        pool = self.available(profile, representation, blocked)
        if pool.empty:
            return pd.DataFrame(), pool, False
        weight, cap = POLICIES[policy]
        pool["ranking_score"] = np.round((1-weight)*pool["content_similarity"] + weight*pool["pop_percentile"], 12)
        if cap:
            selected, relaxed = greedy_cap_ranking(pool.rename(columns={"ranking_score": "mitigation_score"}), int(k))
            selected = selected.rename(columns={"mitigation_score": "ranking_score"})
        else:
            selected = pool.sort_values(["ranking_score", "content_similarity", "artist_mbid"],
                                        ascending=[False,False,True], kind="mergesort").head(int(k))
            relaxed = False
        selected = selected.copy().reset_index(drop=True)
        selected.insert(0, "position", range(1, len(selected)+1))
        return selected, pool, relaxed

    def explain_candidate(self, profile: str, policy: str, representation: str,
                          artist_mbid: str, k: int = 10,
                          apply_review_blocks: bool = False) -> dict:
        """Desglose reproducible de un puesto; no es una explicación causal.

        Importante: la similitud usa etiquetas de *artista*. Las etiquetas de la
        grabación ilustrativa pueden ser distintas o estar ausentes.
        """
        ranked, pool, relaxed = self.recommendations(
            profile, policy, representation, k, apply_review_blocks)
        match = ranked.loc[ranked["artist_mbid"] == artist_mbid]
        if match.empty:
            raise ValueError("El artista no está en el ranking seleccionado")
        r = match.iloc[0]
        weight, capped = POLICIES[policy]
        raw_tags = [t.strip() for t in str(r["artist_genres"]).split(";") if t.strip()]
        token = genre_token(profile)
        overlap = [t for t in raw_tags if genre_token(t) == token]
        if representation == "with_sampling" and genre_token(r["sampling_genre"]) == token:
            overlap.append("etiqueta de muestreo (no verificada para la canción)")
        musical = float(r["content_similarity"])
        pop = float(r["pop_percentile"])
        return {
            "artist_name": str(r["artist_name"]),
            "track_example": str(r["track_name"]),
            "rank": int(r["position"]),
            "pop_group": GROUP_LABELS[str(r["pop_group"])],
            "genre_source": str(r.get("genre_source", "desconocida")),
            "matched_tags": overlap,
            "similarity": musical,
            "pop_percentile": pop,
            "similarity_weight": 1.0 - weight,
            "popularity_weight": weight,
            "similarity_contribution": (1.0-weight)*musical,
            "popularity_contribution": weight*pop,
            "total_score": (1.0-weight)*musical + weight*pop,
            "has_group_cap": capped,
            "cap_relaxed": bool(relaxed),
            "population": len(pool),
            "note": "Los puestos incluyen reglas de ordenación y, cuando corresponde, tope por grupo. "
                    "No son pruebas de gusto musical individual ni de ausencia de discriminación."
        }

    def group_comparison(self, profile: str, policy_a: str, policy_b: str,
                         representation: str, k: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
        # Sin decisiones humanas, para mantener los conjuntos comparables.
        a, pool_a, relaxed_a = self.recommendations(profile,policy_a,representation,k)
        b, pool_b, relaxed_b = self.recommendations(profile,policy_b,representation,k)
        rows=[]
        for group in GROUPS:
            eligible=int((pool_a["pop_group"] == group).sum())
            for name, ranked in ((policy_a,a),(policy_b,b)):
                n=int((ranked["pop_group"]==group).sum()) if not ranked.empty else 0
                rows.append({"Popularidad":GROUP_LABELS[group], "Política":name.split(' · ')[0],
                             "Apariciones":n, "Elegibles":eligible,
                             "% en Top-K":round(100*n/max(len(ranked),1),1),
                             "% del conjunto elegible":round(100*eligible/max(len(pool_a),1),1)})
        metrics=pd.DataFrame(rows)
        candidates = {"Perfil":profile,"Elegibles":len(pool_a),
                      "Recomendaciones A":len(a),"Recomendaciones B":len(b),
                      "Similitud A":round(float(a["content_similarity"].mean()),4) if not a.empty else None,
                      "Similitud B":round(float(b["content_similarity"].mean()),4) if not b.empty else None,
                      "Artistas compartidos":len(set(a["artist_mbid"]) & set(b["artist_mbid"])),
                      "Tope relajado A": bool(relaxed_a), "Tope relajado B":bool(relaxed_b)}
        tab = pd.DataFrame([candidates])
        display = []
        for label, ranked in ((policy_a,a),(policy_b,b)):
            for r in ranked.itertuples(index=False):
                display.append({"Política":label.split(' · ')[0], "Puesto":r.position,
                                "Artista":r.artist_name, "Grupo":GROUP_LABELS[r.pop_group],
                                "Canción ilustrativa":r.track_name,
                                "Similitud":round(float(r.content_similarity),3)})
        note = ("Comparación local sobre el mismo conjunto elegible; las políticas difieren en el ranking. "
                "La similitud es una aproximación basada en etiquetas musicales, NO satisfacción humana. "
                "Las decisiones de supervisión NO se aplican en esta comparación experimental.")
        if len(pool_a) < k:
            note += f" Solo hay {len(pool_a)} artistas elegibles para '{profile}'; no se inventan candidatos."
        return metrics,tab,pd.DataFrame(display),note

    def _require_token(self, supplied: str) -> None:
        """La auditoría es solo editable en modo local con un secreto configurado."""
        if len(self.review_token) < 16:
            raise PermissionError("Supervisión en solo lectura. Configura SIDEB_REVIEW_TOKEN (16+ caracteres) antes de iniciar Gradio.")
        if not secrets.compare_digest(self.review_token, str(supplied or "")):
            raise PermissionError("Clave de supervisión incorrecta; no se registró ninguna acción.")

    def _mac_key(self) -> bytes:
        if len(self.review_token) < 16:
            raise PermissionError("Se necesita la clave local original para verificar el registro de decisiones.")
        return hashlib.sha256(("SIDE_B_AUDIT_CHAIN_V1|" + self.review_token).encode("utf-8")).digest()

    def _event_mac(self, entry: dict) -> str:
        msg=json.dumps({k:entry[k] for k in AUDIT_BASE_FIELDS+["previous_mac"]},
                       sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hmac.new(self._mac_key(),msg.encode("utf-8"),hashlib.sha256).hexdigest()

    def _read_and_verify(self) -> list[dict]:
        p=self.audit_log_path
        if not p.exists():
            return []
        if not p.is_file():
            raise ValueError("Ruta del registro inválida")
        # Comprobar antes de devolver datos o aplicar bloqueos: fallo seguro si hubo manipulación.
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            reader=csv.DictReader(f)
            if reader.fieldnames != AUDIT_FIELDS:
                raise ValueError("Formato del registro inválido o versión antigua sin firma. Conserva una copia; no lo sobrescribas.")
            rows=list(reader)
        expected_prev="GENESIS"
        for n, row in enumerate(rows, 1):
            if set(row) != set(AUDIT_FIELDS) or row.get("event_id") != str(n):
                raise ValueError("Registro de auditoría alterado o incompleto")
            if row["previous_mac"] != expected_prev or not hmac.compare_digest(row["entry_mac"],self._event_mac(row)):
                raise ValueError("Registro de auditoría alterado: fallo de integridad. No se aplican bloqueos.")
            expected_prev=row["entry_mac"]
        return rows

    def audit_records(self) -> pd.DataFrame:
        with self._review_lock:
            rows=self._read_and_verify()
        return pd.DataFrame(rows, columns=AUDIT_FIELDS)

    def history_for(self, supplied_token: str, limit: int = 15) -> pd.DataFrame:
        self._require_token(supplied_token)
        return self.audit_records().tail(limit).iloc[::-1].reset_index(drop=True)

    def blocked_for(self, profile: str, policy: str, representation: str) -> set[str]:
        records=self.audit_records()
        if records.empty:
            return set()
        same=records.loc[(records.profile==profile)&(records.policy==policy)&
                         (records.representation==representation)]
        if same.empty:
            return set()
        last=same.drop_duplicates("artist_mbid",keep="last")
        return set(last.loc[last.decision=="Bloquear en demo", "artist_mbid"])

    def review(self, reviewer_alias: str, profile: str, policy: str, representation: str,
               artist_mbid: str, decision: str, reason: str, access_token: str = "") -> str:
        self._require_token(access_token)
        alias=str(reviewer_alias).strip()
        reason=str(reason).strip()
        # Rechazar fórmulas de hojas de cálculo, controles y saltos de línea en campos escritos por el usuario.
        for field in (alias,reason):
            if any(ord(ch) < 32 or ord(ch) == 127 for ch in field) or field.lstrip().startswith(("=","+","-","@")):
                raise ValueError("Alias o motivo contiene caracteres no permitidos para exportación segura")
        if not re.fullmatch(r"[\w][\w\- ]{1,31}",alias,flags=re.UNICODE):
            raise ValueError("Usa un alias de 2 a 32 caracteres, sin datos personales")
        if decision not in VALID_DECISIONS:
            raise ValueError("Decisión desconocida")
        if not (10 <= len(reason) <= 500):
            raise ValueError("Explica tu decisión en entre 10 y 500 caracteres")
        if policy not in POLICIES or representation not in REPRESENTATIONS.values() or profile not in self.profiles:
            raise ValueError("Perfil, representación o política inválida")
        row=self.catalog.loc[self.catalog.artist_mbid==artist_mbid]
        if row.empty or artist_mbid not in set(self.available(profile,representation).artist_mbid):
            raise ValueError("El artista no pertenece al conjunto elegible del perfil")
        artist_name=str(row.iloc[0].artist_name)
        if artist_name.lstrip().startswith(("=","+","-","@")):
            artist_name="'"+artist_name  # prevenir CSV formula injection en metadatos públicos
        with self._review_lock:
            prior=self._read_and_verify()  # no anexar encima de datos alterados
            record={"event_id":str(len(prior)+1),"timestamp_utc":datetime.now(timezone.utc).isoformat(),
                    "reviewer_alias":alias,"representation":representation,"profile":profile,"policy":policy,
                    "artist_mbid":artist_mbid,"artist_name":artist_name,"decision":decision,"reason":reason,
                    "previous_mac":prior[-1]["entry_mac"] if prior else "GENESIS"}
            record["entry_mac"]=self._event_mac(record)
            self.audit_log_path.parent.mkdir(parents=True,exist_ok=True)
            # Archivo temporal en el mismo directorio: reemplazo atómico; evita registros parciales.
            fd,temp_path=tempfile.mkstemp(prefix=".sideb_audit_",suffix=".csv",dir=self.audit_log_path.parent)
            try:
                with os.fdopen(fd,"w",encoding="utf-8-sig",newline="") as f:
                    writer=csv.DictWriter(f,fieldnames=AUDIT_FIELDS)
                    writer.writeheader(); writer.writerows(prior+[record]); f.flush();os.fsync(f.fileno())
                os.replace(temp_path,self.audit_log_path)
            finally:
                if os.path.exists(temp_path): os.unlink(temp_path)
        return f"Decisión registrada: {decision} para {record['artist_name']}. Los datos científicos no se modificaron."

    def evaluation(self, simulated: bool) -> pd.DataFrame:
        location = (self.root / "simulacion" / "validacion_humana" if simulated
                    else self.root / "data" / "validacion_humana_v0_3")
        return csv_semicolon(location/"analysis"/"summary_by_profile.csv")

    def simple_audit(self) -> pd.DataFrame:
        path=self.root/"data"/"auditoria_v0_1"/"ablation_overall.csv"
        return pd.read_csv(path)
