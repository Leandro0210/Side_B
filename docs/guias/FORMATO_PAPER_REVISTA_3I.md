# Guía editorial SIDE B: Artículo científico — Revista 3i

**Fuente de estas reglas:** archivo entregado por el docente, `Artículo Científico-Revista 3i.docx.pdf`, seis páginas. No se republica la plantilla ni sus datos editoriales personales en este repositorio. Este documento es una **lista de control**, no un paper terminado ni garantía de aceptación editorial. Conservar la apariencia exacta de la plantilla al maquetar el manuscrito.

## Restricciones de la plantilla

| Elemento | Regla indicada | Verificación para SIDE B |
|---|---|---|
| Extensión | **6 a 12 páginas**; interlineado **1,5**, sin sangría corriente; solo referencias con sangría francesa | Revisar el documento final en Word y PDF |
| Título | Máximo **12 palabras**, con traducción al **inglés y portugués** | Contar palabras del título español y cotejar traducciones |
| Autorías | Nombre(s), facultad, institución, ORCID, correo; fecha real de envío | No conservar datos del ejemplo editorial; completar con datos confirmados |
| Resumen | Un párrafo de hasta **200 palabras**, objetivo-método-resultados-conclusión, **sin citas** | Usar resultados realmente sustentados; evitar afirmaciones fuertes |
| Abstract y Resumo | Un párrafo cada uno, **hasta 200 palabras**, sin citas | Traducir significado y cifras, no añadir hallazgos |
| Palabras clave | **3 a 5**, en minúscula, separadas por comas, presentes en título y resúmenes y seleccionadas del **Tesauro UNESCO** | Comprobar los términos definitivos del tesauro antes de entrega |
| Introducción | De lo general a lo particular, **aprox. una página**; tema, justificación, objetivo, tipo de trabajo, carrera y nivel de estudios | Enmarcar concentración de popularidad y auditoría ética |
| Metodología | Métodos, técnicas, muestra y análisis; **evitar citas** | Describir extracción, TF-IDF, políticas A/B/C/D, perfiles y carácter exploratorio |
| Resultados | **Mínimo 3 páginas**; tablas y figuras numeradas y citadas en el texto | Incluir exposición A/B/C/D, robustez, calidad y controles con gráficos editables |
| Tablas y figuras | **APA 7** y números arábigos; figuras JPG/PNG en alta resolución; tablas editables en Word; gráficos preferentemente editables, no capturas | Incluir títulos, notas y referencias internas correctas |
| Redacción de resultados | Hallazgos en presente; porcentajes con **% y conteo absoluto entre paréntesis**; párrafos de aprox. 6–10 líneas según la plantilla | Escribir **60 % (36/60)**, no presentar posiciones como personas |
| Ecuaciones | Editor de ecuaciones de Word; numeración arábiga **entre corchetes** y centradas | Solo si se incorporan formalmente |
| Discusión | Comparar con **estudios primarios**, idealmente artículos indexados con DOI; citar en APA 7; se indica límite de similitud del **25 %** | No inventar bibliografía ni prometer un porcentaje; verificar originalidad con el procedimiento académico |
| Conclusiones | Alineadas al objetivo y a las evidencias, sin lenguaje despectivo ni generalizaciones injustificadas | Exposición cambia; equidad y relevancia humana **no demostradas** |
| Referencias | **10 a 50**; APA 7, orden alfabético; cada cita en referencias y cada referencia citada; enlaces verificables, idealmente DOI URL; si no todos, al menos 90 % con enlace | Buscar fuentes primarias reales y cotejar DOI y enlaces |
| Agradecimientos | Solo investigaciones con financiación institucional; eliminar en tesis | Usar solo si realmente aplica |
| Sobre el autor o autora | Párrafo **4–5 líneas**, estudios y experiencia verdadera | Completar únicamente con información confirmada |
| Financiamiento | Declarar recursos propios o patrocinador/proyecto según corresponda | No inventar fuentes de financiación |
| Declaración de intereses | Declaración veraz de conflictos | Confirmar antes de entrega |
| Consentimiento informado | Si se nombran personas o instituciones, **consentimiento escrito** para aparición de nombres y resultados | Preferir resultados anónimos; conservar consentimiento en lugar privado si corresponde |
| Derechos de uso | La plantilla indica **Creative Commons Atribución 4.0 Internacional** | Completar titularía y atribución de la obra final según condiciones reales |
| Entrega a revista (OJS) | Tres documentos separados: manuscrito, carta de entendimiento, formulario de autoverificación | Solo si se hará un envío formal; no confundir con la entrega universitaria |

