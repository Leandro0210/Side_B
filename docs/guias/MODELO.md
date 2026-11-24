# SIDE B · Modelo experimental v0.1

## Objetivo

Esta es la **primera comparación reproducible de políticas de ranking**, diseñada para el dataset recolectado por SIDE B Collector v2.2. **No es todavía una auditoría de fairness concluida, ni un estudio con oyentes reales.**

Se recomienda **un artista por posición**, acompañado de una grabación de ejemplo. Las 8 grabaciones de un mismo artista no cuentan como 8 oportunidades independientes de exposición. El modelo se basa en etiquetas de artista y género de muestreo: no contiene descriptores acústicos ni aprendizaje supervisado.

## Instalación en el proyecto que ya tienes

1. Copia `side_b_model_v0.py` y `requirements_model.txt` a la raíz de `side_b_dataset_starter`.
2. Copia `test_model_v0.py` a tu subcarpeta `tests` (no borres las pruebas del recolector).
3. Abre PowerShell dentro de `side_b_dataset_starter`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_model.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe side_b_model_v0.py --input data\dataset_v1\side_b_dataset.csv --out data\model_v0 --top-k 10
```

## ¿Qué genera?

- `recommendations.csv`: ranking de artistas (con canción ilustrativa), por perfil y política, con puntuación y tercil.
- `comparison_by_profile.csv`: grupos de popularidad disponibles por perfil, cobertura en top-K, exposición ponderada por posición y similitud media.
- `experiment_manifest.json`: parámetros, procedencia, controles de calidad y limitaciones.

Por defecto se crean seis perfiles **de prueba** a partir de cada `sampling_genre` presente. **No representan usuarios reales.**

## ¿Qué compara?

**A — Baseline con sesgo de popularidad diseñado:** `0.75 * similitud + 0.25 * percentil_popularidad`.

**B — Política mitigada experimental:** `0.95 * similitud + 0.05 * percentil_popularidad`, con un máximo de `ceil(K/3)` artistas del mismo tercil en los primeros K, *si existen suficientes candidatos con similitud positiva*. Si faltan, se relaja el límite, se registra `cap_relaxed` y **nunca** se obliga a recomendar música sin coincidencias en las etiquetas.

**No se entrena un modelo predictivo con etiquetas de relevancia:** TF-IDF ajusta las ponderaciones de los géneros presentes en el dataset. La similitud de coseno es una **aproximación basada en metadatos**, no precisión real ni prueba de satisfacción.

## Principales advertencias metodológicas

- Un perfil como `rock` es un escenario técnico; no es un oyente.
- El tercil no es una clase protegida ni una etiqueta de artista emergente; es relativo al dataset. Igualdad de recuentos no equivale a justicia.
- El listado de candidatos puede estar sesgado por el muestreo de origen; los resultados solo aplican a este catálogo.
- Usar `sampling_genre` en los rasgos garantiza coincidencia con el género de búsqueda: es útil como prototipo, pero hay circularidad entre selección y similitud. Se debe documentar y validar con etiquetas externas para un estudio conclusivo.
- El experimento reduce o restringe popularidad deliberadamente para investigar la hipótesis; no demuestra que Spotify, Last.fm u otra plataforma comercial utilice estas mismas reglas.
- El algoritmo selecciona una grabación ejemplo de forma determinista; no podemos concluir que esa grabación es la mejor de ese artista.
- Para la siguiente fase será necesario evaluar manualmente una muestra de recomendaciones con criterios de relevancia independientes y comparar por perfiles y géneros.
