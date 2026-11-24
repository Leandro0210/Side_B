"""Figuras y tablas reproducibles para el futuro paper de SIDE B.

Fuente: CSV de la ablación 4 políticas y 6 perfiles. No usa valoraciones humanas
ni atribuye significación estadística a diferencias entre posiciones del ranking.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ("data/auditoria_v0_1/ablation_overall.csv",
           "data/auditoria_v0_1/ablation_by_profile.csv")
POLICIES = ("A_pop25_sin_tope", "B_pop25_con_tope",
            "C_pop05_sin_tope", "D_pop05_con_tope")
GROUPS = (("low", "Baja"), ("medium", "Media"), ("high", "Alta"))


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def table_data(root: Path = ROOT) -> dict:
    overall = rows(root / SOURCES[0])
    profile = rows(root / SOURCES[1])
    if [r["policy"] for r in overall] != list(POLICIES):
        raise ValueError("Orden o contenido inesperado de las políticas")
    data = []
    for r in overall:
        n = int(r["total_positions"])
        vals = [int(r[f"positions_{g}_observed"]) for g, _ in GROUPS]
        if n != 60 or sum(vals) != 60:
            raise ValueError("Inconsistencia de exposición")
        data.append({"politica": r["policy"][0], "posiciones": n, "baja": vals[0],
                     "media": vals[1], "alta": vals[2],
                     "porcentaje_alta": round(vals[2]*100/n, 1),
                     "similitud_proxy": float(r["mean_similarity_proxy"])})
    profiles = sorted(set(x["profile"] for x in profile))
    if len(profiles) != 6 or len(profile) != 24:
        raise ValueError("No coincide el experimento por perfil (6 × 4)")
    pairs = []
    for name in profiles:
        a, c = (next(x for x in profile if x["profile"] == name and x["policy"] == p)
                for p in (POLICIES[0], POLICIES[2]))
        if int(a["recommended_n"]) != 10 or int(c["recommended_n"]) != 10:
            raise ValueError("Top-K distinto de 10")
        if a["eligible_high_observed"] != c["eligible_high_observed"] or a["eligible_total"] != c["eligible_total"]:
            raise ValueError("Distinto conjunto elegible al comparar A y C")
        pairs.append({"perfil": name, "elegibles": int(a["eligible_total"]),
                      "alta_elegible": int(a["eligible_high_observed"]),
                      "alta_top10_A": int(a["topk_high_observed"]),
                      "alta_top10_C": int(c["topk_high_observed"])})
    return {"overall": data, "profiles": pairs}


def _csv(path: Path, fieldnames: tuple[str, ...], items: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)


def make_assets(root: Path = ROOT, out: Path | None = None) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    root = Path(root).resolve()
    out = Path(out).resolve() if out else root / "docs" / "paper_assets"
    out.mkdir(parents=True, exist_ok=True)
    data = table_data(root)
    policies = data["overall"]
    profiles = data["profiles"]
    figures = ["figura_01_exposicion_politicas.png", "figura_02_popularidad_por_perfil.png",
               "figura_03_similitud_proxy.png"]
    plt.rcParams.update({"font.size": 10})
    # Fig. 1: categorías mutuamente excluyentes, 60 puestos por política.
    fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
    base = np.zeros(4)
    for group, label in GROUPS:
        vals = np.array([x[{"low":"baja","medium":"media","high":"alta"}[group]] for x in policies])
        bars = ax.bar([x["politica"] for x in policies], vals, bottom=base, label=label)
        ax.bar_label(bars, labels=[str(int(v)) for v in vals], label_type="center")
        base += vals
    ax.set(ylabel="Puestos Top-10 en seis perfiles (total: 60)", ylim=(0, 68),
           title="Exposición por nivel de popularidad y política")
    ax.legend(title="Popularidad observada", ncol=3, loc="upper center")
    ax.set_xlabel("Política de ranking")
    fig.savefig(out / figures[0], dpi=300)
    plt.close(fig)

    # Fig. 2: cuota del tercil alto por perfil, control de elegibilidad.
    fig, ax = plt.subplots(figsize=(10, 5.3), layout="constrained")
    x = np.arange(len(profiles))
    w = 0.28
    av = [100*p["alta_top10_A"]/10 for p in profiles]
    cv = [100*p["alta_top10_C"]/10 for p in profiles]
    ev = [100*p["alta_elegible"]/p["elegibles"] for p in profiles]
    a = ax.bar(x-w/2, av, width=w, label="A: pop. 25 %")
    c = ax.bar(x+w/2, cv, width=w, label="C: pop. 5 %")
    ax.plot(x, ev, linestyle=":", marker="o", color="0.3", label="Elegibles del tercil alto")
    ax.set_xticks(x, [p["perfil"].title() for p in profiles], rotation=15)
    ax.set(ylabel="Porcentaje de artistas de popularidad alta (%)", ylim=(0, 105),
           title="Exposición alta A/C frente a elegibilidad de cada perfil")
    ax.legend(loc="upper center", ncol=3)
    fig.savefig(out / figures[1], dpi=300)
    plt.close(fig)

    # Fig. 3: similitud proxy, no agrado de oyentes.
    fig, ax = plt.subplots(figsize=(8.8, 4.7), layout="constrained")
    bars = ax.bar([r["politica"] for r in policies], [r["similitud_proxy"] for r in policies])
    ax.bar_label(bars, labels=[f'{r["similitud_proxy"]:.3f}' for r in policies], padding=3)
    ax.set(title="Similitud media por política (métrica proxy TF-IDF)",
           ylabel="Similitud de metadatos (0–1)", ylim=(0, .42))
    ax.set_xlabel("Política de ranking")
    fig.savefig(out / figures[2], dpi=300)
    plt.close(fig)

    _csv(out / "tabla_01_exposicion_politicas.csv", tuple(policies[0].keys()), policies)
    _csv(out / "tabla_02_comparacion_perfil.csv", tuple(profiles[0].keys()), profiles)
    report = {
        "formato": "SIDE_B_PAPER_ASSETS_V012",
        "archivos_fuente": {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in SOURCES},
        "figuras": figures,
        "tablas": ["tabla_01_exposicion_politicas.csv", "tabla_02_comparacion_perfil.csv"],
        "notas": "Figuras ilustran posiciones del ranking y similitud proxy; no respuestas humanas.",
        "reproducir": "python generar_figuras_paper.py"
    }
    (out / "manifiesto_figuras.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


def validate_assets(root: Path = ROOT, out: Path | None = None) -> dict:
    root = Path(root).resolve()
    folder = Path(out).resolve() if out else root / "docs" / "paper_assets"
    manifest = json.loads((folder / "manifiesto_figuras.json").read_text(encoding="utf-8"))
    if manifest["formato"] != "SIDE_B_PAPER_ASSETS_V012":
        raise ValueError("Manifiesto de figuras inválido")
    if any(hashlib.sha256((root / p).read_bytes()).hexdigest()!=sha
           for p,sha in manifest["archivos_fuente"].items()):
        raise ValueError("Las figuras no corresponden a los CSV de evidencia vigentes")
    for fig in manifest["figuras"]:
        blob=(folder/fig).read_bytes()
        if not blob.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Figura PNG ausente o inválida: " + fig)
        width=int.from_bytes(blob[16:20],"big")
        if width<1800:raise ValueError("Resolución insuficiente: " + fig)
    if any(not (folder/t).is_file() for t in manifest["tablas"]):
        raise ValueError("Tabla ausente")
    if len(table_data(root)["overall"]) != 4:
        raise ValueError("No hay cuatro políticas")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Gráficos científicos reproducibles de SIDE B")
    parser.add_argument("--out", type=Path, help="Carpeta para publicar gráficos y tablas")
    parser.add_argument("--check", action="store_true", help="Verificar los archivos existentes sin modificar")
    args = parser.parse_args()
    result = validate_assets(ROOT,args.out) if args.check else make_assets(ROOT,args.out)
    print(f"Figuras verificadas: {len(result['figuras'])}; tablas: {len(result['tablas'])}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
