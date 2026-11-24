# Recursos gráficos y tablas para el paper SIDE B — v0.12

**Finalidad:** insertar resultados observados en el manuscrito científico sin rehacer análisis ni inventar pruebas humanas. Figuras derivadas únicamente de archivos CSV reproducibles y **separadas de las notas verbales de participantes**.

| Ítem | Recurso | Fuente de datos | Uso sugerido |
|---|---|---|---|
| Figura 1 | `../paper_assets/figura_01_exposicion_politicas.png` | `data/auditoria_v0_1/ablation_overall.csv` | Mostrar composición del Top-10 de seis perfiles por política |
| Figura 2 | `../paper_assets/figura_02_popularidad_por_perfil.png` | `data/auditoria_v0_1/ablation_by_profile.csv` | Mostrar elegibilidad y cambios específicos A/C por género |
| Figura 3 | `../paper_assets/figura_03_similitud_proxy.png` | `data/auditoria_v0_1/ablation_overall.csv` | Comparar similitud de metadatos como medida proxy, nunca agrado |
| Tabla 1 | `../paper_assets/tabla_01_exposicion_politicas.csv` | `data/auditoria_v0_1/ablation_overall.csv` | Valores completos de las cuatro políticas |
| Tabla 2 | `../paper_assets/tabla_02_comparacion_perfil.csv` | `data/auditoria_v0_1/ablation_by_profile.csv` | Comparación Top-10 A/C y composición de elegibles por perfil |

## Propuestas de títulos y notas para Word (formato APA 7)

**Figura 1.** Distribución de posiciones del Top-10 por nivel de popularidad y política.  
*Nota.* Se suman seis perfiles musicales de diez puestos cada uno; las 60 posiciones **no** representan 60 usuarios distintos. La popularidad se define por terciles relativos al catálogo muestreado. Fuente: elaboración propia a partir de `ablation_overall.csv`.

**Figura 2.** Proporción de posiciones ocupadas por artistas de popularidad alta y proporción de elegibles por perfil.  
*Nota.* La categoría Latin no contiene candidatos elegibles de popularidad alta en esta muestra. Los resultados dependen de composición del conjunto elegible y no demuestran equidad normativa. Fuente: elaboración propia a partir de `ablation_by_profile.csv`.

**Figura 3.** Similitud media de metadatos para las cuatro políticas de ranking.  
*Nota.* La similitud TF-IDF es una medida proxy calculada sobre etiquetas; no evalúa agrado, precisión percibida ni diferencias estadísticamente significativas. Fuente: elaboración propia a partir de `ablation_overall.csv`.

## Reglas de inserción y revisión

1. Insertar el PNG a **300 ppp** y conservar proporciones y títulos; verificar que letras y números sigan legibles en la página.
2. Copiar **datos** desde los CSV y reconstruir tablas editables en Word: **no pegar tablas como imágenes**.
3. Numerar figuras y tablas en arábigos, citarlas explícitamente en los párrafos y usar notas de procedencia.
4. Mantener resultados con **porcentaje y conteo entre paréntesis**, por ejemplo 60,0 % (36/60 posiciones).
5. No contar la misma fila de ranking como persona independiente ni presentar la disminución descriptiva como efecto causal sobre el bienestar del oyente.
6. Regenerar con `python generar_figuras_paper.py` y comprobar con `python generar_figuras_paper.py --check`; las huellas SHA-256 de ambos CSV fuente están en `manifiesto_figuras.json`.
7. Las gráficas son de respaldo para la futura sección **Resultados (mínimo tres páginas)**. No contienen cifras de encuesta humana por canción.
