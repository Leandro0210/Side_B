"""SIDE B | Interfaz simple de Gradio para la auditoría ética musical.

Presenta primero las tareas que entiende un oyente, dejando el análisis avanzado
bajo acordeones. La fuente científica se mantiene intacta.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import gradio as gr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from side_b_dashboard_core import (
    GROUPS, GROUP_LABELS, POLICIES, REPRESENTATIONS, SideBEngine
)
from validar_integral_side_b import run_audit, markdown_report

ROOT = Path(__file__).resolve().parent
ENGINE = SideBEngine(ROOT)
POL_A, POL_B, POL_C, POL_D = list(POLICIES)
REPRESENTATION = list(REPRESENTATIONS)[0]  # Solo etiquetas del artista
PROFILE_OPTIONS = [(name.title() if name != "hip hop" else "Hip-hop", name) for name in ENGINE.profiles]

GROUP_COLORS = {"low_observed": "#159d85", "medium_observed": "#ca922f", "high_observed": "#8671c6"}

CSS = """
.gradio-container {max-width: 1080px !important; margin: 0 auto !important;}
#side-hero {padding: 30px 32px; border-radius: 20px; background: linear-gradient(115deg,#101f2f,#173c44);
            color:#fff !important; margin-bottom:14px;}
#side-hero h1 {font-size:2.55rem; color:#fff !important; margin:4px 0 4px; letter-spacing:.06em;}
#side-hero .eyebrow {font-size:.78rem; color:#9fe8d7; letter-spacing:.16em; font-weight:700;}
#side-hero p {color:#d2e2e7 !important; font-size:1rem; margin:0;}
#side-hero .subnote {color:#a9bfca !important; font-size:.85rem; margin-top:8px;}
#steps {display:grid; grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:7px 0 16px;}
#steps > div {padding:12px 16px; background:var(--block-background-fill, #f3f5f7);
               border:1px solid var(--border-color-primary, #e3e5e8);border-radius:12px;font-size:.89rem;}
#steps span {display:inline-block; width:24px; height:24px; margin-right:6px; border-radius:50%;
             background:#157b70;color:white;text-align:center;line-height:24px;font-weight:700;}
.sb-section-title {font-size:1.15rem;font-weight:750;margin:6px 0;}
.sb-muted {font-size:.88rem;opacity:.85;}
.sb-cards {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;}
.sb-artist {border-radius:14px;border:1px solid var(--border-color-primary, #e2e5e9);
             padding:15px;background:var(--block-background-fill, white);min-width:0;}
.sb-artist .sb-rank {color:#159d85;font-size:.8rem;font-weight:700;}
.sb-artist .sb-name {font-size:1.08rem;font-weight:750;margin:4px 0;overflow-wrap:anywhere;}
.sb-artist .sb-song {opacity:.77;font-size:.84rem;overflow-wrap:anywhere;}
.sb-chip {font-size:.72rem;padding:3px 8px;border-radius:999px;border:1px solid currentColor;white-space:nowrap;}
.sb-low {color:#138971}.sb-medium {color:#ab7b28}.sb-high {color:#8567b9}
.sb-summary-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:10px 0;}
.sb-stat {padding:14px;border:1px solid var(--border-color-primary, #e2e5e9);
          border-radius:12px;background:var(--block-background-fill, white);}
.sb-stat strong {display:block;font-size:1.65rem;line-height:1.2;margin:2px 0;}
.sb-stat small {opacity:.78;}
.sb-footnote {opacity:.77;font-size:.83rem;margin-top:9px;}
@media(max-width:700px) {#steps,.sb-cards,.sb-summary-grid{grid-template-columns:1fr;}
    #side-hero{padding:20px;} #side-hero h1{font-size:1.95rem;}}
"""


def _policy_simple(label: str) -> str:
    return POL_A if label == "Priorizar artistas conocidos" else POL_C


def _exposure_figure(ranked: pd.DataFrame, pool: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.2, 3.3), layout="constrained")
    if ranked.empty:
        ax.text(.5,.5,"No hay candidatos para este estilo",ha="center",va="center");ax.axis("off")
        return fig
    x = np.arange(3)
    take = [int((ranked.pop_group == g).sum()) for g in GROUPS]
    eligible = [int((pool.pop_group == g).sum()) for g in GROUPS]
    ax.bar(x-.19, eligible, .35, color="#aebbc3", label="Disponibles")
    ax.bar(x+.19, take, .35, color=[GROUP_COLORS[g] for g in GROUPS], label="Recomendados")
    ax.set_xticks(x,["Baja","Media","Alta"])
    ax.set_ylabel("Artistas")
    ax.set_title("¿A quién está mostrando el algoritmo?",fontsize=12)
    ax.legend(frameon=False,fontsize=9);ax.spines[['top','right']].set_visible(False)
    return fig


def _comparison_figure(frame: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.4, 3.35), layout="constrained")
    if frame.empty:
        ax.axis("off"); return fig
    policies=list(dict.fromkeys(frame["Política"].tolist()))
    x=np.arange(3)
    for j, pol in enumerate(policies):
        numbers=[int(frame.loc[(frame["Política"]==pol)&(frame["Popularidad"]==GROUP_LABELS[g]),"Apariciones"].sum()) for g in GROUPS]
        ax.bar(x+(-.19 if j==0 else .19),numbers,.36,label=f"Modelo {pol}")
    ax.set_xticks(x,["Baja","Media","Alta"]);ax.set_ylabel("Recomendaciones")
    ax.set_title("Exposición por nivel de popularidad",fontsize=12)
    ax.legend(frameon=False,fontsize=9);ax.spines[['top','right']].set_visible(False)
    return fig


def _overall_figure():
    data=ENGINE.simple_audit()
    fig,ax=plt.subplots(figsize=(8,3.45),layout="constrained")
    x=np.arange(len(data));width=.24
    for j, group in enumerate(GROUPS):
        ax.bar(x+(j-1)*width, data[f"positions_{group}"].astype(float).to_numpy(),width,
               color=GROUP_COLORS[group],label=GROUP_LABELS[group])
    ax.set_xticks(x,[str(p).split("_")[0] for p in data.policy]);ax.set_ylabel("Posiciones en Top-10")
    ax.set_title("Resultados de las cuatro políticas (6 perfiles)",fontsize=12)
    ax.legend(ncol=3,frameon=False,fontsize=9);ax.spines[['top','right']].set_visible(False)
    return fig


def _card_html(r: pd.Series) -> str:
    name=escape(str(r.artist_name))
    audit=ENGINE.illustration(str(r.artist_mbid))
    title=escape(str(audit["display_example"]))
    group=str(r.pop_group)
    g_label=GROUP_LABELS.get(group,"Sin grupo")
    g_cls={"low_observed":"sb-low","medium_observed":"sb-medium","high_observed":"sb-high"}.get(group,"")
    # Únicamente mostramos alertas importantes; el detalle queda en Auditoría.
    if audit["display_quality"] == "sin_ejemplo":
        title="⚠ Sin canción ilustrativa revisable en la muestra"
    elif "no coinciden exactamente" in audit["display_reason"]:
        title += " · ⚠ género de esta grabación sin correspondencia confirmada"
    return (f"<div class='sb-artist'><div class='sb-rank'>#{int(r.position)} · Artista recomendado</div>"
            f"<div class='sb-name'>{name}</div><div class='sb-song'>Ejemplo del catálogo: {title}</div>"
            f"<div style='margin-top:11px'><span class='sb-chip {g_cls}'>Popularidad {g_label.lower()}</span></div></div>")


def _discover(profile: str, preference: str, representation_name: str, top_k: int):
    policy = _policy_simple(preference)
    representation=REPRESENTATIONS[representation_name]
    ranked,pool,relaxed=ENGINE.recommendations(profile,policy,representation,int(top_k),apply_review_blocks=True)
    if ranked.empty:
        return "<div class='sb-artist'>No se encontraron artistas compatibles con este estilo.</div>", "No hay recomendaciones para este filtro.", _exposure_figure(ranked,pool),gr.Dropdown(choices=[],value=None)
    cards="<div class='sb-cards'>"+"".join(_card_html(r) for _,r in ranked.iterrows())+"</div>"
    names={"Priorizar artistas conocidos":"Modelo A · da más peso a la popularidad",
           "Descubrir música menos conocida":"Modelo C · reduce el peso de la popularidad"}
    info=(f"**{len(ranked)} artistas recomendados** de {len(pool)} compatibles. "
          f"{names[preference]}. Las canciones son ejemplos del catálogo, no una garantía del género ni de escucha verificada.")
    if len(ranked)<top_k:
        info+=f" Solo existen {len(pool)} candidatos compatibles: no rellenamos la lista artificialmente."
    if relaxed:
        info+=" Se relajó el límite por grupo al generar la lista."
    choices=[(f"#{int(r.position)} {r.artist_name}",str(r.artist_mbid)) for _,r in ranked.iterrows()]
    return cards,info,_exposure_figure(ranked,pool),gr.Dropdown(choices=choices,value=choices[0][1])


def _explain(profile: str, preference: str, representation_name: str, top_k: int, artist_id: str):
    if not artist_id:
        return "Elige un artista para mostrar su explicación."
    try:
        item=ENGINE.explain_candidate(profile,_policy_simple(preference),
                 REPRESENTATIONS[representation_name],artist_id,int(top_k),True)
    except ValueError:
        return "La lista cambió. Pulsa **Ver recomendaciones** otra vez."
    tags=", ".join(escape(t) for t in item["matched_tags"]) or "No hay etiqueta exacta; coincidencia calculada por TF-IDF"
    shown=ENGINE.illustration(artist_id)
    note=escape(shown["display_reason"])
    song=escape(shown["display_example"])
    changed=" Se conservó el registro original del experimento." if shown["example_changed"] else ""
    return (f"### {escape(item['artist_name'])} · Puesto #{item['rank']}\n\n"
            f"**Coincidencia con el perfil {escape(profile)}:** {tags}.\n\n"
            f"**Desglose de puntuación:** similitud {item['similarity']:.4f} × "
            f"{item['similarity_weight']:.0%} = {item['similarity_contribution']:.4f}; "
            f"popularidad percentil {item['pop_percentile']:.4f} × "
            f"{item['popularity_weight']:.0%} = {item['popularity_contribution']:.4f}. "
            f"**Total: {item['total_score']:.4f}**.\n\n"
            f"**Grupo:** {item['pop_group']} · **candidatos elegibles:** {item['population']}. "
            f"{'Se aplicó un tope por popularidad. ' if item['has_group_cap'] else ''}"
            f"{'El tope se relajó por falta de candidatos. ' if item['cap_relaxed'] else ''}\n\n"
            f"**Ejemplo visible del catálogo:** {song}. Estado: `{shown['display_quality']}`. "
            f"Nota de calidad: {note}.{changed} "
            "La similitud se calcula con etiquetas **del artista**, no con audio ni gustos comprobados.\n\n"
            f"*{item['note']}*")


def _compare(profile: str, left: str, right: str,representation_name: str, top_k: int):
    m,t,detail,note=ENGINE.group_comparison(profile,left,right,REPRESENTATIONS[representation_name],int(top_k))
    names={left:left.split(" · ")[0],right:right.split(" · ")[0]}
    blocks=[]
    for idx,pol in enumerate((left,right)):
        code=names[pol]
        counts={g:int(m.loc[(m['Política']==code)&(m['Popularidad']==GROUP_LABELS[g]),'Apariciones'].sum()) for g in GROUPS}
        score=t.iloc[0]["Similitud A" if idx==0 else "Similitud B"]
        blocks.append(f"<div class='sb-stat'><small>Modelo {escape(code)}</small>"
                      f"<strong>{counts[GROUPS[0]]} <span style='font-size:.75rem'>/ {int(top_k)}</span></strong>"
                      f"<small>Artistas de popularidad baja · similitud {score}</small></div>")
    available=int(t.iloc[0].Elegibles)
    center=f"<div class='sb-stat'><small>Mismo conjunto de candidatos</small><strong>{available}</strong><small>Artistas compatibles con {escape(profile)}</small></div>"
    summary="<div class='sb-summary-grid'>"+blocks[0]+blocks[1]+center+"</div>"
    explanation=("**Cómo leerlo:** los dos modelos parten de los mismos artistas elegibles. "
                 "La gráfica compara cuántas posiciones recibieron los grupos de popularidad baja, media y alta. "
                 "Eso mide exposición, **no demuestra por sí solo justicia ni preferencias reales**.")
    if available<top_k:
        explanation+=f" En este perfil solo hay **{available} candidatos** para {top_k} posiciones."
    return summary,_comparison_figure(m),explanation,m,detail


def _evaluation_note(real: pd.DataFrame) -> str:
    """Solo mostrar evidencia individual cuando está disponible localmente."""
    if real.empty:
        return ("**Calificaciones por canción:** no hay un resumen local autorizado. "
                "Los nueve relatos cualitativos se muestran agrupados abajo, pero "
                "no permiten comparar numéricamente la relevancia de los modelos A/C.")
    return ("**Calificaciones por canción:** se encontró un resumen local de formularios completos. "
            "Considéralo por separado de los relatos cualitativos y revisa consentimiento "
            "y trazabilidad antes de usarlo como evidencia de investigación.")


def _eval_tables():
    real = ENGINE.evaluation()
    return real, _evaluation_note(real)


def _study_summary() -> pd.DataFrame:
    path = ROOT / "data" / "estudio_v08" / "resumen_grupal.csv"
    table = pd.read_csv(path, sep=";")
    if table["participantes"].sum() != 9 or len(table) != 5:
        raise ValueError("El resumen agregado de nueve relatos no coincide con su manifiesto")
    return table.rename(columns={"grupo_interpretativo":"Patrón de recepción",
                                 "participantes":"Relatos",
                                 "descripcion":"Qué expresaron"})


def _integral_diagnostic():
    return markdown_report(run_audit(ROOT))


def _eligible_dropdown(profile: str, representation_name: str, policy: str):
    representation=REPRESENTATIONS[representation_name]
    ranked,pool,_=ENGINE.recommendations(profile,policy,representation,10)
    top_ids=set(ranked.artist_mbid)
    choices=[(f"Top-10 #{int(r.position)} · {r.artist_name}",str(r.artist_mbid))
             for r in ranked.itertuples(index=False)]
    choices.extend((f"Otro elegible · {r.artist_name}",str(r.artist_mbid))
                   for r in pool.loc[~pool.artist_mbid.isin(top_ids)].sort_values('artist_name').itertuples(index=False))
    return gr.Dropdown(choices=choices,value=choices[0][1] if choices else None)


def _oversight_save(alias,profile,policy,representation_name,artist_id,decision,reason,access_token):
    """Autorizar la acción antes de mostrar historial; nunca devolver la clave al cliente."""
    try:
        msg=ENGINE.review(alias,profile,policy,REPRESENTATIONS[representation_name],artist_id,decision,reason,access_token)
        history=ENGINE.history_for(access_token)
    except (ValueError,OSError,PermissionError) as e:
        msg=f"No se pudo guardar: {escape(str(e))}"
        history=pd.DataFrame()
    return msg,history,gr.update(value="")


def _oversight_history(access_token):
    try:
        history=ENGINE.history_for(access_token)
        return (f"Registro verificado: {len(history)} últimos eventos visibles. "
                "Las firmas comprueban modificaciones internas, pero no sustituyen un respaldo externo."),history,gr.update(value="")
    except (ValueError,OSError,PermissionError) as e:
        return f"No se pudo verificar el historial: {escape(str(e))}",pd.DataFrame(),gr.update(value="")


def _risk_table():
    return pd.read_csv(ROOT / "docs" / "matriz_riesgos.csv").fillna("")


def _robustness(profile,representation_name):
    source=pd.read_csv(ROOT / "data" / "robustez_v0_2" / "robustness_by_profile.csv")
    representation="solo_etiquetas_artista" if REPRESENTATIONS[representation_name]=="artist_only" else "original_con_muestreo"
    filtered=source.loc[(source.profile==profile)&(source.representation==representation)].copy()
    return pd.DataFrame({
        "Modelo":filtered.policy.str.split('_').str[0],
        "Elegibles":filtered.eligible_total,
        "Recomendaciones":filtered.recommended_n,
        "Pop. baja":filtered.topk_low_observed,
        "Pop. media":filtered.topk_medium_observed,
        "Pop. alta":filtered.topk_high_observed,
        "Similitud (aprox.)":filtered.mean_similarity_proxy.round(3),
    })


def create_app():
    with gr.Blocks(title="SIDE B · Descubre lo que el algoritmo oculta") as app:
        gr.HTML("""<section id='side-hero'>
            <div class='eyebrow'>SIDE B · PROYECTO ACADÉMICO</div>
            <h1>La música tiene otro lado.</h1>
            <p>Descubre artistas y compara cómo una IA decide quién merece ser escuchado.</p>
            <p class='subnote'>72 artistas · 576 grabaciones · Auditoría de popularidad</p>
        </section><div id='steps'>
            <div><span>1</span> Descubre artistas</div>
            <div><span>2</span> Compara dos algoritmos</div>
            <div><span>3</span> Entiende los resultados</div>
        </div>""")
        with gr.Tabs():
            with gr.Tab("🎧 Descubrir música"):
                gr.Markdown("### ¿Qué música quieres descubrir?\nElige un estilo y explora una lista de artistas. No necesitas entender cómo funciona el algoritmo.")
                with gr.Row():
                    genre=gr.Dropdown(PROFILE_OPTIONS,value="rock",label="Estilo musical",scale=2)
                    mode=gr.Radio(["Descubrir música menos conocida","Priorizar artistas conocidos"],
                                  value="Descubrir música menos conocida",label="¿Cómo quieres explorar?",scale=3)
                with gr.Accordion("Opciones avanzadas",open=False):
                    repr1=gr.Dropdown(list(REPRESENTATIONS),value=REPRESENTATION,label="Origen de etiquetas")
                    top1=gr.Slider(3,15,step=1,value=10,label="Cantidad de artistas")
                discover_button=gr.Button("Ver recomendaciones",variant="primary")
                discover_note=gr.Markdown()
                artist_cards=gr.HTML()
                with gr.Accordion("¿Por qué aparecen estos artistas?",open=False):
                    selected=gr.Dropdown(label="Artista")
                    explain_button=gr.Button("Mostrar explicación")
                    explanation=gr.Markdown()
                    gr.Markdown("La recomendación se calcula **por artista**. La grabación mostrada es un ejemplo y puede requerir revisión.")
                with gr.Accordion("Ver datos de exposición",open=False):
                    chart_discover=gr.Plot()
                    gr.Markdown("**Baja, media y alta** son niveles *relativos* de popularidad dentro de nuestra muestra; no categorías de talento ni de artistas emergentes.")
                discover_button.click(_discover,[genre,mode,repr1,top1],
                                      [artist_cards,discover_note,chart_discover,selected])
                explain_button.click(_explain,[genre,mode,repr1,top1,selected],explanation)
                app.load(_discover,[genre,mode,repr1,top1],[artist_cards,discover_note,chart_discover,selected])

            with gr.Tab("⚖️ Comparar algoritmos"):
                gr.Markdown("### ¿Qué cambia cuando la IA presta menos atención a la fama?\nCompara **A** (más peso de popularidad) con **C** (menos peso de popularidad).")
                cmp_genre=gr.Dropdown(PROFILE_OPTIONS,value="pop",label="Estilo musical")
                with gr.Accordion("Cambiar modelos o ajustes",open=False):
                    with gr.Row():
                        left=gr.Dropdown(list(POLICIES),value=POL_A,label="Primer modelo")
                        right=gr.Dropdown(list(POLICIES),value=POL_C,label="Segundo modelo")
                    with gr.Row():
                        repr2=gr.Dropdown(list(REPRESENTATIONS),value=REPRESENTATION,label="Origen de etiquetas")
                        top2=gr.Slider(3,15,step=1,value=10,label="Cantidad de artistas")
                cmp_button=gr.Button("Comparar modelos",variant="primary")
                cmp_summary=gr.HTML()
                cmp_chart=gr.Plot()
                cmp_note=gr.Markdown()
                with gr.Accordion("Ver tablas y resultados individuales",open=False):
                    compare_table=gr.Dataframe(label="Conteos de exposición",interactive=False)
                    compare_detail=gr.Dataframe(label="Listas que produjo cada modelo",interactive=False)
                cmp_button.click(_compare,[cmp_genre,left,right,repr2,top2],
                                 [cmp_summary,cmp_chart,cmp_note,compare_table,compare_detail])
                app.load(_compare,[cmp_genre,left,right,repr2,top2],
                         [cmp_summary,cmp_chart,cmp_note,compare_table,compare_detail])

            with gr.Tab("🔎 Auditoría ética"):
                gr.Markdown("### Lo que SIDE B ha descubierto\nAnalizamos si la popularidad determina quién aparece en las recomendaciones.")
                gr.HTML("""<div class='sb-summary-grid'>
                    <div class='sb-stat'><small>Catálogo experimental</small><strong>72</strong><small>artistas de 6 grupos musicales</small></div>
                    <div class='sb-stat'><small>Modelo A · popularidad alta</small><strong>36/60</strong><small>posiciones en los seis perfiles</small></div>
                    <div class='sb-stat'><small>Modelo C · popularidad alta</small><strong>18/60</strong><small>posiciones en los seis perfiles</small></div>
                </div>""")
                gr.Plot(value=_overall_figure())
                gr.Markdown("**Qué significa:** al reducir el peso de popularidad cambió la exposición en esta muestra. "
                            "**Qué NO significa:** que el modelo C sea definitivamente justo o que los oyentes lo prefieran. "
                            "Los perfiles son categorías musicales, no personas reales.")
                with gr.Accordion("Calidad del catálogo · canciones ilustrativas",open=False):
                    overview=ENGINE.illustration_audit
                    no_song=int((overview["display_quality"]=="sin_ejemplo").sum())
                    changes=int(overview["example_changed"].sum())
                    gr.Markdown(f"**{len(overview)} artistas revisados** · "
                                f"**{changes} ejemplos cambiados/no disponibles** · "
                                f"**{no_song} artistas sin grabación ilustrativa apta**. "
                                "Estas son comprobaciones de metadatos, no verificación por escucha. "
                                "El ranking por artista y la evidencia histórica no se modificaron.")
                    issues=ENGINE.illustration_issues()
                    columns={"artist_name":"Artista", "original_example":"Grabación histórica",
                             "display_example":"Ejemplo propuesto", "display_quality":"Estado",
                             "display_reason":"Observación"}
                    gr.Dataframe(value=issues[list(columns)].rename(columns=columns),
                                 label="Casos que necesitan revisión",interactive=False)
                    gr.Markdown("**Importante:** un artista puede coincidir con el género del perfil sin que "
                                "todas sus grabaciones lo hagan. Las respuestas históricas describen "
                                "otros ejemplos y no se recalculan retroactivamente. "
                                "Detalles: `docs/informes/CALIDAD_CATALOGO_V09.md`.")
                with gr.Accordion("Estudio exploratorio de participantes",open=False):
                    gr.Markdown("**9 relatos recibidos:** resumen temático anónimo de preferencias "
                                "transmitidas por el responsable del proyecto. "
                                "No hay 28 calificaciones verificadas por persona ni se dispone de "
                                "consentimientos documentados en este repositorio.")
                    gr.Dataframe(label="Resumen cualitativo agregado · 9 relatos",value=_study_summary(),interactive=False)
                    gr.Markdown("**Interpretación:** hay diferencias de afinidad por género y por idioma; "
                                "la muestra no permite generalizar ni calcular una preferencia cuantitativa A/C. "
                                "Metodología: `docs/informes/ESTUDIO_EXPLORATORIO_V08.md`.")
                    with gr.Accordion("Calificaciones por canción (solo archivo local autorizado)",open=False):
                        evaluation_state=gr.Markdown(value=_evaluation_note(ENGINE.evaluation()))
                        real=gr.Dataframe(label="Agregados de formularios completos",value=ENGINE.evaluation(),interactive=False)
                        gr.Button("Actualizar calificaciones locales").click(_eval_tables,outputs=[real,evaluation_state])
                with gr.Accordion("Validación integral reproducible · v0.6",open=False):
                    gr.Markdown("Ejecuta las verificaciones técnicas **sin modificar el dataset**. "
                                "El resultado distingue los controles comprobados de los "
                                "aspectos éticos que siguen pendientes. No certifica justicia ni autoriza despliegue público.")
                    integral_button=gr.Button("Comprobar SIDE B",variant="secondary")
                    integral_result=gr.Markdown()
                    integral_button.click(_integral_diagnostic,outputs=integral_result)
                with gr.Accordion("Supervisión humana (demostración)",open=False):
                    gr.Markdown("**Demostración local, no despliegue público.** Las acciones requieren una clave configurada en `SIDEB_REVIEW_TOKEN` antes de iniciar la app. Sin ella, el panel queda en **solo lectura**. La clave no se guarda en los CSV. Las decisiones no alteran los resultados científicos.")
                    with gr.Row():
                        supervisor_genre=gr.Dropdown(PROFILE_OPTIONS,value="rock",label="Estilo musical")
                        supervisor_model=gr.Dropdown(list(POLICIES),value=POL_C,label="Modelo")
                    supervisor_rep=gr.Dropdown(list(REPRESENTATIONS),value=REPRESENTATION,label="Etiquetas")
                    supervisor_artist=gr.Dropdown(label="Artista elegible")
                    supervisor_genre.change(_eligible_dropdown,[supervisor_genre,supervisor_rep,supervisor_model],supervisor_artist)
                    supervisor_rep.change(_eligible_dropdown,[supervisor_genre,supervisor_rep,supervisor_model],supervisor_artist)
                    supervisor_model.change(_eligible_dropdown,[supervisor_genre,supervisor_rep,supervisor_model],supervisor_artist)
                    app.load(_eligible_dropdown,[supervisor_genre,supervisor_rep,supervisor_model],supervisor_artist)
                    with gr.Row():
                        supervisor_alias=gr.Textbox(label="Alias de auditor",value="AUDITOR_DEMO")
                        supervisor_decision=gr.Radio(["Aprobar","Solicitar revisión","Bloquear en demo"],
                                                     value="Solicitar revisión",label="Acción")
                    supervisor_reason=gr.Textbox(label="Justificación (obligatoria)",lines=2,
                                                 placeholder="Indica qué riesgo identificaste y por qué intervienes")
                    supervisor_secret=gr.Textbox(label="Clave local del auditor",type="password",
                                                 placeholder="Clave configurada antes de iniciar SIDE B")
                    with gr.Row():
                        supervisor_button=gr.Button("Guardar decisión",variant="primary")
                        history_button=gr.Button("Verificar / consultar historial")
                    supervisor_result=gr.Markdown()
                    supervisor_history=gr.Dataframe(label="Últimas decisiones verificadas",interactive=False)
                    supervisor_button.click(_oversight_save,[supervisor_alias,supervisor_genre,supervisor_model,
                        supervisor_rep,supervisor_artist,supervisor_decision,supervisor_reason,supervisor_secret],
                        [supervisor_result,supervisor_history,supervisor_secret])
                    history_button.click(_oversight_history,[supervisor_secret],
                                         [supervisor_result,supervisor_history,supervisor_secret])
                    gr.Markdown("**Efecto de cada acción:** «Bloquear en demo» excluye al artista en el perfil y política elegidos; «Aprobar» revierte ese bloqueo; «Solicitar revisión» registra la solicitud sin cambiar el ranking. Las modificaciones del archivo firmado generan una alerta y detienen la aplicación de bloqueos. No uses nombres personales como alias.")
                with gr.Accordion("Detalles de metodología y pruebas de robustez",open=False):
                    gr.Markdown("El modelo puntúa artistas con **TF-IDF de etiquetas + similitud coseno**. "
                                "Las cuatro políticas A/B/C/D combinan un peso de popularidad diferente con o sin límites por grupo. "
                                "La métrica de similitud no es una valoración de personas.")
                    with gr.Row():
                        robust_genre=gr.Dropdown(PROFILE_OPTIONS,value="latin",label="Perfil")
                        robust_repr=gr.Dropdown(list(REPRESENTATIONS),value=REPRESENTATION,label="Representación")
                    robust_btn=gr.Button("Ver robustez del perfil")
                    robust_table=gr.Dataframe(interactive=False)
                    robust_btn.click(_robustness,[robust_genre,robust_repr],robust_table)
                    gr.Markdown("Las etiquetas de las grabaciones faltan a menudo y se usan las de artista como respaldo. "
                                "En el perfil latino puede haber solo nueve candidatos; no agregamos recomendaciones inexistentes.")
                with gr.Accordion("Privacidad, riesgos y límites del proyecto",open=False):
                    gr.Markdown("""**Controles activos en la demostración:**
- Sin cuentas de streaming ni historiales privados; la app escucha únicamente en `127.0.0.1`.
- Las decisiones humanas requieren una clave local (no hay autenticación de usuarios multirol).
- Cada acción exige alias, decisión y justificación; el registro se firma con una cadena HMAC y se comprueba antes de usar bloqueos.
- Entradas y perfiles se validan en el servidor; no se alteran el dataset ni los CSV de experimentos.
- Las respuestas individuales no se publican; solo se muestran tendencias agregadas de nueve relatos indirectos.
- La selección de grabaciones visibles está sujeta a un control automático de metadatos, **sin certificar que la canción corresponda al género**; el ranking sigue siendo de artistas.

**Límites:** una clave compartida no ofrece identidades verificadas ni protección frente a alguien con acceso completo a la computadora y la clave. La cadena detecta cambios intermedios, pero no garantiza detectar que alguien borró el archivo completo o su tramo final. No desplegar públicamente sin autenticación real, respaldos y controles de acceso.

**Equidad:** popularidad baja no equivale a artista emergente. TF-IDF de géneros no equivale a preferencia humana. Las recomendaciones ilustrativas pueden ser grabaciones no musicales.""")
                    gr.Markdown("**Matriz de riesgos y responsabilidades (prioridades iniciales)**")
                    gr.Markdown("**Privacidad y explicaciones:** la app no solicita cuentas de streaming; los perfiles no se almacenan. "
                                "El desglose del ranking puede verse en Descubrir música → ¿Por qué aparecen estos artistas? "
                                "Las respuestas individuales son privadas; los relatos cualitativos no equivalen a puntuaciones completas por canción. "
                                "Consulta `docs/PRIVACIDAD_EXPLICABILIDAD.md` antes de compartir o publicar resultados.")
                    gr.Dataframe(value=_risk_table(),label="Riesgos de SIDE B",interactive=False)
                    gr.Markdown("La probabilidad y el impacto son estimaciones cualitativas del equipo, **no** frecuencias medidas. Ver `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md` y las pruebas automatizadas.")
        gr.Markdown("<small>SIDE B · Prototipo académico local · Sin reproducción de audio · Sin acceso a cuentas de música.</small>")
    return app


if __name__ == "__main__":
    app=create_app()
    app.launch(server_name="127.0.0.1",server_port=7860,share=False,inbrowser=True,
               theme=gr.themes.Soft(primary_hue="teal",neutral_hue="slate"),css=CSS,show_error=True)
