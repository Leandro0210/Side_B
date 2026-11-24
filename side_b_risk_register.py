"""SIDE B — trazabilidad de riesgos y mitigaciones, sin alterar datos musicales.

Cada estado corresponde a verificaciones técnicas existentes o tareas aún abiertas.
Una comprobación correcta NO implica que un riesgo haya desaparecido.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED_COLUMNS = (
    "id", "riesgo", "afectados", "probabilidad_1_5", "impacto_1_5",
    "prioridad_estimada", "mitigacion", "estado", "responsable_rol",
    "verificaciones", "alcance_control", "evidencia", "accion_pendiente",
)
VALID_CHECKS = frozenset({
    "integridad_sha256", "catalogo", "reproduccion_48_escenarios",
    "consistencia_ablacion", "supervision_hmac", "privacidad_publicacion",
    "calidad_grabaciones_ilustrativas", "evidencia_humana",
})


def load_risks(root: Path = ROOT) -> list[dict]:
    """Comprueba coherencia, prioridades, rutas locales y referencias a controles."""
    root = Path(root).resolve()
    path = root / "docs" / "matriz_riesgos.csv"
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise ValueError("La matriz de riesgos no tiene el esquema documentado")
        records = list(reader)
    if not records:
        raise ValueError("No se encontraron riesgos")
    seen = set()
    for row in records:
        rid = row["id"]
        if not rid.startswith("R") or not rid[1:].isdigit() or rid in seen:
            raise ValueError(f"Identificador repetido o inválido: {rid}")
        seen.add(rid)
        if any(not row[key].strip() for key in (
            "riesgo", "afectados", "mitigacion", "estado", "responsable_rol", "accion_pendiente"
        )):
            raise ValueError(f"Riesgo sin descripción, responsable o tarea: {rid}")
        try:
            p, i, score = (int(row[k]) for k in
                           ("probabilidad_1_5", "impacto_1_5", "prioridad_estimada"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Prioridad no numérica: {rid}") from exc
        if not (1 <= p <= 5 and 1 <= i <= 5 and score == p * i):
            raise ValueError(f"Probabilidad, impacto o prioridad inconsistente: {rid}")
        row["probabilidad_1_5"], row["impacto_1_5"] = p, i
        row["prioridad_estimada"] = score
        if row["alcance_control"] not in ("parcial", "documental"):
            raise ValueError(f"Alcance de control no documentado: {rid}")
        checks = row["verificaciones"].split("|") if row["verificaciones"] else []
        if any(check not in VALID_CHECKS for check in checks):
            raise ValueError(f"Verificación desconocida: {rid}")
        if row["alcance_control"] == "documental" and row["verificaciones"] and rid == "R07":
            raise ValueError("R07 no tiene prueba técnica de representatividad")
        evidence = Path(row["evidencia"])
        if (evidence.is_absolute() or ".." in evidence.parts or
                not (root / evidence).is_file()):
            raise ValueError(f"Ruta de evidencia ausente o insegura: {rid}")
        row["severidad"] = "Alta" if score >= 15 else "Media" if score >= 8 else "Baja"
    return sorted(records, key=lambda r: (-r["prioridad_estimada"], r["id"]))


def evaluate_risks(root: Path = ROOT, diagnostic: dict | None = None) -> dict:
    """Evalúa cobertura técnica; jamás convierte una prueba en certificación ética."""
    records = load_risks(root)
    if diagnostic is None:
        from validar_integral_side_b import run_audit
        diagnostic = run_audit(Path(root))
    statuses = {c["id"]: c["status"] for c in diagnostic.get("checks", [])}
    result = []
    for row in records:
        checks = row["verificaciones"].split("|") if row["verificaciones"] else []
        found = [statuses.get(check, "PENDIENTE") for check in checks]
        if any(value == "FALLA" for value in found):
            state = "FALLA"
        elif not checks or row["alcance_control"] == "documental":
            state = "PENDIENTE"
        elif all(value == "OK" for value in found):
            state = "PARCIAL"  # controles técnicos comprobados, riesgo residual abierto
        elif "OK" in found:
            state = "PARCIAL"
        else:
            state = "PENDIENTE"
        evidence_checks = [{"id": check, "estado": statuses.get(check, "PENDIENTE")}
                           for check in checks]
        result.append({**row, "estado_verificacion": state,
                       "controles": evidence_checks,
                       "riesgo_cerrado": False})
    counts = {key: sum(r["estado_verificacion"] == key for r in result)
              for key in ("PARCIAL", "PENDIENTE", "FALLA")}
    return {
        "formato": "SIDE_B_REGISTRO_RIESGOS_V010",
        "riesgos": result,
        "resumen": {"total": len(result), **counts,
                    "alto_prioridad": sum(r["severidad"] == "Alta" for r in result),
                    "cerrados": 0},
        "aprobado_despliegue_publico": False,
        "nota": "Estimaciones cualitativas; pruebas técnicas no equivalen a riesgo eliminado."
    }


def risk_markdown(report: dict) -> str:
    summary = report["resumen"]
    lines = [
        "### Riesgos y medidas de mitigación",
        f"**{summary['total']} riesgos identificados** · "
        f"{summary['alto_prioridad']} de prioridad alta · "
        f"{summary['PARCIAL']} controles parciales · "
        f"{summary['PENDIENTE']} pendientes · {summary['FALLA']} fallos técnicos.",
        "**Despliegue público: NO autorizado.** Ningún riesgo se considera cerrado "
        "solo porque pasó una prueba técnica.", "",
        "| ID | Prioridad inicial | Estado de control | Acción por completar |",
        "|---|---:|---|---|",
    ]
    for row in report["riesgos"]:
        action = row["accion_pendiente"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {row['id']} | {row['prioridad_estimada']}/25 "
                     f"({row['severidad']}) | {row['estado_verificacion']} | {action} |")
    lines += ["", "*Probabilidad × impacto expresa un juicio preliminar, "
              "no una probabilidad medida ni una reducción cuantificada del daño.*"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico local de riesgos SIDE B")
    parser.add_argument("--out", type=Path, help="Directorio opcional para guardar reporte JSON/Markdown")
    args = parser.parse_args()
    report = evaluate_risks()
    print(risk_markdown(report))
    if args.out:
        out = args.out.resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "riesgos_v010.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "riesgos_v010.md").write_text(risk_markdown(report) + "\n", encoding="utf-8")
        print(f"\nReporte guardado en {out}")
    return int(report["resumen"]["FALLA"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
