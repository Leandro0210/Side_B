"""Verifica que los CSV de investigación conservan sus hashes documentados."""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/'docs'/'manifiesto_evidencias_sha256.json'

def verify(manifest=MANIFEST, root=ROOT):
    data=json.loads(Path(manifest).read_text(encoding='utf-8'))
    failures=[]
    for path,sha in data['files'].items():
        full=Path(root)/path
        if not full.is_file():
            failures.append(f'FALTA: {path}')
        elif hashlib.sha256(full.read_bytes()).hexdigest()!=sha:
            failures.append(f'MODIFICADO: {path}')
    return failures, len(data['files'])

if __name__=='__main__':
    errors,total=verify()
    print(f'SIDE B | archivos verificados: {total-len(errors)}/{total}')
    for item in errors: print(item)
    raise SystemExit(1 if errors else 0)
