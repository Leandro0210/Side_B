"""Guardas del diagnóstico ético reproducible, sin datos personales ni red."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from validar_integral_side_b import (run_audit, markdown_report, _integrity,
                                      _human_evidence, _release_surface)

ROOT = Path(__file__).resolve().parents[1]


class TestIntegralAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_audit(ROOT)

    def test_full_reproduction_and_hmac(self):
        self.assertTrue(self.report["technical_checks_pass"], self.report["checks"])
        self.assertEqual(len(self.report["scenarios"]), 48)
        self.assertEqual([c["status"] for c in self.report["checks"][:5]], ["OK"]*5)
        self.assertIn("supervision_hmac", [c["id"] for c in self.report["checks"]])

    def test_descriptive_exposure_and_no_claim_of_fairness(self):
        exposure={x["politica"]: x for x in self.report["exposure"]}
        self.assertEqual(exposure["A"]["alta_popularidad"],36)
        self.assertEqual(exposure["C"]["alta_popularidad"],18)
        self.assertEqual(exposure["A"]["posiciones"],60)
        self.assertFalse(self.report["public_deployment_approved"])
        self.assertFalse(self.report["fairness_certified"])
        self.assertFalse(self.report["human_preference_validated"])
        self.assertIn("no demuestra justicia",markdown_report(self.report))

    def test_integrity_failure_is_rejected(self):
        with patch("validar_integral_side_b.verify",return_value=(["MODIFICADO: dataset.csv"],5)):
            with self.assertRaisesRegex(AssertionError,"MODIFICADO"):
                _integrity(ROOT)

    def test_published_release_has_no_personal_ratings(self):
        # El checkout público no lleva los agregados; los CSV individuales son privados.
        if not (ROOT / "simulacion" / "validacion_humana").exists():
            status, note = _human_evidence(ROOT)
            self.assertEqual(status, "PENDIENTE")
            self.assertIn("no se deducen resultados",note)
        self.assertNotIn("rating_1_5", '\n'.join(x["detail"] for x in self.report["checks"]))

    def test_known_publication_paths_are_checked(self):
        class GitResult:
            stdout=b"app_gradio.py\0data/supervision/revisiones_demo.csv\0"
        with patch("validar_integral_side_b.subprocess.run",return_value=GitResult()):
            with self.assertRaisesRegex(AssertionError,"sensibles"):
                _release_surface(ROOT)

    def test_offline_publication_scan_never_claims_ok(self):
        with patch("validar_integral_side_b.subprocess.run",side_effect=FileNotFoundError):
            status, detail = _release_surface(ROOT)
        self.assertEqual(status, "PENDIENTE")
        self.assertIn("Git", detail)

    def test_human_evidence_missing_never_becomes_real(self):
        with tempfile.TemporaryDirectory() as temp:
            status, detail=_human_evidence(Path(temp))
        self.assertEqual(status,"PENDIENTE")
        self.assertIn("no se deducen",detail)

    def test_integral_summary_does_not_expose_secrets(self):
        content=markdown_report(self.report)
        self.assertIn("NO",content)
        self.assertIn("SHA-256",content)
        self.assertNotIn("SIDE_B_VALIDACION_SOLO_LOCAL_2026_DOS",content)


if __name__=="__main__":
    unittest.main()
