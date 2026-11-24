#!/usr/bin/env python3
"""SIDE B: prepara formularios ciegos y analiza valoraciones de relevancia independientes.
Solo usa la biblioteca estándar de Python. No entrena modelos ni modifica datos originales.
"""
import argparse
import csv
import hashlib
import random
import json
from collections import defaultdict
from pathlib import Path

REPRESENTATION = 'solo_etiquetas_artista'
POLICIES = {'A_pop25_sin_tope', 'C_pop05_sin_tope'}
RATING_FIELDS = ['participant_id', 'profile', 'item_id', 'artist_name', 'example_track',
                 'musicbrainz_url', 'familiar_yes_no', 'relevance_1_5', 'notes']
KEY_FIELDS = ['profile', 'item_id', 'artist_mbid', 'artist_name', 'example_track',
              'popularity_group', 'A_position', 'C_position']


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=',;\t').delimiter
        except csv.Error:
            delimiter = ';'
        return list(csv.DictReader(f, delimiter=delimiter))


def write_csv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def build_key(rankings):
    need = {'representation','profile','policy','position','artist_mbid','artist_name','example_track','group'}
    if not rankings or not need.issubset(rankings[0]):
        raise ValueError('Faltan columnas en robustness_recommendations.csv')
    items = {}
    for r in rankings:
        if r['representation'] != REPRESENTATION or r['policy'] not in POLICIES:
            continue
        k = (r['profile'], r['artist_mbid'])
        item_id = 'SB' + hashlib.sha256(('|'.join(k)).encode('utf-8')).hexdigest()[:10].upper()
        if k not in items:
            items[k] = {'profile':r['profile'], 'item_id':item_id, 'artist_mbid':r['artist_mbid'],
                        'artist_name':r['artist_name'], 'example_track':r['example_track'],
                        'popularity_group':r['group'], 'A_position':'', 'C_position':''}
        col = 'A_position' if r['policy'].startswith('A_') else 'C_position'
        if items[k][col]:
            raise ValueError('Artista repetido dentro de una misma lista de recomendaciones')
        items[k][col] = int(r['position'])
    if not items:
        raise ValueError('No hay recomendaciones A/C con representación solo_etiquetas_artista')
    key = sorted(items.values(), key=lambda r:(r['profile'],r['item_id']))
    profiles = {r['profile'] for r in key}
    for profile in profiles:
        for col in ('A_position','C_position'):
            positions = sorted(int(r[col]) for r in key if r['profile']==profile and r[col]!='')
            if positions != list(range(1, len(positions)+1)):
                raise ValueError(f'Posiciones inválidas para {profile} / {col}: {positions}')
    return key


def dataset_urls(dataset):
    result = {}
    for r in dataset:
        a = r.get('artist_mbid','')
        t = r.get('track_name','').strip().casefold()
        url = r.get('musicbrainz_url','').strip()
        if a and t and url:
            result.setdefault((a,t),url)
    return result


def prepare(args):
    key = build_key(read_csv(args.rankings))
    out = Path(args.out)
    selected = args.profiles if args.profiles != ['all'] else sorted({r['profile'] for r in key})
    absent = set(selected)-{r['profile'] for r in key}
    if absent:
        raise ValueError(f'Perfiles desconocidos: {sorted(absent)}')
    pid = args.participant.strip().upper()
    if not pid or any(ch not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for ch in pid):
        raise ValueError('Usa un identificador anónimo, p. ej. P01')
    urls = dataset_urls(read_csv(args.dataset)) if args.dataset else {}
    shuffled = []
    for profile in selected:
        rows = [r for r in key if r['profile']==profile]
        rng = random.Random(f'{pid}|{profile}|SIDE_B_2026')
        rng.shuffle(rows)
        for r in rows:
            shuffled.append({'participant_id':pid, 'profile':profile, 'item_id':r['item_id'],
                             'artist_name':r['artist_name'], 'example_track':r['example_track'],
                             'musicbrainz_url':urls.get((r['artist_mbid'],r['example_track'].strip().casefold()),''),
                             'familiar_yes_no':'', 'relevance_1_5':'', 'notes':''})
    write_csv(out/'private'/'evaluation_key.csv', KEY_FIELDS, key)
    target = out/'ratings'/f'{pid}.csv'
    if target.exists() and not args.overwrite:
        raise FileExistsError(f'{target} ya existe; no sobrescribir valoraciones. Usa un ID nuevo.')
    write_csv(target, RATING_FIELDS, shuffled)
    print(f'Plantilla anónima: {target} ({len(shuffled)} filas, {len(selected)} perfiles)')
    print(f'Clave SOLO para el investigador: {out / "private" / "evaluation_key.csv"}')
    print('IMPORTANTE: No mostrar la carpeta private/ a los participantes.')


