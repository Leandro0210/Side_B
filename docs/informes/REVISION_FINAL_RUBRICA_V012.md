# SIDE B — Revisión final de rúbrica y preparación de evidencias v0.12

**Base:** rúbrica original «Proyecto final del curso: auditoría ética de un sistema de IA» (diapositiva 8, 100 puntos) y plantilla académica «Artículo Científico — Revista 3i» (6 páginas de instrucciones).  
**Alcance:** revisión reproducible de la evidencia del repositorio, no nota obtenida ni evaluación oficial del docente.  
**Fecha de corte de evidencia:** 24 de noviembre de 2026.

## Dictamen ejecutivo

SIDE B cumple el **objetivo de construir una auditoría ética experimental de un sistema de recomendación de artistas**. Los **siete criterios de la rúbrica tienen evidencias identificables**; cuatro poseen soporte técnico y documental sólido para un prototipo académico, mientras tres mantienen controles o datos por completar. La cobertura de 100 puntos de *criterios* **no equivale a obtener 100 puntos de calificación**. La demostración académica local es defendible con limitaciones explícitas; el despliegue autónomo o público no se considera autorizado.

### Correspondencia con la rúbrica original

| Criterio literal o equivalente | Peso | Estado técnico | Evidencia inspeccionada | Limitación que debe exponerse |
|---|---:|---|---|---|
| Descripción del sistema y objetivo | 10 | Sólido | `README.md`, `docs/guias/MODELO.md` | El motor recomienda artistas, no escucha audio ni estima gusto real |
| Stakeholders y datos utilizados | 10 | Sólido | `docs/DICCIONARIO_DATOS.md`, `data/dataset_v1/side_b_dataset.csv` | Muestra intencional y desbalance geográfico; etiquetas incompletas |
| Sesgos y análisis de fairness | 15 | Sólido experimental | `data/auditoria_v0_1/ablation_overall.csv`, `data/robustez_v0_2/robustness_by_profile.csv` | Medir distribución de exposición no demuestra justicia normativa |
| Privacidad y explicabilidad | 15 | Parcial | `docs/PRIVACIDAD_EXPLICABILIDAD.md`, `tests/test_explain_privacy.py` | Faltan consentimiento verificable, retención y control de acceso para datos humanos |
| Supervisión humana, seguridad y responsabilidad | 20 | Parcial | `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md`, `tests/test_security_controls.py` | HMAC y token locales; falta recuperación externa y autenticación individual |
| Impacto social y riesgos | 15 | Parcial | `docs/matriz_riesgos.csv`, `docs/informes/MATRIZ_RIESGOS_MITIGACION_V010.md` | Se evalúan riesgos previstos, no impactos sociales observados |
| Medidas de mitigación y conclusión final | 15 | Sólido experimental | `side_b_ethics_closure.py`, `docs/informes/DICTAMEN_ETICO_V011.md` | No existe evidencia para afirmar que la política C maximiza la utilidad humana |
| **Total** | **100** | **7/7 criterios con fuentes** | **4 sólidos; 3 parciales** | **No se proyecta una nota docente** |

## Resultados comprobables y límites

El catálogo se compone de **72 artistas, 576 grabaciones y seis estratos de 96 grabaciones cada uno**. Del total de grabaciones, **311/576 (53,99 %) no cuentan con popularidad individual disponible** y **499/576 (86,63 %) carecen de etiquetas de género a nivel de grabación**. La representación utiliza etiquetas complementarias del artista, una decisión que afecta la validez de las similitudes. Los terciles *baja/media/alta* describen popularidad relativa de la muestra; no identifican grupos protegidos, músicos nuevos ni potencial de ingresos.

En el experimento de cuatro políticas, cada una genera un Top-10 en seis perfiles (60 posiciones en total). El grupo de popularidad alta aparece **36/60 (60,0 %) en A**, **21/60 (35,0 %) en B**, **18/60 (30,0 %) en C** y **18/60 (30,0 %) en D**. De A a C hay **18 posiciones menos y una diferencia descriptiva de −30 puntos porcentuales**. La similitud proxy media pasa de 0,310430 (A) a 0,339983 (C); **no es una calificación humana ni una prueba de causalidad**.

