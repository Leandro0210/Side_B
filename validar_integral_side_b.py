"""SIDE B v0.6 — diagnóstico reproducible para la DEMOSTRACIÓN LOCAL.

No es una certificación de justicia algorítmica, seguridad ni privacidad.
No necesita internet ni recopila respuestas individuales.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import pandas as pd

from side_b_dashboard_core import GROUPS, POLICIES, SideBEngine
from verificar_evidencias import verify

ROOT = Path(__file__).resolve().parent
POLICY_IDS = {
    "A": "A_pop25_sin_tope", "B": "B_pop25_con_tope",
    "C": "C_pop05_sin_tope", "D": "D_pop05_con_tope",
}
MODES = {"with_sampling": "original_con_muestreo", "artist_only": "solo_etiquetas_artista"}


def _checks(result: dict, key: str, fn) -> None:
    try:
        detail = fn()
        result["checks"].append({"id": key, "status": "OK", "detail": detail})
    except (AssertionError, OSError, ValueError, KeyError, TypeError, PermissionError) as exc:
        result["checks"].append({"id": key, "status": "FALLA", "detail": str(exc) or type(exc).__name__})


def _integrity(root: Path) -> str:
    bad, total = verify(root / "docs" / "manifiesto_evidencias_sha256.json", root)
    assert not bad, "; ".join(bad)
    assert total >= 5, "Manifiesto incompleto"
    return f"{total} archivos de evidencia coinciden con SHA-256"


def _catalog(engine: SideBEngine) -> str:
    tracks = engine.tracks
    assert len(tracks) == 576, "El catálogo ya no tiene 576 grabaciones; revisar su versión"
    assert tracks["recording_mbid"].nunique() == len(tracks), "Grabaciones duplicadas"
    assert len(engine.catalog) == 72, "El catálogo ya no tiene 72 artistas"
    assert len(engine.profiles) == 6, "Se esperaban seis perfiles musicales"
    assert set(engine.catalog["pop_group"]) == set(GROUPS), "Falta un tercil"
    assert all(tracks["artist_listeners"].str.strip()), "Popularidad de artista ausente"
    return "576 grabaciones, 72 artistas, seis perfiles; sin duplicados de grabación"


def _reproduce(engine: SideBEngine, root: Path) -> tuple[str, list[dict]]:
    references = pd.read_csv(root / "data" / "robustez_v0_2" / "robustness_by_profile.csv")
    assert len(references) == 48, f"Se esperaban 48 escenarios de referencia, hay {len(references)}"
    metrics = []
    policy_names = {name.split(" · ", 1)[0]: name for name in POLICIES}
    for representation, ref_mode in MODES.items():
        for profile in engine.profiles:
            for short, ref_policy in POLICY_IDS.items():
                match = references.loc[(references.representation == ref_mode) &
                                       (references.profile == profile) & (references.policy == ref_policy)]
                assert len(match) == 1, f"Referencia ausente o ambigua: {representation}/{profile}/{short}"
                ref = match.iloc[0]
                ranked, eligible, relaxed = engine.recommendations(profile, policy_names[short], representation, 10)
                assert len(eligible) == int(ref.eligible_total), f"Elegibilidad cambió: {profile}/{short}/{representation}"
                assert len(ranked) == int(ref.recommended_n), f"N° recomendaciones cambió: {profile}/{short}/{representation}"
                assert len(ranked) == ranked.artist_mbid.nunique(), "Un artista aparece más de una vez"
                assert set(ranked.artist_mbid) <= set(eligible.artist_mbid), "Recomendación no elegible"
                assert ranked.position.tolist() == list(range(1, len(ranked)+1)), "Posiciones no consecutivas"
                assert bool(relaxed) == bool(ref.cap_relaxed), "Cambio en relajación del tope"
                assert math.isclose(float(ranked.content_similarity.mean()),
                                    float(ref.mean_similarity_proxy), abs_tol=0.000002), "Similitud no reproducible"
                counts = Counter(ranked.pop_group)
                for group, suffix in (("low_observed", "low"), ("medium_observed", "medium"),
                                      ("high_observed", "high")):
                    assert counts[group] == int(ref[f"topk_{suffix}_observed"]), (
                        f"Exposición cambió: {profile}/{short}/{representation}/{group}")
                if short in ("B", "D") and not relaxed:
                    assert all(n <= math.ceil(10 / 3) for n in counts.values()), "Tope por grupo incumplido"
                if not ranked.empty:
                    explanation = engine.explain_candidate(profile, policy_names[short], representation,
                                                           str(ranked.iloc[0].artist_mbid), 10)
                    assert math.isclose(explanation["total_score"], float(ranked.iloc[0].ranking_score),
                                        abs_tol=1e-9), "Explicación no coincide con el score"
                    assert math.isclose(explanation["similarity_weight"] + explanation["popularity_weight"],
                                        1.0, abs_tol=1e-12), "Pesos incorrectos"
                    assert math.isclose(explanation["similarity_contribution"] +
                                        explanation["popularity_contribution"],
                                        explanation["total_score"], abs_tol=1e-12), "Desglose inconsistente"
                metrics.append({"representacion": representation, "perfil": profile,
                                "politica": short, "elegibles": len(eligible),
                                "recomendaciones": len(ranked),
                                "alta_popularidad_topk": counts["high_observed"],
                                "similitud_proxy_media": round(float(ranked.content_similarity.mean()), 6),
                                "tope_relajado": bool(relaxed)})
    return "48 escenarios reproducidos: ranking, exposición, topes y explicación de puntuaciones", metrics


def _scientific_consistency(root: Path, metrics: list[dict]) -> tuple[str, list[dict]]:
    original = pd.read_csv(root / "data" / "auditoria_v0_1" / "ablation_overall.csv")
    result = []
    for short, key in POLICY_IDS.items():
        row = original.loc[original.policy == key]
        assert len(row) == 1, f"Política {key} ausente en ablación"
        valid = [r for r in metrics if r["representacion"] == "with_sampling" and r["politica"] == short]
        n = sum(r["recomendaciones"] for r in valid)
        high = sum(r["alta_popularidad_topk"] for r in valid)
        assert n == int(row.iloc[0].total_positions), f"Posiciones distintas en {short}"
        assert high == int(row.iloc[0].positions_high_observed), f"Exposición distinta en {short}"
        result.append({"politica": short, "posiciones": n, "alta_popularidad": high,
                       "fraccion_alta": round(high / n, 4) if n else None,
                       "similitud_proxy": float(row.iloc[0].mean_similarity_proxy)})
    return "A/B/C/D coinciden con la ablación publicada; resultado descriptivo, no prueba de equidad", result


def _oversight(root: Path) -> str:
    # No acceder a data/supervision del usuario ni al secreto real.
    secret = "SIDE_B_VALIDACION_SOLO_LOCAL_2026_DOS"
    engine = SideBEngine(root, review_token=secret)
    profile, policy, representation = engine.profiles[0], list(POLICIES)[0], "with_sampling"
    original, _, _ = engine.recommendations(profile, policy, representation)
    artist_id = str(original.iloc[0].artist_mbid)
    with tempfile.TemporaryDirectory() as temp:
        engine.audit_log_path = Path(temp) / "audit.csv"
        denied = False
        try:
            engine.review("AUDITOR_DEMO", profile, policy, representation, artist_id,
                          "Bloquear en demo", "Registro de prueba con clave incorrecta", "incorrecto")
        except PermissionError:
            denied = True
        assert denied and not engine.audit_log_path.exists(), "Escritura sin autorización"
        engine.review("AUDITOR_DEMO", profile, policy, representation, artist_id,
                      "Bloquear en demo", "Prueba verificable de bloqueo autorizado", secret)
        assert artist_id in engine.blocked_for(profile, policy, representation), "Bloqueo no aplicado"
        assert artist_id not in set(engine.recommendations(profile, policy, representation, 10, True)[0].artist_mbid), "Bloqueo no filtra"
        engine.review("AUDITOR_DEMO", profile, policy, representation, artist_id,
                      "Aprobar", "Se autoriza la recuperación de la recomendación", secret)
        assert artist_id not in engine.blocked_for(profile, policy, representation), "Aprobación no restaura"
        content = engine.audit_log_path.read_text(encoding="utf-8-sig")
        assert "Bloquear en demo" in content
        engine.audit_log_path.write_text(content.replace("Bloquear en demo", "Solicitar revisión", 1), encoding="utf-8-sig")
        rejected = False
        try:
            engine.audit_records()
        except ValueError:
            rejected = True
        assert rejected, "Manipulación de HMAC no detectada"
    return "Autorización, bloqueo, restauración e integridad HMAC verificadas en directorio temporal"


def _release_surface(root: Path) -> tuple[str, str]:
    app = (root / "app_gradio.py").read_text(encoding="utf-8")
    assert 'server_name="127.0.0.1"' in app and "share=False" in app, "Arranque local seguro no declarado"
    # Solo se puede afirmar lo que Git tiene bajo control de versiones; archivos
    # locales ignorados no cuentan como publicación.
    try:
        proc = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                              capture_output=True, check=True, timeout=15)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ("PENDIENTE", "Arranque limitado a 127.0.0.1; no es posible revisar archivos versionados sin Git")
    tracked = [x.decode("utf-8", errors="replace").replace("\\", "/")
               for x in proc.stdout.split(b"\0") if x]
    forbidden = [path for path in tracked if path.startswith(("data/supervision/", "data/validacion_humana_v0_3/",
                  "simulacion/", "archivo_historico/", "data/dataset_v1/raw/", ".venv/"))
                 or "/private/" in f"/{path}" or path in (".env",) or path.endswith((".pem", ".key"))]
    assert not forbidden, "Archivos sensibles versionados: " + ", ".join(forbidden[:8])
    return ("OK", f"Arranque 127.0.0.1 sin share; {len(tracked)} rutas versionadas sin directorios privados conocidos")


def _human_evidence(root: Path) -> tuple[str, str]:
    real = root / "data" / "validacion_humana_v0_3" / "analysis" / "summary_by_profile.csv"
    fake = root / "simulacion" / "validacion_humana" / "analysis" / "summary_by_profile.csv"
    if not real.exists() and not fake.exists():
        return "PENDIENTE", "Los agregados privados no están en GitHub; no se deducen resultados humanos ni sintéticos"
    if real.exists() and fake.exists():
        df_real = pd.read_csv(real, sep=";")
        df_fake = pd.read_csv(fake, sep=";")
        assert "complete_participants" in df_real and "complete_participants" in df_fake
        return "PENDIENTE", (f"Fuentes separadas: evaluación real n={int(df_real.complete_participants.max())}, "
                              f"simulada n={int(df_fake.complete_participants.max())}; falta ampliación humana real")
    return "PENDIENTE", "Solo existe uno de los resúmenes: no mezclar ni inferir resultados de la fuente ausente"


def run_audit(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    report = {"format": "SIDE_B_VALIDACION_ETICA_V06", "generated_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Prototipo local, verificaciones técnicas y evidencias existentes",
              "checks": [], "exposure": [], "scenarios": [],
              "public_deployment_approved": False,
              "fairness_certified": False,
              "human_preference_validated": False}
    _checks(report, "integridad_sha256", lambda: _integrity(root))
    try:
        engine = SideBEngine(root, review_token="")  # prohibir edición en la instancia del diagnóstico
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report["checks"].append({"id": "catalogo", "status": "FALLA", "detail": str(exc)})
        report["technical_checks_pass"] = False
        return report
    _checks(report, "catalogo", lambda: _catalog(engine))

    def scenarios():
        detail, cases = _reproduce(engine, root)
        report["scenarios"] = cases
        return detail
    _checks(report, "reproduccion_48_escenarios", scenarios)
    if report["scenarios"]:
        def crosscheck():
            detail, data = _scientific_consistency(root, report["scenarios"])
            report["exposure"] = data
            return detail
        _checks(report, "consistencia_ablacion", crosscheck)
    _checks(report, "supervision_hmac", lambda: _oversight(root))
    try:
        status, detail = _release_surface(root)
        report["checks"].append({"id": "privacidad_publicacion", "status": status, "detail": detail})
    except (AssertionError, OSError, ValueError, TypeError) as exc:
        report["checks"].append({"id": "privacidad_publicacion", "status": "FALLA",
                                 "detail": str(exc) or type(exc).__name__})
    try:
        status, detail = _human_evidence(root)
        report["checks"].append({"id": "evidencia_humana", "status": status, "detail": detail})
    except (OSError, ValueError, KeyError) as exc:
        report["checks"].append({"id": "evidencia_humana", "status": "FALLA", "detail": str(exc)})
    report["technical_checks_pass"] = all(c["status"] != "FALLA" for c in report["checks"])
    return report


def markdown_report(report: dict) -> str:
    status = "PASAN" if report.get("technical_checks_pass") else "FALLAN"
    out = [f"### Diagnóstico integral SIDE B · v0.6 — comprobaciones técnicas {status}",
           "", "| Control | Estado | Resultado |", "|---|---|---|"]
    for item in report["checks"]:
        clean = str(item["detail"]).replace("|", "/").replace("\n", " ")
        out.append(f"| `{item['id']}` | {item['status']} | {clean} |")
    if report.get("exposure"):
        out.extend(["", "**Exposición en las seis consultas experimentales (representación con etiqueta de muestreo):**",
                    "", "| Política | Posiciones | Pop. alta | Fracción | Similitud proxy |", "|---|---:|---:|---:|---:|"])
        for m in report["exposure"]:
            out.append(f"| {m['politica']} | {m['posiciones']} | {m['alta_popularidad']} | "
                       f"{100*m['fraccion_alta']:.1f}% | {m['similitud_proxy']:.3f} |")
    out.extend(["", "**Interpretación:** una reducción de exposición de artistas populares en esta muestra "
                "no demuestra justicia normativa ni mayor satisfacción de oyentes.",
                "**Decisión:** utilizable como demostración académica local si las comprobaciones técnicas pasan; "
                "**NO** autorizado para despliegue público, ni validado con suficientes participantes reales.",
                "**Límites:** el HMAC no detecta por sí solo eliminación completa ni truncamiento del archivo; "
                "las verificaciones de publicación no sustituyen auditoría de seguridad."])
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description="Validación técnica y ética de SIDE B, sin acceso a red")
    p.add_argument("--out", type=Path, help="Carpeta para reporte JSON y Markdown (opcional)")
    args = p.parse_args()
    report = run_audit()
    text = markdown_report(report)
    print(text)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "validacion_integral_v06.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.out / "validacion_integral_v06.md").write_text(text, encoding="utf-8")
        print(f"\nArchivos generados en {args.out}")
    return 0 if report.get("technical_checks_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
