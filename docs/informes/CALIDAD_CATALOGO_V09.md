# SIDE B v0.9 — Calidad de grabaciones ilustrativas

## Objetivo y alcance

SIDE B **recomienda artistas**, no grabaciones individuales. El motor usa TF-IDF sobre etiquetas de artistas y un término de popularidad observada en ListenBrainz. Por ello, la grabación que aparece en una tarjeta es **ilustrativa**, no el ítem puntuado. Este control busca evitar mostrar anuncios, entrevistas o intervalos como si fueran canciones; **no clasifica el audio ni verifica que una canción corresponda al género elegido**.

Se revisaron mediante reglas de metadatos **576 grabaciones de 72 artistas** (8 registros por artista). La fuente es `data/dataset_v1/side_b_dataset.csv`; **permanece inalterada** y su huella SHA-256 se conserva en `docs/manifiesto_evidencias_sha256.json`. No se modificaron los identificadores ni los scores del experimento original.

## Metodología reproducible

1. Se conservó **el ejemplo original** salvo si se detectó una señal fuerte en el título (como *promo*, *interlude*, *skit*, *intro*, *encore break*, *BGM*) o en las etiquetas de grabación (*speech*) o si duraba menos de 30 segundos.
2. Solo para esos casos se buscó una alternativa dentro de las **ocho grabaciones del mismo artista**. Se prefirieron duraciones de 90 segundos a 10 minutos y títulos sin señales de versiones especiales. Un valor faltante de duración o género **no se convirtió en evidencia de calidad**.
3. Si ninguna grabación pasaba el filtro, se dejó el campo **sin ejemplo**, conservando al artista en el ranking.
4. Un conflicto entre etiquetas específicas de la grabación y la categoría de muestreo se muestra como advertencia, no como certificación de género ni como cambio automático de canción.
5. El reporte CSV documenta título e ID de grabación originales, título e ID presentados, estado, motivo del cambio y número de grabaciones consideradas.

Reproducir desde el repositorio:

```bash
python side_b_catalog_quality.py --out data/catalogo_v09/revision_ilustraciones.csv
python verificar_evidencias.py
python validar_integral_side_b.py
```

## Resultados sobre la muestra actual

| Indicador | Valor |
|---|---:|
| Grabaciones históricas conservadas | 576 |
| Artistas considerados | 72 |
| Ejemplos originales con señales fuertes para no presentarlos como canción | 5 |
| Alternativas propuestas de un mismo artista | 4 |
| Artistas sin canción ilustrativa aceptable dentro de la muestra | 1 |
| Ejemplos originales preservados | 67 |

Cambios **solo de presentación**:

| Artista | Registro original | Resultado visible |
|---|---|---|
| Buddy Holly | Don Passerby Promo 1 | Don't Come Back Knocking |
| Lupe Fiasco | Slave Ship (interlude) | Ms. Mural |
| Necro | Kid Joe (skit) | Knife Season (original) |
| ZUNTATA | BGM2 | BURNING STORM |
| The E Street Band | [encore break] | Sin grabación ilustrativa apta en la muestra |

El último caso refleja que las ocho grabaciones disponibles para The E Street Band son fragmentos, introducciones, pausas o entrevistas. **No se eliminó al artista ni se inventó una canción.** Se requiere una futura revisión editorial y nuevas fuentes de grabaciones verificadas.

## Interpretación y límites

- Se encontraron además **11 ejemplos mostrados con etiquetas específicas que no coinciden literalmente con el género usado para muestrear al artista**. No significa que sean canciones de género equivocado de forma definitiva: las categorías son aproximadas y los géneros pueden superponerse. Se mantuvieron los registros para no introducir cambios subjetivos sin escucha.
- Un estado `candidata` significa **sin alertas detectadas**, no "canción validada". `revisar` implica metadatos insuficientes o algún aviso. `sin_ejemplo` indica que no se encontró alternativa apropiada en la muestra.
- Las **fichas científicas y formularios históricos** permanecen asociadas a las grabaciones originales. Estas alternativas **no reescriben retroactivamente** lo que un participante escuchó ni permiten inferir sus calificaciones.
- El análisis de exposición A/B/C/D y sus métricas siguen siendo comparables; el estudio cualitativo de nueve relatos **no permite inferir relevancia pareada A/C**. La evaluación humana con fragmentos verificables, consentimiento y notas por candidato permanece pendiente.
- Este control reduce errores de presentación pero no sustituye control editorial, comprobación por escucha, autorización de reproducción, auditoría de sesgos ni evaluación real de pertinencia musical.

La interfaz permite consultar las incidencias en **Auditoría ética → Calidad del catálogo**. Los casos se publican de forma agregada sin datos personales.
