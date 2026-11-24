"""Asegura que la demostración ficticia nunca se atribuya a personas reales."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import hashlib
import json
import unittest

from simular_participantes import (FICTITIOUS_PERSONAS, RANKINGS, export_demo,
                                   generate, summary_tables)
from validacion_humana_side_b import analyze, read_csv


class TestFictionalPersonas(unittest.TestCase):
    def test_deterministic_five_names_and_140_ratings(self):
        key, first = generate(seed=2026)
        self.assertEqual(len(key), 28)  # pop 15 / rock 13
        self.assertEqual(len(first), 140)
        self.assertEqual(first, generate(seed=2026)[1])
        self.assertEqual(len({p['nombre'] for p in FICTITIOUS_PERSONAS}), 5)
        self.assertEqual({r['participant_id'] for r in first}, {p['id'] for p in FICTITIOUS_PERSONAS})
        self.assertTrue(all(r['notes'].startswith('[SIMULADO]') for r in first))
        self.assertTrue(all(1 <= int(r['relevance_1_5']) <= 5 for r in first))
        self.assertFalse(any(r['participant_id'] == 'P01' for r in first))
        self.assertTrue(all(r['profile'] in {'pop', 'rock'} for r in first))

    def test_individual_preferences_differ_and_remain_named_fiction(self):
        detailed, summary = summary_tables()
        self.assertEqual(len(detailed), 10)
        self.assertEqual(len(summary), 2)
        self.assertEqual(set(detailed['Nombre ficticio']), {p['nombre'] for p in FICTITIOUS_PERSONAS})
        self.assertEqual(set(detailed['Origen']), {'SIMULADO — NO HUMANO'})
        # No presentar una simple hoja de cinco copias idénticas.
        self.assertGreater(len(set(detailed.loc[detailed['Perfil'] == 'pop', 'Modelo A'])), 1)
        self.assertGreater(len(set(detailed.loc[detailed['Perfil'] == 'rock', 'Modelo C'])), 1)

    def test_export_never_writes_real_folder_and_simulated_only_analyzer(self):
        initial_hash = hashlib.sha256((Path(__file__).resolve().parents[1]/'data'/'dataset_v1'/'side_b_dataset.csv').read_bytes()).hexdigest()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError,'Solo se permite'):
                export_demo(root/'data'/'validacion_humana_v0_3', root=root, rankings=RANKINGS)
            out=root/'simulacion'/'demostracion'
            manifest=export_demo(out, root=root, rankings=RANKINGS)
            self.assertFalse(manifest['evidencia_humana'])
            self.assertEqual(manifest['personas_reales'],0)
            self.assertEqual(manifest['filas_calificadas'],140)
            self.assertEqual(len(list((out/'ratings').glob('SIM*.csv'))),5)
            self.assertEqual(len(read_csv(out/'ratings'/'SIM01.csv')),28)
            self.assertIn('SINTÉTICOS', (out/'analysis'/'SIMULADO_NO_EVIDENCIA_HUMANA.txt').read_text())
            self.assertEqual(len(read_csv(out/'analysis'/'per_participant_profile.csv')),10)
            self.assertTrue((out/'MANIFIESTO_NO_HUMANO.json').is_file())
            with self.assertRaisesRegex(ValueError,'sintéticas'):
                analyze(SimpleNamespace(out=str(out), simulated=False))
            manifest_disk=json.loads((out/'MANIFIESTO_NO_HUMANO.json').read_text())
            self.assertEqual(manifest_disk['personas_reales'],0)
        final_hash = hashlib.sha256((Path(__file__).resolve().parents[1]/'data'/'dataset_v1'/'side_b_dataset.csv').read_bytes()).hexdigest()
        self.assertEqual(initial_hash,final_hash)

if __name__=='__main__':
    unittest.main()
