# SIDE B v0.7 — Simulación de participantes ficticios

> **NO ES UNA EVALUACIÓN CON HUMANOS.** La simulación contiene nombres inventados, puntuaciones y familiaridades generadas por Python. Ninguna de estas personas fue encuestada ni escuchó las canciones. No declarar que son participantes reales ni utilizar estos promedios como evidencia científica.

## Finalidad

Probar de extremo a extremo el componente de evaluación ciega de recomendaciones del prototipo **SIDE B** y mostrar cómo se procesarían respuestas independientes en una demostración académica.

## Personajes ficticios

Los nombres **Valeria Montes, Mateo Rivas, Lucía Paredes, Diego Salinas y Camila Soto** son etiquetas de personajes creados para la demostración. Sus identificadores son `SIM01` a `SIM05`. No están asociados con personas, entrevistas, consentimientos ni datos personales existentes.

## Datos y método

- Dataset original inalterado: 72 artistas y 576 grabaciones. Rankings provenientes de `data/robustez_v0_2/robustness_recommendations.csv`.
- Se utiliza la **unión ciega** de los candidatos de las políticas A y C de **pop** y **rock**. Los formularios no revelan qué política recomendó cada elemento.
- Cada uno de los cinco personajes obtiene 28 puntuaciones (15 artistas de pop y 13 de rock): **140 registros sintéticos**, diez combinaciones personaje-perfil.
- La escala es 1–5; cada puntuación se determina con afinidades de popularidad **inventadas**, preferencia ficticia de género y ruido seudorrandómico reproducible (`seed=2026`). También se simula la familiaridad.
- Todos los registros de calificación contienen `notes` iniciando exactamente con **`[SIMULADO]`** y se procesan exclusivamente con `--simulated`.
- **Nunca** sumar esos cinco personajes a `P01` para obtener un supuesto tamaño muestral humano de seis.

## Uso

Dentro de SIDE B:

```powershell
.\.venv\Scripts\python.exe simular_participantes.py
```

Genera formularios separados en `simulacion/participantes_ficticios_v07/ratings/`, una clave de investigación simulada bajo `private/`, resúmenes A/C, un manifiesto `MANIFIESTO_NO_HUMANO.json` y la lista de personajes. `simulacion/` permanece excluido de Git por `.gitignore`.

También puedes ver la simulación **sin guardar archivos** desde **Gradio → Auditoría ética → Evaluación humana y simulación → Probar con 5 personajes ficticios → Simular ahora**.

## Interpretación ética

Aunque el programa produzca diferencias numéricas de relevancia, **no** prueban preferencias reales ni justicia algorítmica y no son datos de un estudio de usuarios. El estado de **validación humana ampliada** de SIDE B permanece **PENDIENTE**. Para fundamentar un paper hacen falta personas voluntarias reales, consentimiento, evaluación de grabaciones idóneas y un protocolo reproducible.
