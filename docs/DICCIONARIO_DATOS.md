# SIDE B — Diccionario de datos (Collector v2.1)

## `side_b_dataset.csv`

| Columna | Significado | Fuente o cálculo |
| --- | --- | --- |
| `recording_mbid` | Identificador MusicBrainz de la grabación | MusicBrainz |
| `track_name` | Título de la grabación | MusicBrainz |
| `duration_ms` | Duración conocida en milisegundos, puede estar vacía | MusicBrainz |
| `recording_genres` | Etiquetas de género **de la grabación**, separadas por `;` | MusicBrainz; pueden faltar |
| `effective_genres` | Etiquetas disponibles para el modelo; usa artista como respaldo | Derivada: grabación o artista, marcado explícitamente |
| `genre_source` | `recording`, `artist_fallback` o `missing` | Derivada: procedencia de etiquetas |
| `recording_disambiguation` | Texto de desambiguación de la grabación | MusicBrainz |
| `quality_flags` | Anomalías no excluyentes para revisar, separadas por `;` | Regla del recolector |
| `recording_browse_offset` | Página de búsqueda de grabaciones de la cual procedió | Recolector |
| `artist_mbid` | Identificador MusicBrainz del artista usado para seleccionar | MusicBrainz |
| `artist_name` | Nombre del artista | MusicBrainz |
| `artist_country` | País asignado al artista en MusicBrainz, si está disponible | MusicBrainz |
| `artist_type` | Tipo de artista (Person, Group, etc.) | MusicBrainz |
| `artist_genres` | Etiquetas del artista; NO necesariamente de cada canción | MusicBrainz |
| `sampling_genre` | Género textual usado para buscar al artista | Recolector |
| `artist_search_rank` | Posición del resultado en la búsqueda de artistas para ese estrato | Recolector |
| `artist_search_offset` | Offset de página en búsqueda de artistas | Recolector |
| `recording_listens` | Escuchas registradas de la grabación | ListenBrainz; puede faltar |
| `recording_listeners` | Oyentes únicos registrados de la grabación | ListenBrainz; puede faltar |
| `recording_popularity_status` | `available`, `not_available`, `not_returned`, `request_failed` | Recolector |
| `artist_listens` | Escuchas registradas del artista | ListenBrainz; puede faltar |
| `artist_listeners` | Oyentes únicos registrados del artista | ListenBrainz; puede faltar |
| `artist_popularity_status` | Estado de disponibilidad de la popularidad del artista | Recolector |
| `artist_popularity_group` | Tercil de popularidad **dentro de la muestra**, no etiqueta de emergente | Recolector |
| `extracted_at` | Momento UTC de ejecución | Recolector |
| `musicbrainz_url` | Enlace a la grabación en MusicBrainz | Recolector |
| `data_sources` | Servicios consultados | Recolector |

## `artists.csv`

Contiene `artist_mbid`, `artist_name`, `artist_country`, `artist_type`, `artist_genres`, `sampling_genre`, `artist_search_rank`, `artist_search_offset`, `artist_listens`, `artist_listeners`, `artist_popularity_status` y `artist_popularity_group`.

## `excluded_recordings.csv`

`artist_mbid`, `artist_name`, `sampling_genre`, `recording_mbid`, `track_name`, `duration_ms`, `recording_browse_offset`, `reason`.

Los motivos incluyen `clearly_nonmusical_title`, `empty_title`, `missing_recording_mbid`, `invalid_negative_duration`, `invalid_duration_value`, `duplicate_recording_mbid_in_pages`. La repetición de un **título**, con MBID distinto, ya no constituye exclusión automática. **No todas las entradas marcadas para revisión son excluidas.**

## `unselected_recordings.csv`

Candidatos de grabaciones elegibles que no entraron en el cupo final. `same_title_not_selected` indica que se priorizó otro registro del mismo artista/título; `sampling_limit` indica falta de cupo. No confundir candidatos no seleccionados con errores del dataset.

## Variables de auditoría

- Preferir `artist_listeners` para los primeros grupos de exposición por **popularidad observada**; declarar que no equivale a éxito comercial global.
- Conservar `recording_listeners` nulo si falta. No sustituir nulos por cero.
- El `artist_popularity_group` se calcula con terciles del lote y puede cambiar al ampliar la muestra.
- No confundir un grupo minoritario de popularidad con una clase protegida legalmente, ni con artistas emergentes sin datos adicionales.
- La relevancia musical de cada recomendación requiere un protocolo de evaluación independiente del ranking.