def analyze(args):
    out = Path(args.out)
    keypath = out/'private'/'evaluation_key.csv'
    if not keypath.exists():
        raise FileNotFoundError(f'Falta la clave: {keypath}. Ejecuta prepare primero.')
    key = {(r['profile'],r['item_id']):r for r in read_csv(keypath)}
    per_person = []
    valid_scores = {}
    files = sorted((out/'ratings').glob('*.csv'))
    simulated_mode = getattr(args, 'simulated', False)
    if not files:
        print('Aún no hay archivos de valoración.'); return
    for file in files:
        rows = read_csv(file)
        if not rows: continue
        synthetic_flags = [(r.get('notes') or '').strip().startswith('[SIMULADO]') for r in rows]
        if any(synthetic_flags) and not all(synthetic_flags):
            raise ValueError(f'{file.name}: mezcla de filas simuladas y no simuladas')
        if any(synthetic_flags) and not simulated_mode:
            raise ValueError(f'{file.name}: respuestas sintéticas detectadas. No analizarlas como humanas. Usa --simulated en una carpeta de simulación separada.')
        if simulated_mode and not all(synthetic_flags):
            raise ValueError(f'{file.name}: modo --simulated exige que todas las filas se identifiquen como [SIMULADO]')
        pid = file.stem.upper()
        groups = defaultdict(list)
        for r in rows:
            if r.get('participant_id','').strip().upper() != pid:
                raise ValueError(f'{file.name}: participant_id no coincide con el nombre del archivo')
            k = (r.get('profile',''),r.get('item_id',''))
            if k not in key:
                raise ValueError(f'{file.name}: item_id desconocido {k}')
            raw = r.get('relevance_1_5','').strip()
            value = None
            if raw:
                try: value = int(raw)
                except ValueError: raise ValueError(f'{file.name}: calificación debe ser número entero 1-5')
                if value not in range(1,6):
                    raise ValueError(f'{file.name}: calificación fuera de rango 1-5')
            groups[k[0]].append((k,value))
        for profile, group in groups.items():
            expected = {k for k in key if k[0]==profile}
            seen = [x[0] for x in group]
            if len(seen)!=len(set(seen)):
                raise ValueError(f'{file.name}: item_id duplicado para {profile}')
            if set(seen)!=expected or any(v is None for _,v in group):
                print(f'{file.name}/{profile}: incompleto; excluido de la comparación pareada')
                continue
            values = {k[1]:v for k,v in group}
            record = {'participant_id':pid,'profile':profile,'candidates_rated':len(values)}
            for prefix,col in (('A','A_position'),('C','C_position')):
                policy_values = [values[r['item_id']] for r in key.values()
                                 if r['profile']==profile and r[col] != '']
                record[f'{prefix}_n']=len(policy_values)
                record[f'{prefix}_mean_relevance']=round(sum(policy_values)/len(policy_values),4)
            record['C_minus_A']=round(record['C_mean_relevance']-record['A_mean_relevance'],4)
            per_person.append(record)
            valid_scores[(pid,profile)] = values
    write_csv(out/'analysis'/'per_participant_profile.csv',
              ['participant_id','profile','candidates_rated','A_n','A_mean_relevance','C_n','C_mean_relevance','C_minus_A'],per_person)
    aggregates=[]
    for profile in sorted({r['profile'] for r in per_person}):
        subset=[r for r in per_person if r['profile']==profile]
        avg=lambda field:sum(r[field] for r in subset)/len(subset)
        aggregates.append({'profile':profile,'complete_participants':len(subset),
                           'mean_A':round(avg('A_mean_relevance'),4),
                           'mean_C':round(avg('C_mean_relevance'),4),
                           'mean_paired_difference_C_minus_A':round(avg('C_minus_A'),4)})
    write_csv(out/'analysis'/'summary_by_profile.csv',
              ['profile','complete_participants','mean_A','mean_C','mean_paired_difference_C_minus_A'],aggregates)
    if simulated_mode:
        (out/'analysis'/'SIMULADO_NO_EVIDENCIA_HUMANA.txt').write_text('RESULTADOS SINTÉTICOS DE PRUEBA. NO SON VALORACIONES DE SERES HUMANOS. NO UTILIZAR COMO EVIDENCIA EMPÍRICA.\n',encoding='utf-8')
        print('*** SIMULACIÓN: las puntuaciones son inventadas para probar el pipeline, NO son resultados humanos. ***')
    print(f'Valoraciones completas: {len(per_person)} combinaciones persona-perfil.')
    print(f'Resumen: {out / "analysis" / "summary_by_profile.csv"}')
    if not per_person: print('Todavía no hay calificaciones completas; NO hay resultado empírico humano.')
    else:
        for r in aggregates:
            print(f"{r['profile']}: n={r['complete_participants']}, A={r['mean_A']}, C={r['mean_C']}, C-A={r['mean_paired_difference_C_minus_A']}")
        print('Descriptivo: no demuestra causalidad ni significación estadística; no extrapolar a la población.')


def main():
    parser = argparse.ArgumentParser(description='SIDE B - Evaluación humana ciega A/C')
    sub = parser.add_subparsers(dest='command',required=True)
    p = sub.add_parser('prepare',help='Preparar formulario ciego')
    p.add_argument('--rankings',required=True)
    p.add_argument('--dataset',help='CSV para agregar enlaces MusicBrainz cuando existan')
    p.add_argument('--out',default=r'data/validacion_humana_v0_3')
    p.add_argument('--participant',required=True)
    p.add_argument('--profiles',nargs='+',default=['pop','rock'])
    p.add_argument('--overwrite',action='store_true',help='Reemplazar hoja existente sin preservar valoraciones')
    q = sub.add_parser('analyze',help='Analizar formularios ya completados')
    q.add_argument('--out',default=r'data/validacion_humana_v0_3')
    q.add_argument('--simulated',action='store_true',help='Habilita exclusivamente evaluación de datos rotulados [SIMULADO]')
    args = parser.parse_args()
    if args.command=='prepare':prepare(args)
    else:analyze(args)

if __name__=='__main__':main()
