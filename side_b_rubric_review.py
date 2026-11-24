"""Revisión técnica SIDE B contra los siete criterios del proyecto final (100 pt).

Evalúa PRESENCIA y coherencia de evidencias. Nunca atribuye puntos académicos,
certifica derechos, inventa consentimiento ni asume satisfacción de oyentes.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from side_b_ethics_closure import build_report

ROOT = Path(__file__).resolve().parent
CRITERIA = (
    ("01", "Descripción del sistema y objetivo", 10, "SÓLIDA",
     ("README.md", "docs/guias/MODELO.md"),
     "Describir SIDE B como recomendador experimental de artistas, no reproductor de audio."),
    ("02", "Stakeholders y datos utilizados", 10, "SÓLIDA",
     ("docs/DICCIONARIO_DATOS.md", "data/dataset_v1/side_b_dataset.csv"),
     "Explicar los 72 artistas, 576 grabaciones y las limitaciones geográficas y de extracción."),
    ("03", "Sesgos y análisis de fairness", 15, "SÓLIDA",
     ("data/auditoria_v0_1/ablation_overall.csv", "data/robustez_v0_2/robustness_by_profile.csv"),
     "No equiparar terciles de popularidad con grupos protegidos ni con artistas emergentes."),
    ("04", "Privacidad y explicabilidad", 15, "PARCIAL",
     ("docs/PRIVACIDAD_EXPLICABILIDAD.md", "tests/test_explain_privacy.py"),
     "Pendientes consentimientos documentados, política de retención y revisión de acceso a datos."),
    ("05", "Supervisión humana, seguridad y responsabilidad", 20, "PARCIAL",
     ("docs/informes/CONTROLES_ETICOS_SEGURIDAD.md", "tests/test_security_controls.py"),
     "Control local HMAC/token probado; faltan identidad individual y restauración externa."),
    ("06", "Impacto social y riesgos", 15, "PARCIAL",
     ("docs/matriz_riesgos.csv", "docs/informes/MATRIZ_RIESGOS_MITIGACION_V010.md"),
     "Hay 11 riesgos estimados; no se han medido consecuencias sociales reales."),
    ("07", "Medidas de mitigación y conclusión final", 15, "SÓLIDA",
     ("docs/informes/DICTAMEN_ETICO_V011.md", "side_b_ethics_closure.py"),
     "Mitigación reproducida; sin afirmar beneficio humano ni autorizar despliegue público."),
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_review(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    items = []
    for code, title, points, status, sources, limitations in CRITERIA:
        missing = [p for p in sources if not (root / p).is_file()]
        items.append({"id": code, "criterio": title, "peso": points,
                      "cobertura": "SIN_EVIDENCIA" if missing else status,
                      "fuentes": list(sources), "faltantes_documentales": missing,
                      "limitaciones": limitations})
    if sum(x["peso"] for x in items) != 100:
        raise ValueError("Los siete criterios deben sumar 100 puntos")
    if any(x["faltantes_documentales"] for x in items):
        raise ValueError("Faltan archivos básicos de la rúbrica")

    summary = build_report(root)
    ablation = _rows(root / "data/auditoria_v0_1/ablation_overall.csv")
    for row in ablation:
        if int(row["total_positions"]) != 60:
            raise ValueError("Cambio inesperado del experimento de 60 puestos")
    raw = _rows(root / "data/dataset_v1/side_b_dataset.csv")
    artist_ids = {r["artist_mbid"] for r in raw}
    recording_ids = {r["recording_mbid"] for r in raw}
    if len(raw) != 576 or len(recording_ids) != 576 or len(artist_ids) != 72:
        raise ValueError("No coincide la muestra histórica de SIDE B")
    groups = {}
    for row in raw:
        groups[row["sampling_genre"]] = groups.get(row["sampling_genre"], 0) + 1
    if len(groups) != 6 or any(v != 96 for v in groups.values()):
        raise ValueError("No coinciden los estratos históricos")
    recorded = sum(1 for row in raw if row["recording_popularity_status"] != "available")
    missing_genres = sum(1 for row in raw if not row["recording_genres"].strip())
    stats = summary["evidencia"]
    if stats["riesgos_total"] != 11 or stats["relatos_cualitativos_agregados"] != 9:
        raise ValueError("Desalineación entre la revisión y el dictamen ético")
    return {"formato": "SIDE_B_REVISION_RUBRICA_V012",
            "criterios": items,
            "cobertura_total_puntos": 100,
            "cantidad_criterios_con_evidencia": sum(not x["faltantes_documentales"] for x in items),
            "criterios_solidos": sum(x["cobertura"] == "SÓLIDA" for x in items),
            "criterios_parciales": sum(x["cobertura"] == "PARCIAL" for x in items),
            "muestra": {"grabaciones": len(raw), "artistas": len(artist_ids),
                        "generos": groups,
                        "popularidad_grabacion_ausente": recorded,
                        "genero_grabacion_ausente": missing_genres},
            "experimento": {"alta_A": stats["politicas"]["A"]["alta"],
                            "alta_C": stats["politicas"]["C"]["alta"],
                            "diferencia_puntos_porcentuales": stats["diferencia_puntos_porcentuales_A_C"]},
            "estudio_humano": {"relatos_agregados": 9,
                               "notas_pareadas_A_C_verificadas": False,
                               "consentimientos_documentados_verificados": False},
            "riesgos": {"total": stats["riesgos_total"], "alta_prioridad": stats["riesgos_prioridad_alta"]},
            "criterios_de_salida_pendientes": len(summary["criterios_de_salida"]),
            "dictamen": "APTO_PARA_DEFENSA_EXPLORATORIA_CON_LIMITACIONES",
            "despliegue_publico": "NO_AUTORIZADO",
            "paper": "PENDIENTE_DE_MAQUETACION_Y_BIBLIOGRAFIA",
            "nota": "Cobertura documental no equivale a nota, equidad demostrada o consentimiento obtenido."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisión reproducible de siete criterios SIDE B")
    parser.add_argument("--out", type=Path, help="Archivo JSON opcional para uso local")
    args = parser.parse_args()
    report = build_review()
    print(f"Rúbrica: {report['cantidad_criterios_con_evidencia']}/7 criterios con evidencia; "
          f"{report['criterios_solidos']} sólidos y {report['criterios_parciales']} parciales.")
    print(f"Muestra: {report['muestra']['artistas']} artistas, "
          f"{report['muestra']['grabaciones']} grabaciones; "
          f"A={report['experimento']['alta_A']}/60, C={report['experimento']['alta_C']}/60.")
    print(f"Pendientes: {report['criterios_de_salida_pendientes']} criterios de salida. "
          f"Despliegue público: {report['despliegue_publico']}.")
    if args.out:
        out = args.out.resolve()
        if out.exists() and out.is_dir():
            raise ValueError("--out debe apuntar a archivo JSON")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
