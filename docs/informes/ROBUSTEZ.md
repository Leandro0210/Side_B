# SIDE B — Verificación metodológica v0.2

**Tipo:** prueba de sensibilidad del ranking a la inclusión de la etiqueta de género de muestreo en el vector de artista.  
**Entrada:** 576 grabaciones, 72 artistas, seis perfiles musicales, catálogo SIDE B Dataset v1.  
**Unidad recomendada:** artista; una grabación ilustrativa por artista.  
**Métricas:** posiciones entre Top-10, candidatos compatibles por perfil, similitud TF-IDF interna y coincidencia de rankings.

## Hipótesis metodológica

El recomendador original agrega `sampling_genre` a `artist_genres`. Como el perfil del usuario también es ese género, añadir la etiqueta puede hacer que algunos candidatos resulten compatibles por la propia forma en que fueron muestreados, no únicamente por las etiquetas existentes del artista.

Se comparan dos representaciones de características con las cuatro políticas de ablación ya definidas:

1. `original_con_muestreo`: `artist_genres` + `sampling_genre`.
2. `solo_etiquetas_artista`: únicamente `artist_genres`.

## Resultados globales

| Representación | Política | Posiciones | Artistas diferentes | Baja | Media | Alta |
|---|---|---:|---:|---:|---:|---:|
| Original | A · 25% popularidad, sin tope | 60 | 41 | 14 | 10 | 36 |
| Original | B · 25% popularidad, con tope | 60 | 46 | 19 | 20 | 21 |
| Original | C · 5% popularidad, sin tope | 60 | 45 | 24 | 18 | 18 |
| Original | D · 5% popularidad, con tope | 60 | 45 | 22 | 20 | 18 |
| Sin etiqueta de muestreo | A | 59 | 42 | 15 | 10 | 34 |
| Sin etiqueta de muestreo | B | 59 | 46 | 19 | 18 | 22 |
| Sin etiqueta de muestreo | C | 59 | 43 | 22 | 19 | 18 |
| Sin etiqueta de muestreo | D | 59 | 43 | 21 | 19 | 19 |

La variante C mantiene menor concentración de artistas de alta popularidad que A bajo ambas representaciones. Sin embargo, **los conteos brutos entre representaciones deben contextualizarse**, ya que con el segundo conjunto de etiquetas se reducen los candidatos compatibles y solo se generan 59 posiciones.

## Cambios en elegibilidad

| Perfil | Con etiqueta de muestreo | Sin etiqueta de muestreo |
|---|---:|---:|
| Electrónica | 20 | 17 |
| Hip-hop | 15 | 15 |
| Indie rock | 14 | 13 |
| Latina | 12 | 9 |
| Pop | 34 | 28 |
| Rock | 36 | 35 |

Sin etiqueta de muestreo, el perfil latino tiene nueve artistas con similitud positiva y, por tanto, no podemos completar un Top-10 sin forzar recomendaciones de similitud cero. Este comportamiento es deseable desde el punto de vista de transparencia de elegibilidad.

## Estabilidad de la configuración C

Comparando conjuntos de artistas Top-10 entre representaciones:

| Perfil | Artistas compartidos | Coincidencia de conjuntos (Jaccard) |
|---|---:|---:|
| Electrónica | 8 | 0,667 |
| Hip-hop | 10 | 1,000 |
| Indie rock | 10 | 1,000 |
| Latina | 7 | 0,583 |
| Pop | 9 | 0,818 |
| Rock | 10 | 1,000 |

La sensibilidad es más visible para latina y electrónica. No es correcto concluir que las listas son robustas en todos los perfiles.

## Cómo interpretar los hallazgos

- La sensibilidad a `sampling_genre` es una **limitación metodológica importante** del sistema inicial. No basta para sostener por sí sola una afirmación de *data leakage* clásico o de discriminación.
- La similitud TF-IDF está ajustada por separado en cada representación; no compare directamente los valores absolutos de similitud entre ellas como si midieran una misma escala externa de relevancia.
- Los porcentajes de exposición no controlan por completo calidad ni preferencias verificadas. Los terciles de audiencia son relativos al dataset y no equivalen a artistas emergentes.
- Este análisis evalúa recomendaciones de **artistas**, no calidad musical ni preferencias sobre canciones.

## Recomendación metodológica

Para las conclusiones finales, conservar la representación **solo etiquetas de artista** como análisis de sensibilidad y documentar ambos conjuntos de candidatos. La próxima etapa debe incorporar una evaluación de relevancia independiente: perfiles definidos antes de la recomendación y valoraciones ciegas sobre las recomendaciones, idealmente de varios participantes y con protocolos de consentimiento y minimización de datos.

**No se realizaron consultas externas ni se modificó el dataset original para este informe.**
