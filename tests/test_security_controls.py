"""Pruebas específicas de intervención humana y preservación de la evidencia."""
from pathlib import Path
import csv
import tempfile
import unittest
from unittest.mock import patch

from side_b_dashboard_core import SideBEngine, POLICIES

ROOT=Path(__file__).resolve().parents[1]
SECRET='SIDE_B_PRUEBAS_SUPERVISION_2026_ABC'


class TestSecurityControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.engine=SideBEngine(ROOT,review_token=SECRET)
        self.engine.audit_log_path=Path(self.temp.name)/'revisiones.csv'
        self.profile='rock'
        self.policy=list(POLICIES)[2]
        self.representation='artist_only'
        self.first=str(self.engine.recommendations(self.profile,self.policy,self.representation,10)[0].iloc[0].artist_mbid)
        self.dataset_digest=self.engine.dataset_path.read_bytes()

    def tearDown(self):
        self.assertEqual(self.dataset_digest,self.engine.dataset_path.read_bytes())
        self.temp.cleanup()

    def action(self, decision='Bloquear en demo',reason='La grabación requiere revisión antes de mostrarse.', token=SECRET):
        return self.engine.review('AUDITOR_DEMO',self.profile,self.policy,self.representation,
                                  self.first,decision,reason,token)

    def test_default_read_only_rejects_write(self):
        locked=SideBEngine(ROOT,review_token='')
        locked.audit_log_path=self.engine.audit_log_path
        with self.assertRaises(PermissionError):
            locked.review('AUDITOR_DEMO',self.profile,self.policy,self.representation,
                          self.first,'Bloquear en demo','Motivo documentado para el bloqueo',SECRET)
        self.assertFalse(self.engine.audit_log_path.exists())

    def test_bad_password_must_not_write(self):
        with self.assertRaises(PermissionError):self.action(token='wrong')
        self.assertFalse(self.engine.audit_log_path.exists())

    def test_block_restore_and_signed_chain(self):
        self.action()
        self.assertIn(self.first,self.engine.blocked_for(self.profile,self.policy,self.representation))
        self.assertNotIn(self.first,set(self.engine.recommendations(self.profile,self.policy,self.representation,10,True)[0].artist_mbid))
        self.action('Aprobar','Se verificó que el registro puede aparecer nuevamente.')
        self.assertNotIn(self.first,self.engine.blocked_for(self.profile,self.policy,self.representation))
        r=self.engine.audit_records()
        self.assertEqual(len(r),2)
        self.assertEqual(r.iloc[1].previous_mac,r.iloc[0].entry_mac)
        self.assertEqual(r.iloc[0].event_id,'1')

    def test_request_review_does_not_block_ranking(self):
        self.action('Solicitar revisión','El título es ambiguo, solicita una revisión humana.')
        self.assertNotIn(self.first,self.engine.blocked_for(self.profile,self.policy,self.representation))

    def test_modified_entry_fails_integrity_check(self):
        self.action()
        content=self.engine.audit_log_path.read_text(encoding='utf-8-sig')
        self.engine.audit_log_path.write_text(content.replace('Bloquear en demo','Aprobar'),encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError,'integridad'):
            self.engine.audit_records()
        with self.assertRaises(ValueError):
            self.engine.blocked_for(self.profile,self.policy,self.representation)
        with self.assertRaises(ValueError):
            self.action('Aprobar','Prueba de sobrescritura ilegítima rechazada.')

    def test_history_requires_correct_key(self):
        self.action()
        with self.assertRaises(PermissionError): self.engine.history_for('incorrecta')
        self.assertEqual(len(self.engine.history_for(SECRET)),1)

    def test_reject_csv_formulas_controls_and_invalid_choices(self):
        for reason in ['=HYPERLINK("x")','@SUM(1)','Motivo con salto\nde línea']:
            with self.subTest(reason=reason),self.assertRaises(ValueError):self.action(reason=reason)
        with self.assertRaises(ValueError):
            self.engine.review('AUDITOR_DEMO',self.profile,self.policy,self.representation,
                               self.first,'INVENTAR_DECISION','Motivo justificado de prueba',SECRET)
        self.assertFalse(self.engine.audit_log_path.exists())

    def test_does_not_modify_experiment_data(self):
        source=ROOT/'data'/'auditoria_v0_1'/'ablation_overall.csv'
        original=source.read_bytes()
        self.action()
        self.assertEqual(original,source.read_bytes())

    def test_cannot_verify_with_different_secret(self):
        self.action()
        other=SideBEngine(ROOT,review_token='UN_TOKEN_ALTERNATIVO_LARGO_09876')
        other.audit_log_path=self.engine.audit_log_path
        with self.assertRaisesRegex(ValueError,'integridad'): other.audit_records()

if __name__=='__main__':unittest.main()
