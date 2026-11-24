"""Pruebas de las reglas de dictamen y trazabilidad sin respuestas personales."""
import csv
import tempfile
import unittest
from pathlib import Path
from shutil import copyfile

from side_b_ethics_closure import ROOT, build_report


class EthicsClosureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in (
            "data/auditoria_v0_1/ablation_overall.csv",
            "data/estudio_v08/resumen_grupal.csv",
            "docs/matriz_riesgos.csv",
        ):
            dest = self.root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            copyfile(ROOT / relative, dest)

    def test_summary_reflects_existing_results(self):
        report = build_report(self.root)
        self.assertEqual(report["evidencia"]["politicas"]["A"]["alta"], 36)
        self.assertEqual(report["evidencia"]["politicas"]["C"]["alta"], 18)
        self.assertEqual(report["evidencia"]["diferencia_puntos_porcentuales_A_C"], 30.0)
        self.assertEqual(report["evidencia"]["relatos_cualitativos_agregados"], 9)

    def test_no_automatic_release_or_closed_gates(self):
        report = build_report(self.root)
        self.assertEqual(report["despliegue_publico"], "NO_AUTORIZADO")
        self.assertEqual(len(report["criterios_de_salida"]), 7)
        self.assertTrue(all(g["estado"] == "PENDIENTE" for g in report["criterios_de_salida"]))
        self.assertTrue(all(not g["aprobacion_automatica"] for g in report["criterios_de_salida"]))

    def test_reject_inconsistent_ablations(self):
        path = self.root / "data/auditoria_v0_1/ablation_overall.csv"
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
            fields = list(rows[0])
        rows[0]["positions_high_observed"] = "100"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaises(ValueError):
            build_report(self.root)

    def test_reject_inconsistent_risk_priority(self):
        path = self.root / "docs/matriz_riesgos.csv"
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
            fields = list(rows[0])
        rows[0]["prioridad_estimada"] = "0"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaises(ValueError):
            build_report(self.root)

    def test_reject_absent_aggregated_reports(self):
        path = self.root / "data/estudio_v08/resumen_grupal.csv"
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
            fields = list(rows[0])
        rows[0]["participantes"] = "0"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaises(ValueError):
            build_report(self.root)


if __name__ == "__main__":
    unittest.main()