**Advertencias de precisión:** la plantilla no establece de forma universal una tipografía/tamaño de letra en el texto extraído; para esos elementos se conservará su diseño visual. La exigencia de tres páginas de resultados convive con la extensión total de 6–12 páginas; se planificará una distribución que cumpla ambas. El ejemplo tiene datos de autores y correos ilustrativos que **no deben copiarse**.

## Secuencia final propuesta de SIDE B

1. **Título trilingüe y metadatos de autoría** (una vez confirmados los datos).
2. **Resumen, Abstract y Resumo**: redactarlos al final, una vez cerrada la sección de resultados.
3. **Introducción**: problema de popularidad en recomendadores, relevancia ética, objetivo y contexto académico.
4. **Metodología**: dataset MusicBrainz/ListenBrainz, muestra de 72 artistas y 576 grabaciones, TF-IDF, seis perfiles, cuatro políticas y control de robustez. Distinguir estudio algorítmico de relatos cualitativos indirectos.
5. **Resultados (mín. 3 páginas)**: Tabla 1 muestra, Tabla 2 comparación A/B/C/D, Figura 1 distribución de exposición, Figura 2 perfiles, Tabla 3 robustez y calidad del catálogo, Tabla 4 riesgos y mitigación. Cifras **solo** de archivos verificados.
6. **Discusión**: comparar resultados con artículos primarios sobre sesgo de popularidad, exposición, diversidad y evaluación de recomendadores. Confrontar hipótesis, límites y riesgos.
7. **Conclusiones**: el cambio de peso de popularidad altera la exposición en el prototipo; no se prueba equidad global ni beneficio real a usuarios.
8. **Referencias**: 10–50 fuentes primarias verificadas, APA 7 y DOI/enlaces.
9. **Declaraciones editoriales finales**: autoría, financiación, intereses, consentimiento, derechos y agradecimientos solo si aplican.

## Mapa de evidencias existentes

| Sección | Archivo reproducible o informe |
|---|---|
| Metodología de la muestra | `docs/DICCIONARIO_DATOS.md` y `docs/guias/MODELO.md` |
| Resultados de ablación | `data/auditoria_v0_1/ablation_overall.csv` y `docs/informes/AUDITORIA_EXPOSICION.md` |
| Robustez | `data/robustez_v0_2/robustness_overall.csv` y `docs/informes/ROBUSTEZ.md` |
| Calidad de catálogo | `docs/informes/CALIDAD_CATALOGO_V09.md` |
| Estudio exploratorio cualitativo | `docs/informes/ESTUDIO_EXPLORATORIO_V08.md` |
| Privacidad y supervisión | `docs/PRIVACIDAD_EXPLICABILIDAD.md` y `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md` |
| Riesgos y mitigaciones | `docs/matriz_riesgos.csv` y `docs/informes/MATRIZ_RIESGOS_MITIGACION_V010.md` |
| Dictamen ético y decisión de uso | `docs/informes/DICTAMEN_ETICO_V011.md` y `side_b_ethics_closure.py` |

## Condiciones para afirmar que el paper está listo

- No copiar frases de muestra de la plantilla; redactar el texto propio y revisar similitud.
- No afirmar consentimientos ni notas humanas por ítem que no estén verificadas.
- No anunciar significación estadística ni causalidad sin análisis que la sustente.
- Verificar manualmente paginación, tablas/figuras, referencias APA 7, idioma y estilo.
- Confirmar la versión final con el docente antes de tratar el documento como un manuscrito publicable.
