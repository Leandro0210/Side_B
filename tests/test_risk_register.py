"""El registro de riesgos documenta mitigaciones sin declarar riesgos eliminados."""
from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from side_b_risk_register import evaluate_risks, load_risks, risk_markdown, VALID_CHECKS

ROOT = Path(__file__).resolve().parents[1]


class RiskRegisterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.risks = load_risks(ROOT)
        cls.real = evaluate_risks(ROOT)

    def test_matrix_priorities_and_responsibles(self):
        self.assertEqual(len(self.risks), 11)
        self.assertEqual({r["id"] for r in self.risks}, {f"R{i:02d}" for i in range(1, 12)})
        self.assertEqual([r["prioridad_estimada"] for r in self.risks],
                         sorted([r["prioridad_estimada"] for r in self.risks], reverse=True))
        self.assertTrue(all(r["responsable_rol"] and r["accion_pendiente"] for r in self.risks))
        self.assertTrue(all(r["prioridad_estimada"] == r["probabilidad_1_5"] *
                            r["impacto_1_5"] for r in self.risks))

    def test_real_report_cannot_approve_deployment_or_fairness(self):
        report = self.real
        self.assertFalse(report["aprobado_despliegue_publico"])
        self.assertEqual(report["resumen"]["total"], 11)
        self.assertEqual(report["resumen"]["cerrados"], 0)
        self.assertTrue(all(not r["riesgo_cerrado"] for r in report["riesgos"]))
        self.assertTrue(all(r["estado_verificacion"] in
                            {"PARCIAL", "PENDIENTE", "FALLA"} for r in report["riesgos"]))
        self.assertIn("NO autorizado", risk_markdown(report))

    def test_paired_human_metrics_not_presented_as_verified(self):
        r = {row["id"]: row for row in self.real["riesgos"]}
        self.assertNotEqual(r["R06"]["estado_verificacion"], "RESUELTO")
        self.assertNotEqual(r["R11"]["estado_verificacion"], "RESUELTO")
        self.assertTrue(r["R11"]["accion_pendiente"])

    def test_failed_control_is_not_hidden(self):
        diagnostic = {"checks": [{"id": check, "status": "OK"} for check in VALID_CHECKS]}
        diagnostic["checks"] = [
            {"id": row["id"], "status": "FALLA" if row["id"] == "supervision_hmac" else "OK"}
            for row in diagnostic["checks"]
        ]
        report = evaluate_risks(ROOT, diagnostic=diagnostic)
        mapped = {row["id"]: row for row in report["riesgos"]}
        self.assertEqual(mapped["R04"]["estado_verificacion"], "FALLA")
        self.assertEqual(mapped["R09"]["estado_verificacion"], "FALLA")
        self.assertFalse(report["aprobado_despliegue_publico"])
        self.assertEqual(mapped["R07"]["estado_verificacion"], "PENDIENTE")

    def test_even_all_green_checks_cannot_close_risks(self):
        diagnostic = {"checks": [{"id": check, "status": "OK"} for check in VALID_CHECKS]}
        report = evaluate_risks(ROOT, diagnostic=diagnostic)
        self.assertEqual(report["resumen"]["cerrados"], 0)
        self.assertFalse(report["aprobado_despliegue_publico"])
        self.assertTrue(all(r["estado_verificacion"] != "RESUELTO" for r in report["riesgos"]))

    def test_corrupt_priority_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            shutil.copytree(ROOT / "docs", temp / "docs")
            risk_file = temp / "docs" / "matriz_riesgos.csv"
            with risk_file.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            rows[0]["prioridad_estimada"] = "1"
            with risk_file.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "inconsistente"):
                load_risks(temp)

    def test_unrecognized_evidence_check_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            shutil.copytree(ROOT / "docs", temp / "docs")
            risk_file = temp / "docs" / "matriz_riesgos.csv"
            with risk_file.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            rows[0]["verificaciones"] = "inventado"
            with risk_file.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "desconocida"):
                load_risks(temp)

    def test_no_personal_identifiers_in_public_risk_table(self):
        content = (ROOT / "docs" / "matriz_riesgos.csv").read_text(encoding="utf-8")
        self.assertNotIn("participante_id", content.lower())
        for name in ("Sebastian", "Alejandro", "Peña", "Jona", "Liz", "Alexia", "Sofia"):
            self.assertNotIn(name, content)


if __name__ == "__main__":
    unittest.main()
