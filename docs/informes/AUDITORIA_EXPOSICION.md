# SIDE B — Primera auditoría experimental del recomendador (v0.1)

**Fecha de revisión:** 5 de noviembre de 2026  
**Base examinada:** `side_b_primera_auditoria.zip` (dataset, recomendaciones, comparación y manifiesto)  
**Unidad de recomendación:** artista; una grabación se muestra únicamente como ejemplo.

## Resumen ejecutivo

Se analizaron 576 grabaciones únicas, correspondientes a 72 artistas, y seis perfiles musicales (rock, pop, indie rock, hip hop, electronic y latin). Cada política generó un Top-10 para cada perfil (60 posiciones por política). No se usan preferencias ni juicios de relevancia de oyentes reales.

El **modelo A** utiliza `0,75 × similitud TF-IDF + 0,25 × percentil de popularidad`; el **modelo D** utiliza `0,95 × similitud + 0,05 × popularidad`, con un límite por tercil de popularidad que se relaja cuando faltan candidatos. Al pasar de A a D, las apariciones de artistas de alta popularidad bajaron de 36/60 a 18/60 y las de baja popularidad aumentaron de 14/60 a 22/60. La similitud media **estimada por metadatos** pasó de 0,310430 a 0,335616 (aumento absoluto de 0,025186; relativo aproximado del 8,1 %). **No se ha demostrado una mejora de satisfacción de oyentes ni ausencia de sesgos.**

## 1. Integridad y trazabilidad

- `side_b_dataset.csv`: 576 grabaciones únicas, 72 artistas.
- `recommendations.csv`: 120 recomendaciones; no hay repeticiones de artista dentro de un mismo Top-10.
- Cada grabación recomendada existe en el dataset y corresponde al artista indicado.
- Los grupos de popularidad de las recomendaciones coinciden con los del dataset.
- Se reprodujeron las dos políticas originales con el código del modelo: **120/120 posiciones coinciden**.
- Las comparaciones se hacen sobre el mismo conjunto de candidatos elegibles por perfil.

## 2. Exposición y composición de candidatos

| Grupo de popularidad observada | Modelo A: apariciones | Modelo D: apariciones | Referencia de elegibilidad, suma de seis perfiles* |
|---|---:|---:|---:|
| Baja | 14 (23,3 %) | 22 (36,7 %) | 18,31 (30,5 %) |
| Media | 10 (16,7 %) | 20 (33,3 %) | 18,94 (31,6 %) |
| Alta | 36 (60,0 %) | 18 (30,0 %) | 22,75 (37,9 %) |

\* Comparador puramente descriptivo: elegir de forma uniforme 10 candidatos elegibles por perfil. **No representa una distribución ética ideal:** la relevancia y el tamaño de los grupos pueden ser diferentes.

Con descuento por posición `1/log2(posición+1)`, la exposición del tercil alto cambia de aproximadamente **61,0 %** (A) a **26,0 %** (D). Esto revela que la mitigación no solo cambia quién aparece, también quién ocupa posiciones visibles.

### Diferencias por perfil

| Perfil | Elegibles (baja/media/alta) | Modelo A Top-10 (baja/media/alta) | Modelo D Top-10 (baja/media/alta) | Similitud A → D |
|---|---:|---:|---:|---:|
| Electronic | 4/8/8 | 0/3/7 | 3/4/3 | 0,232 → 0,281 |
| Hip hop | 7/4/4 | 4/2/4 | 4/3/3 | 0,482 → 0,492 |
| Indie rock | 1/4/9 | 1/1/8 | 1/4/5 | 0,261 → 0,275 |
| Latin | 10/2/0 | 9/1/0 | 8/2/0 | 0,490 → 0,483 |
| Pop | 6/15/13 | 0/1/9 | 4/3/3 | 0,189 → 0,265 |
| Rock | 3/12/21 | 0/2/8 | 2/4/4 | 0,208 → 0,218 |

**Lecturas importantes:**

- **Pop:** de los 34 artistas elegibles, 13 (38,2 %) eran de popularidad alta; sin embargo, el modelo A incluyó nueve de ese grupo entre diez recomendaciones. El modelo D incluyó tres.
- **Electronic:** ocho de 20 elegibles eran de popularidad alta (40 %), pero el modelo A recomendó siete de diez (70 %).
- **Latin:** no hay ningún candidato elegible de alta popularidad. La lista 9/1/0 del modelo A no puede interpretarse como una elección contra artistas de alta popularidad, porque no existían en el pool.
- El límite por grupo se **relajó** en los perfiles indie rock y latin, porque el reparto previsto no era viable. Esto es esperable dada la elegibilidad existente.

## 3. Ablación: separar el peso de popularidad y el límite de grupo

Se ejecutaron **cuatro variantes** manteniendo exactamente el mismo dataset, los mismos perfiles, el mismo Top-10 y la misma definición de candidatos elegibles:

| Política | Peso de popularidad | Límite por grupo | Baja/Media/Alta en 60 posiciones | Similitud media proxy | Artistas únicos expuestos |
|---|---:|---|---|---:|---:|
| A | 25 % | No | 14 / 10 / 36 | 0,310430 | 41 |
| B | 25 % | Sí | 19 / 20 / 21 | 0,325951 | 46 |
| C | 5 % | No | 24 / 18 / 18 | 0,339983 | 45 |
| D | 5 % | Sí | 22 / 20 / 18 | 0,335616 | 45 |

