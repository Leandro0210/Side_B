# Documentación de SIDE B

## Evidencia y método

- `DICCIONARIO_DATOS.md`: columnas, procedencia y significado de los datos.
- `informes/AUDITORIA_EXPOSICION.md`: resultados de rankings y exposición por popularidad.
- `informes/ROBUSTEZ.md`: sensibilidad al uso de etiquetas de muestreo.
- `guias/MODELO.md`: metodología y limitaciones del modelo.
- `guias/ABLACION.md`: reproducción de las cuatro políticas A/B/C/D.
- `manifiesto_evidencias_sha256.json`: huellas de los archivos experimentales sin modificar.

## Privacidad, supervisión y conclusiones

- `PRIVACIDAD_EXPLICABILIDAD.md`: variables explicativas, privacidad y limitaciones.
- `informes/CONTROLES_ETICOS_SEGURIDAD.md`: controles de autorización, integridad y tareas abiertas.
- `informes/ESTUDIO_EXPLORATORIO_V08.md`: nueve relatos agregados y límites de interpretación.
- `informes/CALIDAD_CATALOGO_V09.md`: validación de metadatos de ejemplos musicales.
- `matriz_riesgos.csv`: 11 riesgos con prioridades, responsables y acciones pendientes.
- `informes/MATRIZ_RIESGOS_MITIGACION_V010.md`: trazabilidad de mitigaciones y decisión provisional.
- `informes/DICTAMEN_ETICO_V011.md`: cierre de la evidencia técnica, límites y dictamen de uso.

## Preparación editorial

- `guias/FORMATO_PAPER_REVISTA_3I.md`: restricciones de las seis páginas de la plantilla entregada y mapa de evidencias para la futura redacción del paper.
- `../side_b_ethics_closure.py`: resumen reproducible de A/B/C/D, nueve relatos agregados, once riesgos y siete criterios pendientes.
- `../README.md`: arranque de Gradio y guía principal.

- `informes/REVISION_FINAL_RUBRICA_V012.md`: auditoría final de los siete criterios (100 puntos) y limitaciones.
- `guias/PLAN_FIGURAS_TABLAS_PAPER.md`: figuras/tabla reutilizables con títulos, notas y fuentes para el manuscrito.
- `../generar_figuras_paper.py`: genera tres PNG de 300 ppp y dos tablas CSV bajo `paper_assets/`.
- `../side_b_rubric_review.py`: comprueba cobertura y coherencia de las evidencias existentes.
