# SIDE B — Registro de riesgos y mitigación v0.10

## Propósito

Identificar, priorizar y asignar medidas a riesgos éticos y técnicos del prototipo local SIDE B, con trazabilidad entre **riesgo → medida → evidencia → responsable → pendiente**. Esta matriz es un instrumento de gobernanza académica; **no certifica ausencia de sesgos, seguridad de producción ni cumplimiento jurídico**.

## Criterios de evaluación

- Probabilidad e impacto se valoran de **1 a 5** mediante juicio del equipo; el producto forma una **prioridad inicial** de 1 a 25, no una probabilidad estadística. Alta: 15–25; media: 8–14; baja: 1–7.
- `PARCIAL`: una o más verificaciones técnicas del control pasaron, pero permanecen obligaciones, riesgos residuales o comprobaciones pendientes. No significa riesgo resuelto.
- `PENDIENTE`: la cobertura pertinente es documental, o falta una comprobación automática/humana exigible.
- `FALLA`: al menos una verificación técnica vinculada al riesgo detectó un problema que debe investigarse.
- **Ningún riesgo se declara cerrado automáticamente**. La aprobación del despliegue público permanece en `False` aunque todas las pruebas pasen. Requiere una decisión humana documentada fuera del alcance del prototipo.

La columna **responsable** describe el rol que debe responder por la medida, no afirma una asignación nominal o una firma de aceptación. `evidencia` es una ruta existente en el repositorio; `verificaciones` enlaza identificadores del diagnóstico `validar_integral_side_b.py`. Una prueba de funcionalidad no demuestra que la mitigación tenga efecto social en la población.

## Registro de riesgos y acciones prioritarias

La fuente autoritativa es [`../matriz_riesgos.csv`](../matriz_riesgos.csv), con once riesgos:

| ID | Prioridad | Cobertura actual | Acción para reducir riesgo residual |
|---|---:|---|---|
| R01 | 16 | Cambio de exposición reproducido con A/C; sin garantía de equidad | Diseñar criterio de equidad y evaluar relevancia con oyentes |
| R02 | 15 | Catálogo íntegro; variables incompletas y respaldos | Auditar faltantes por subgrupos y contrastar metadatos |
| R03 | 8 | Ejemplos no musicales detectados y reemplazos de metadatos | Escuchar alternativas y resolver el ejemplo faltante |
| R04 | 12 | Clave local, validación y registro HMAC probados | Separar roles, registrar custodia y revisión externa |
| R05 | 12 | Respuestas individuales excluidas del repositorio conocido | Consentimiento, retención, permisos y revisión de publicación |
| R06 | 16 | Relatos agregados sin inferir puntuaciones por canción | Obtener evaluaciones por ítem y consentimientos verificables |
| R07 | 12 | Limitación de muestreo reconocida | Ampliar regiones e idiomas antes de extrapolar |
| R08 | 15 | Interfaz restringida a localhost | Autenticación individual, TLS y control de abuso para cualquier despliegue |
| R09 | 12 | Integridad HMAC revisada en pruebas | Copias externas, recuperación verificada y custodia de claves |
| R10 | 12 | Diferencias por idioma observadas cualitativamente | Probar pertinencia por idioma en una muestra pertinente |
| R11 | 16 | Exposición y similitud proxy reproducibles | Contrastar con valoraciones y evitar inferencias causales |

## Cómo reproducir la revisión

Desde la raíz del repositorio:

```bash
python -m unittest discover -s tests -v
python validar_integral_side_b.py
python side_b_catalog_quality.py
python side_b_risk_register.py --out resultados_riesgos
```

`side_b_risk_register.py` guarda `riesgos_v010.json` y `riesgos_v010.md` solo en el directorio local opcional. No publica registros de supervisión ni respuestas individuales. Las pruebas de GitHub Actions verifican además el esquema, las prioridades, las rutas de evidencias y que un control fallido no quede oculto por otro exitoso.

En Gradio: **Auditoría ética → Privacidad, riesgos y límites del proyecto → Verificar controles y tareas pendientes**. La tabla inicial es breve; las verificaciones se ejecutan únicamente al pulsar el botón.

## Decisión provisional y criterios de salida

**Decisión: mantener SIDE B como prototipo académico local; no autorizar despliegue público.** Los resultados de A y C demuestran un cambio descriptivo de exposición en esta muestra, no una mejora confirmada de relevancia musical, neutralidad o beneficio social.

Antes de afirmar que el sistema puede usarse fuera de la demostración, se requieren al menos: consentimientos y mediciones humanas suficientes para el objetivo, revisión musical y de idioma, documentación de cobertura/muestreo, controles de acceso reales, custodia y prueba de restauración del historial, y un proceso de aprobación humana con evidencias. La ampliación de mediciones no se reemplaza con estimaciones por participante.

## Conservación de evidencias

No se alteraron los 576 registros, las 72 fichas ni las cuatro políticas A/B/C/D. Las rutas de informes y el manifiesto SHA-256 permanecen inalterados. La matriz puede revisarse y versionarse sin modificar las respuestas de participantes ni los CSV históricos.
