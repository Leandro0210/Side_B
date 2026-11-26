# SIDE B — Dictamen ético y cierre de evidencia técnica v0.11

## Objeto y decisión

SIDE B es un **prototipo académico local** de recomendación de **artistas** que compara cuatro políticas de ordenación y permite auditar concentraciones de exposición relacionadas con popularidad observada en la muestra. El dictamen distingue entre una mejora **descriptiva** de diversidad de exposición y las afirmaciones de **equidad**, **relevancia humana** y **beneficio social**, que requieren otros criterios y datos. El cierre técnico autoriza únicamente la **demostración académica local con limitaciones**; **no autoriza un despliegue público**.

## Evidencia reproducible y alcance

El dataset consta de **72 artistas y 576 grabaciones**, clasificados mediante seis perfiles de género musical. Cada política produjo diez artistas por perfil: **60 posiciones por política**, que no corresponden a 60 participantes independientes. Los terciles de popularidad son relativos a esta muestra y a la fuente consultada; no identifican grupos protegidos ni determinan qué artistas son emergentes.

| Política | Peso de popularidad | Límite por grupo | Baja / media / alta (60 posiciones) | Alta (%) | Similitud de metadatos media |
|---|---:|---|---:|---:|---:|
| A | 25 % | No | 14 / 10 / 36 | 60,0 % | 0,310430 |
| B | 25 % | Sí | 19 / 20 / 21 | 35,0 % | 0,325951 |
| C | 5 % | No | 24 / 18 / 18 | 30,0 % | 0,339983 |
| D | 5 % | Sí | 22 / 20 / 18 | 30,0 % | 0,335616 |

**Hallazgo principal:** frente a A, C reduce de **36 a 18** las posiciones ocupadas por artistas de popularidad alta (**−30 puntos porcentuales**). En esta muestra, su similitud proxy por etiquetas también pasa de 0,310430 a 0,339983. Ninguna cifra demuestra por sí misma satisfacción, causalidad, ausencia de discriminación o justicia algorítmica. La comparación A/C aísla el peso de popularidad respecto al límite por grupo, pero no elimina otros problemas metodológicos, como el muestreo y el uso de etiquetas de género.

La evaluación de robustez sin usar `sampling_genre` como característica confirma que los resultados dependen de la representación y de la elegibilidad de cada perfil; **no** se elige una política ganadora universal. Los rankings originales y sus huellas SHA-256 se conservan. Fuentes internas: `data/auditoria_v0_1/ablation_overall.csv`, `docs/informes/ROBUSTEZ.md` y `docs/manifiesto_evidencias_sha256.json`.

## Hallazgos de personas y límites de recepción

Se cuenta con **nueve relatos verbales** comunicados por una persona responsable del proyecto, resumidos por temas sin datos identificables. Se describe heterogeneidad de preferencias: mayor recepción relativa del pop en dos relatos, del rock en dos, interés por el idioma español en uno, baja afinidad general en tres y calificaciones intermedias en uno. Las categorías son **interpretaciones del relato**, no porcentajes poblacionales. No se dispone en el repositorio de consentimientos escritos ni matrices verificadas de puntuaciones por canción y persona. Por tanto, **no es válido** calcular con ellos una diferencia de relevancia humana A/C, medias por participante o significación estadística. Fuente: `docs/informes/ESTUDIO_EXPLORATORIO_V08.md` y `data/estudio_v08/resumen_grupal.csv`.

## Calidad musical, privacidad y supervisión

Cinco ejemplos originales de grabaciones ilustrativas resultaron problemáticos según reglas sobre metadatos: cuatro recibieron **alternativas propuestas del mismo artista** y uno permanece sin un ejemplo adecuado entre los registros disponibles. Las alternativas **no han sido validadas por escucha**. La recomendación sigue siendo de artistas y el ranking no cambió. Fuente: `docs/informes/CALIDAD_CATALOGO_V09.md`.

El prototipo incorpora control local con clave, bloqueo reversible y registro HMAC; las pruebas muestran determinadas propiedades técnicas, no seguridad de producción. Se excluyen del Git público las valoraciones individuales, las claves y la bitácora privada. Faltan consentimientos documentados, procedimiento de retención, control de identidades individuales y copia externa comprobada de la bitácora. El registro HMAC no demuestra protección ante eliminación o truncamiento del fichero. Fuentes: `docs/PRIVACIDAD_EXPLICABILIDAD.md` y `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md`.

## Riesgos residuales y medidas de salida

La matriz vigente contiene **once riesgos**, cinco con prioridad inicial alta (puntuación de 15 a 25). Esas valoraciones se asignaron cualitativamente; **no son tasas observadas**. Ninguna prueba automática cierra un riesgo. Permanecen obligaciones sobre consentimiento, relevancia humana, calidad por escucha, idioma, cobertura cultural, controles de acceso de producción, recuperación de la bitácora y aprobación por responsables.

El diagnóstico `side_b_ethics_closure.py` revisa sin modificar los CSV originales: calcula las diferencias A/C, valida el conteo agregado, contrasta el esquema de riesgos y lista siete **criterios de salida pendientes**. Para ejecutarlo:

```bash
python side_b_ethics_closure.py
python side_b_risk_register.py
python validar_integral_side_b.py
```

| Decisión | Resultado razonado |
|---|---|
| Presentación y demostración local | **Apta con limitaciones explícitas**: mostrar el funcionamiento y los resultados descriptivos, sin afirmar equidad demostrada |
| Selección de política para implementación comercial | **No determinada**: C es un comparador de interés, no una política ganadora validada con usuarios |
| Despliegue público o uso autónomo | **No autorizado**: controles de seguridad, participación y evidencia insuficientes |
| Manuscrito académico | **Manuscrito versionado posteriormente**: consultar `docs/manuscrito/` y mantener consistencia entre tablas, métodos y conclusiones |

## Alcance del dictamen

Este documento **cierra el análisis técnico disponible**, no la investigación ni los riesgos. Un futuro paper puede presentar con precisión el experimento de exposición, la robustez, los límites de calidad y los relatos cualitativos, pero debe separar resultados confirmados de inferencias. Ninguna conclusión de significación estadística, beneficio social causal, consentimiento acreditado o cumplimiento normativo debe aparecer si falta evidencia verificable.