**Hallazgo nuevo:** reducir el peso de popularidad del 25 % al 5 % por sí solo (A → C) ya altera sustancialmente la exposición. La política C obtuvo incluso una similitud de metadatos media ligeramente superior a la de D. Por tanto, **no se puede atribuir todo el resultado al límite por terciles**; de hecho, la utilidad de ese límite debe evaluarse por separado.

Ejemplos: en pop, C y D generaron la misma distribución 4/3/3. En hip hop, C generó 6/3/1 y D 4/3/3: el límite incrementó la participación de alta popularidad y redujo ligeramente la similitud media. En latin, como no hay alta popularidad elegible, el límite se relajó.

## 4. Diversidad y posición

- Artistas distintos expuestos al menos una vez en los seis perfiles: **41 en A**, **45 en D**.
- En el **primer puesto**, A mostró artistas de alta popularidad en cuatro perfiles y de baja popularidad en dos. D mostró artistas de baja popularidad en cinco perfiles y de popularidad media en uno.
- El solapamiento entre listas A y D fue menor para **pop (4 de 10 artistas)** y mayor en **hip hop** y **latin** (9 de 10). La mitigación cambió perfiles de manera desigual.

**Atención:** las 60 posiciones no son 60 oyentes independientes; un mismo artista puede aparecer en varios perfiles, y todos provienen de un catálogo pequeño. Estas cifras son exploratorias.

## 5. Riesgos metodológicos y éticos identificados

1. **Circularidad en los géneros.** Se utiliza `sampling_genre` para construir el vector TF-IDF y también para crear los perfiles. Esto puede incrementar artificialmente coincidencias de género. Debe repetirse el experimento sin usar esa etiqueta como característica predictiva.
2. **Similitudes exactas de 1,0.** Varios artistas alcanzan ese valor para hip hop y uno para latin, coherente con perfiles de una sola etiqueta; no es prueba de afinidad musical real.
3. **Faltantes en el catálogo.** 311 de 576 grabaciones (53,99 %) no tienen popularidad por canción; 499 (86,63 %) no tienen género propio de grabación. Los géneros de artista suplen el segundo faltante, pero no describen el sonido de la canción.
4. **Criterios de equidad.** Popularidad baja no equivale a 'artista emergente' ni a grupo protegido. Una mayor exposición no es automáticamente más justa; deben compararse candidatos pertinentes y justificar los objetivos.
5. **Dos mitigaciones simultáneas.** La comparación original A vs D no aísla causalmente el efecto de disminuir el peso de popularidad y de introducir un límite. La ablación de este informe reduce esa limitación.
6. **No hay valoración humana.** La similitud TF-IDF no equivale a calidad, precisión ni satisfacción. Tampoco hay datos suficientes para evaluar diferencias por edad, género de personas u otras características protegidas.
7. **Cobertura cultural desigual.** El catálogo incluye 47 de 72 artistas asociados a EE. UU. o Reino Unido, y las categorías de perfiles varían en su composición de popularidad.
8. **Ejemplos de canciones.** El algoritmo recomienda artistas; la pista mostrada es ilustrativa y no se evalúa individualmente por afinidad. No deben presentarse sus títulos como canciones recomendadas por un modelo de audio.

## 6. Recomendación de diseño para la siguiente versión

**No elegir aún una política ganadora.** La configuración C (5 % de popularidad, sin límite) resulta un comparador importante, pues en esta muestra tiene la mayor similitud de metadatos, pero no tenemos relevancia validada. Las políticas B y D pueden responder a distintas metas de representación. El próximo experimento debe incluir:

1. **Control de circularidad:** repetir cuatro políticas sin `sampling_genre` dentro de las características TF-IDF; tratar los perfiles con vocabulario del artista y verificar cobertura.
2. **Validación de relevancia:** construir 20–30 perfiles de gustos simulados y una muestra de recomendaciones para evaluación humana ciega de compatibilidad, con escala y protocolo explícitos; separar gustos reales de perfiles simulados.
3. **Sensibilidad:** comparar Top-5, Top-10 y Top-20, así como pesos de popularidad y límites alternativos, con conjuntos elegibles constantes por experimento.
4. **Métricas por perfil:** reportar composición de elegibles, selección por grupo, exposición descontada, similitud proxy, cobertura de artistas y posibles pérdidas para perfiles minoritarios.
5. **Seguridad y responsabilidad:** definir acciones de auditor humano, registro de cambios y límites de inferencia antes de construir el panel.

## 7. Dictamen

**Apto como prueba de concepto y como resultado preliminar de auditoría ética. No apto aún para afirmar fairness o calidad de recomendaciones para usuarios reales, ni para desplegar como recomendador autónomo.**

La evidencia actual sustenta las secciones de sesgo de popularidad, desigualdad de exposición, transparencia sobre limitaciones y prueba inicial de mitigación. La recomendación académica es avanzar al experimento de relevancia y a la evaluación de sensibilidad antes de invertir en una interfaz grande.
