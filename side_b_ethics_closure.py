"""Dictamen reproducible de cierre técnico y límites éticos de SIDE B.

Utiliza resultados experimentales y conteos agregados existentes. No infiere
respuestas individuales, satisfacción humana ni certificación de equidad.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = {
    "A": "A_pop25_sin_tope",
    "B": "B_pop25_con_tope",
    "C": "C_pop05_sin_tope",
    "D": "D_pop05_con_tope",
}
GATES = (
    ("G01", "Valoraciones humanas originales por candidato y comparación pareada A/C", "R01|R06|R11"),
    ("G02", "Consentimientos documentados y protocolo de uso y conservación de datos", "R05|R06"),
    ("G03", "Revisión por escucha de grabaciones y pertinencia idiomática", "R02|R03|R10"),
    ("G04", "Revisión de cobertura cultural y límites de representatividad", "R07"),
    ("G05", "Autenticación individual, TLS y revisión de seguridad para despliegue", "R04|R08"),
    ("G06", "Respaldo externo y ensayo de recuperación de bitácora HMAC", "R09"),
    ("G07", "Evaluación y aprobación documentadas por personas responsables", "R01|R11"),
)


def _csv_rows(path: Path, **kwargs) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as src:
        rows = list(csv.DictReader(src, **kwargs))
    if not rows:
        raise ValueError(f"CSV vacío: {path.name}")
    return rows


def build_report(root: Path = ROOT) -> dict:
    """Revisa evidencia disponible; jamás promueve un riesgo a cerrado."""
    root = Path(root)
    ablation_path = root / "data/auditoria_v0_1/ablation_overall.csv"
    risk_path = root / "docs/matriz_riesgos.csv"
    study_path = root / "data/estudio_v08/resumen_grupal.csv"
    ablation = _csv_rows(ablation_path)
    policies = {r["policy"]: r for r in ablation}
    if set(policies) != set(POLICIES.values()):
        raise ValueError("Faltan o sobran políticas A/B/C/D en la ablación")
    stats = {}
    for name, policy in POLICIES.items():
        r = policies[policy]
        total = int(r["total_positions"])
        parts = tuple(int(r[f"positions_{group}_observed"])
                      for group in ("low", "medium", "high"))
        sim = float(r["mean_similarity_proxy"])
        if total != 60 or sum(parts) != total or not 0 <= sim <= 1:
            raise ValueError(f"Resultados incoherentes en política {name}")
        stats[name] = {"posiciones": total, "baja": parts[0], "media": parts[1],
                       "alta": parts[2], "alta_porcentaje": round(100 * parts[2] / total, 2),
                       "similitud_proxy": sim}
    risks = _csv_rows(risk_path)
    seen = set()
    for row in risks:
        rid = row["id"]
        if rid in seen or not rid.startswith("R") or not rid[1:].isdigit():
            raise ValueError("Identificadores de riesgos repetidos o inválidos")
        seen.add(rid)
        p, i, score = (int(row[k]) for k in
                       ("probabilidad_1_5", "impacto_1_5", "prioridad_estimada"))
        if not 1 <= p <= 5 or not 1 <= i <= 5 or score != p * i:
            raise ValueError(f"Prioridad de riesgo incoherente: {rid}")
    if len(risks) != 11 or any(rid not in seen for _, _, ids in GATES for rid in ids.split("|")):
        raise ValueError("El dictamen requiere los 11 riesgos documentados")
    study = _csv_rows(study_path, delimiter=";")
    total_reports = sum(int(r["participantes"]) for r in study)
    if total_reports != 9:
        raise ValueError("El resumen agregado debe corresponder a nueve relatos")
    if any("nombre" in k.lower() or "correo" in k.lower() for k in study[0]):
        raise ValueError("El resumen público no debe incluir identificadores personales")
    high = sum(int(r["prioridad_estimada"]) >= 15 for r in risks)
    return {
        "formato": "SIDE_B_DICTAMEN_ETICO_V011",
        "evidencia": {
            "politicas": stats,
            "reduccion_posiciones_altas_A_C": stats["A"]["alta"] - stats["C"]["alta"],
            "diferencia_puntos_porcentuales_A_C": (stats["A"]["alta_porcentaje"] -
                                                    stats["C"]["alta_porcentaje"]),
            "relatos_cualitativos_agregados": total_reports,
            "riesgos_total": len(risks), "riesgos_prioridad_alta": high,
        },
        "interpretacion": (
            "La diferencia de exposición es descriptiva, no una prueba de justicia, "
            "causalidad ni satisfacción. Las posiciones no son oyentes independientes. "
            "Nueve relatos indirectos no permiten calcular preferencias A/C pareadas."
        ),
        "criterios_de_salida": [
            {"id": key, "descripcion": detail, "riesgos": ids.split("|"),
             "estado": "PENDIENTE", "aprobacion_automatica": False}
            for key, detail, ids in GATES
        ],
        "uso_academico_local": "PERMITIDO_CON_LIMITACIONES",
        "despliegue_publico": "NO_AUTORIZADO",
        "paper_formato_revista_3i": "PLANIFICADO_NO_REDACTADO",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cierre ético verificable de SIDE B")
    parser.add_argument("--out", type=Path,
                        help="Salida JSON opcional local fuera de los resultados históricos")
    args = parser.parse_args()
    report = build_report()
    metrics = report["evidencia"]
    print(f"A: {metrics['politicas']['A']['alta']}/60 puestos de popularidad alta; "
          f"C: {metrics['politicas']['C']['alta']}/60.")
    print(f"{metrics['relatos_cualitativos_agregados']} relatos agregados; "
          f"{metrics['riesgos_total']} riesgos; "
          f"{metrics['riesgos_prioridad_alta']} de prioridad alta.")
    print(f"Despliegue público: {report['despliegue_publico']}. "
          f"Criterios pendientes: {len(report['criterios_de_salida'])}.")
    if args.out:
        path = args.out.resolve()
        if path.exists() and path.is_dir():
            raise ValueError("--out debe ser un archivo JSON, no un directorio")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
