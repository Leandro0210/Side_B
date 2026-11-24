#!/usr/bin/env python3
"""SIDE B: participantes y calificaciones FICTICIOS para demostración del pipeline.

NO representan personas que escucharon canciones. Nombres inventados y notas [SIMULADO].
Los archivos se escriben solo en simulacion/ (fuera del repositorio Git).
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from validacion_humana_side_b import (
    KEY_FIELDS, RATING_FIELDS, analyze, build_key, read_csv, write_csv,
)

ROOT = Path(__file__).resolve().parent
RANKINGS = ROOT / 'data' / 'robustez_v0_2' / 'robustness_recommendations.csv'
DEFAULT_OUT = ROOT / 'simulacion' / 'participantes_ficticios_v07'
PROFILES = ('pop', 'rock')
# Son personajes de prueba, NO participantes reclutados, entrevistados ni encuestados.
FICTITIOUS_PERSONAS = (
    {'id': 'SIM01', 'nombre': 'Valeria Montes', 'sesgo_baja': 1, 'sesgo_media': 0, 'sesgo_alta': -1, 'estilo': 'pop'},
    {'id': 'SIM02', 'nombre': 'Mateo Rivas', 'sesgo_baja': -1, 'sesgo_media': 0, 'sesgo_alta': 1, 'estilo': 'rock'},
    {'id': 'SIM03', 'nombre': 'Lucía Paredes', 'sesgo_baja': 0, 'sesgo_media': 1, 'sesgo_alta': -1, 'estilo': 'pop'},
    {'id': 'SIM04', 'nombre': 'Diego Salinas', 'sesgo_baja': 1, 'sesgo_media': -1, 'sesgo_alta': 0, 'estilo': 'rock'},
    {'id': 'SIM05', 'nombre': 'Camila Soto', 'sesgo_baja': 0, 'sesgo_media': -1, 'sesgo_alta': 1, 'estilo': 'pop'},
)
GROUP_BIAS = {'low_observed': 'sesgo_baja', 'medium_observed': 'sesgo_media', 'high_observed': 'sesgo_alta'}


def generate(seed: int = 2026, rankings: Path = RANKINGS):
    """Devuelve registros y clave A/C; determinista y sin escritura."""
    key = [r for r in build_key(read_csv(rankings)) if r['profile'] in PROFILES]
    if set(r['profile'] for r in key) != set(PROFILES):
        raise ValueError('Faltan los perfiles de la demostración')
    ratings = []
    for persona in FICTITIOUS_PERSONAS:
        for profile in PROFILES:
            candidates = [r for r in key if r['profile'] == profile]
            rng = random.Random(f'SIDE_B_SYNTH_V07|{seed}|{persona["id"]}|{profile}')
            rng.shuffle(candidates)  # el formulario sigue siendo ciego a A/C
            for r in candidates:
                group = r['popularity_group']
                drift = rng.choice((-1, 0, 0, 0, 1))
                affinity = 1 if profile == persona['estilo'] and rng.random() < .3 else 0
                synthetic_score = max(1, min(5, 3 + persona[GROUP_BIAS[group]] + drift + affinity))
                # Familiaridad también inventada: no indica escucha, reconocimiento ni uso de la plataforma.
                familiarity_prob = {'low_observed': .2, 'medium_observed': .5, 'high_observed': .75}[group]
                familiar = 'yes' if rng.random() < familiarity_prob else 'no'
                ratings.append({
                    'participant_id': persona['id'], 'profile': profile, 'item_id': r['item_id'],
                    'artist_name': r['artist_name'], 'example_track': r['example_track'],
                    'musicbrainz_url': '', 'familiar_yes_no': familiar,
                    'relevance_1_5': synthetic_score,
                    'notes': '[SIMULADO] Puntuación y familiaridad generadas automáticamente; nadie evaluó la canción.',
                })
    return key, ratings


def summary_tables(seed: int = 2026, rankings: Path = RANKINGS):
    """Tabla de personajes ficticios y medias A/C calculadas, sin crear ficheros."""
    key, ratings = generate(seed, rankings)
    by_person = {}
    for row in ratings:
        by_person.setdefault((row['participant_id'], row['profile']), {})[row['item_id']] = int(row['relevance_1_5'])
    persona_lookup = {p['id']: p for p in FICTITIOUS_PERSONAS}
    individual = []
    for (pid, profile), values in sorted(by_person.items()):
        subset = [r for r in key if r['profile'] == profile]
        def average(which):
            selected = [values[r['item_id']] for r in subset if r[which + '_position'] != '']
            return sum(selected) / len(selected)
        a, c = average('A'), average('C')
        individual.append({'ID ficticio': pid, 'Nombre ficticio': persona_lookup[pid]['nombre'],
                           'Perfil': profile, 'Modelo A': round(a, 4), 'Modelo C': round(c, 4),
                           'C - A': round(c-a, 4), 'Origen': 'SIMULADO — NO HUMANO'})
    detail = pd.DataFrame(individual)
    profile_rows = []
    for profile in PROFILES:
        subset = detail.loc[detail['Perfil'] == profile]
        mean_a = float(subset['Modelo A'].mean())
        mean_c = float(subset['Modelo C'].mean())
        profile_rows.append({'Perfil': profile, 'Personajes ficticios': len(subset),
                             'Promedio A': round(mean_a, 4), 'Promedio C': round(mean_c, 4),
                             'Diferencia C - A': round(mean_c - mean_a, 4),
                             'Origen': 'SIMULACIÓN AUTOMÁTICA'})
    return detail, pd.DataFrame(profile_rows)


def export_demo(out: Path = DEFAULT_OUT, root: Path = ROOT, seed: int = 2026, rankings: Path = RANKINGS):
    root = Path(root).resolve()
    out = Path(out).resolve()
    if not out.is_relative_to(root / 'simulacion'):
        raise ValueError('Solo se permite escribir dentro de simulacion/; nunca en resultados humanos reales.')
    key, ratings = generate(seed, rankings)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'private' / 'evaluation_key.csv', KEY_FIELDS, key)
    for p in FICTITIOUS_PERSONAS:
        file = out / 'ratings' / f'{p["id"]}.csv'
        write_csv(file, RATING_FIELDS, [r for r in ratings if r['participant_id'] == p['id']])
    # Se usa el analizador original y su barrera anti-mezcla; nunca modo real.
    analyze(SimpleNamespace(out=str(out), simulated=True))
    with (out / 'personajes_FICTICIOS.csv').open('w', encoding='utf-8') as f:
        f.write('participant_id;nombre_inventado;origen\n')
        for p in FICTITIOUS_PERSONAS:
            f.write(f'{p["id"]};{p["nombre"]};SIMULADO_NO_HUMANO\n')
    manifest = {
        'tipo': 'SIDE_B_SIMULACION_SINTETICA_V07',
        'evidencia_humana': False, 'personas_reales': 0,
        'participantes': len(FICTITIOUS_PERSONAS), 'filas_calificadas': len(ratings),
        'perfiles': list(PROFILES), 'semilla': seed, 'uso': 'PRUEBA TECNICA Y DEMOSTRACION SOLAMENTE',
        'metodo': 'Calificaciones enteras 1-5 según preferencias ficticias y ruido seudorrandómico; sin escucha.',
    }
    (out / 'MANIFIESTO_NO_HUMANO.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description='Generar solo evaluaciones FICTICIAS para SIDE B')
    parser.add_argument('--seed', type=int, default=2026, help='Semilla para la demostración determinista')
    args = parser.parse_args()
    result = export_demo(seed=args.seed)
    print('\nPERSONAS FICTICIAS: ' + ', '.join(p['nombre'] for p in FICTITIOUS_PERSONAS))
    print(f'{result["filas_calificadas"]} valoraciones SINTÉTICAS guardadas en {DEFAULT_OUT.relative_to(ROOT)}')
    print('NO citar como encuesta, entrevista, estudio humano ni resultado empírico.')


if __name__ == '__main__':
    main()
