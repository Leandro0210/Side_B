"""Check that this report is aggregate, concise, and cannot be used as per-song evidence."""
import csv
from pathlib import Path
import unittest
from app_gradio import _study_summary, _evaluation_note
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

class TestExploratoryStudy(unittest.TestCase):
    def test_nine_anonymous_reports(self):
        data=_study_summary()
        self.assertEqual(int(data['Relatos'].sum()),9)
        self.assertEqual(len(data),5)
        self.assertFalse(any(k.lower() in ';'.join(data.columns).lower() for k in ('nombre', 'correo', 'religion', 'sexo')))

    def test_no_individual_ratings_or_ids_published(self):
        with (ROOT/'data/estudio_v08/resumen_grupal.csv').open(encoding='utf-8') as f:
            text=f.read()
        self.assertNotIn('participant_id',text)
        self.assertNotIn('relevance_1_5',text)
        self.assertNotIn('P01',text)

    def test_local_evaluation_not_inferred_from_qualitative(self):
        note=_evaluation_note(pd.DataFrame())
        self.assertIn('no permiten comparar',note)

if __name__=='__main__':unittest.main()