La representación sin la etiqueta de muestreo muestra que algunos perfiles cambian de elegibilidad; las 48 combinaciones de perfiles, representaciones y políticas se reproducen con el diagnóstico de robustez. La elección de una política «más justa» depende del objetivo normativo, la elegibilidad y una medición de pertinencia que todavía falta.

La revisión del catálogo identificó **cinco ejemplos ilustrativos con problemas claros de metadatos**; cuatro recibieron una alternativa propuesta y uno no tiene ejemplo apto en el dataset. Las alternativas requieren escucha editorial. Los rankings originales no se alteran.

Los **nueve relatos verbales** comunicados por el responsable se resumen en cinco patrones **agregados**. No hay un conjunto de valoraciones pareadas por canción documentado en este repositorio ni constancias de consentimiento individual. Por tanto, no se debe asignar a los nueve participantes medias A/C, diferencias estadísticas, escuchas verificadas o datos fabricados como si fuesen cuestionarios completados. Los porcentajes de exposición proceden de **puestos de ranking**, no de personas encuestadas.

La matriz identifica **11 riesgos**, de los que **5 tienen prioridad inicial alta**, sin certificar mitigación completa. Los siete criterios de salida del dictamen siguen pendientes. La protección local con clave y registros HMAC no equivale a seguridad pública; una cadena HMAC por sí sola no prueba que un archivo no fue truncado o eliminado.

## Observaciones de revisión crítica

1. **Corrigir la presentación de las conclusiones:** evitar «eliminamos sesgos», «mejora de satisfacción», «algoritmo ético» o «artistas emergentes». La afirmación respaldada es **reducción de exposición relativa del tercil alto en esta muestra**.
2. **Separar análisis de ranking y relatos de personas:** nunca convertir descripciones generales en notas de ítems ni en pruebas de significación.
3. **Documentar las restricciones del paper:** los tres resúmenes, resultados de mínimo tres páginas, referencias y declaraciones deben caber en 6–12 páginas con interlineado 1,5.
4. **Atribuir correctamente figuras y tablas:** datos derivados de CSV publicados; las tablas deben insertarse de modo editable y las figuras en PNG de alta resolución, con título, número y nota APA 7.
5. **No confundir controles con impacto social observado:** el registro de riesgos es un análisis preventivo fundamentado, no un experimento de impacto sobre artistas reales.
6. **No inventar firmas, consentimiento, ORCID, autoría ni referencias bibliográficas:** completar o documentar las ausencias de modo verificable antes de entregar el manuscrito.

## Figuras y tablas listas para el paper

Los recursos **reproducibles** están en `docs/paper_assets/` y se regeneran con:

```bash
python generar_figuras_paper.py
python generar_figuras_paper.py --check
```

- **Figura 1:** distribución de puestos baja/media/alta en A/B/C/D.
- **Figura 2:** cuota del tercil alto A/C por perfil frente a su proporción de candidatos elegibles. *Latin* tiene **0 candidatos elegibles de popularidad alta** y no puede interpretarse como resultado de exclusión por modelo.
- **Figura 3:** similitud proxy TF-IDF por política, sin atribuir satisfacción humana.
- **Tabla 1:** 60 posiciones por política, composición y similitud proxy.
- **Tabla 2:** elegibilidad y puestos de popularidad alta por perfil.

Se preservan **PNG de 300 ppp y CSV reutilizables**. El tamaño de las imágenes debe comprobarse nuevamente al insertarlas en Word; no copiarlas como capturas del navegador. Las notas y etiquetas de interpretación se desarrollan en `docs/guias/PLAN_FIGURAS_TABLAS_PAPER.md`.

## Decisión para la siguiente etapa

**Procede redactar un paper académico exploratorio**, haciendo explícitos el alcance del prototipo y sus límites. El trabajo **no** está listo para afirmar satisfacción probada ni para uso público. Se podrán incluir observaciones cualitativas agregadas únicamente con la información y permisos correspondientes; el resultado central autosuficiente es la ablación algorítmica con robustez y análisis de riesgos.

Antes de considerar el manuscrito entregable se verificarán autoría, afiliación, fuente de las palabras clave UNESCO, **10–50 referencias primarias reales**, formato APA 7, tablas y figuras, resúmenes en tres idiomas y consentimiento escrito cuando corresponda. Esto es trabajo editorial pendiente, no una nueva exigencia inventada por SIDE B.
