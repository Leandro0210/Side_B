"""Validación de cobertura documental y figuras del próximo manuscrito."""
import tempfile
import unittest
from pathlib import Path
from shutil import copyfile

from side_b_rubric_review import CRITERIA, ROOT, build_review
from generar_figuras_paper import make_assets, table_data, validate_assets


class ReviewTests(unittest.TestCase):
    def test_seven_weights_and_evidence(self):
        report=build_review(ROOT)
        self.assertEqual(len(report['criterios']),7)
        self.assertEqual(report['cobertura_total_puntos'],100)
        self.assertEqual(report['cantidad_criterios_con_evidencia'],7)
        self.assertEqual(report['criterios_solidos'],4)
        self.assertEqual(report['criterios_parciales'],3)
        self.assertEqual(sum(x[2] for x in CRITERIA),100)

    def test_exact_sample_and_exposure(self):
        r=build_review(ROOT)
        self.assertEqual(r['muestra']['grabaciones'],576)
        self.assertEqual(r['muestra']['artistas'],72)
        self.assertEqual(len(r['muestra']['generos']),6)
        self.assertEqual(r['experimento']['alta_A'],36)
        self.assertEqual(r['experimento']['alta_C'],18)
        self.assertEqual(r['experimento']['diferencia_puntos_porcentuales'],30.0)

    def test_cannot_claim_human_significance_or_public_release(self):
        r=build_review(ROOT)
        self.assertFalse(r['estudio_humano']['notas_pareadas_A_C_verificadas'])
        self.assertFalse(r['estudio_humano']['consentimientos_documentados_verificados'])
        self.assertEqual(r['despliegue_publico'],'NO_AUTORIZADO')
        self.assertEqual(r['criterios_de_salida_pendientes'],7)

    def test_table_counts_and_per_profile_eligibility(self):
        data=table_data(ROOT)
        self.assertEqual(len(data['overall']),4)
        self.assertEqual(len(data['profiles']),6)
        self.assertEqual(sum(r['alta'] for r in data['overall']),93)
        self.assertEqual(next(r for r in data['profiles'] if r['perfil']=='latin')['alta_elegible'],0)
        self.assertEqual(next(r for r in data['profiles'] if r['perfil']=='pop')['alta_top10_A'],9)

    def test_figures_are_reproducible_and_high_res(self):
        with tempfile.TemporaryDirectory() as td:
            generated=make_assets(ROOT,Path(td))
            tested=validate_assets(ROOT,Path(td))
            self.assertEqual(generated,tested)
            self.assertEqual(len(tested['figuras']),3)

    def test_review_rejects_missing_required_dataset(self):
        # Protege frente a falta de evidencias sin modificar el repositorio real.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for _,_,_,_,sources,_ in CRITERIA:
                for rel in sources:
                    source=ROOT/rel
                    dest=root/rel
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    if source.is_file():copyfile(source,dest)
            with self.assertRaises(FileNotFoundError):
                build_review(root)


if __name__=='__main__':
    unittest.main()
