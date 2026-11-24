# SIDE B — Validación integral reproducible v0.6

## Objetivo y alcance

Documentar evidencia técnica para la auditoría ética del recomendador experimental. El diagnóstico no certifica equidad, ausencia de daño, cumplimiento legal ni seguridad de un despliegue público. Se ejecuta localmente sin red con los mismos 72 artistas, 576 grabaciones y cuatro políticas A/B/C/D.

## Procedimiento reproducible

```bash
python -m unittest discover -s tests -v
python verificar_evidencias.py
python validar_integral_side_b.py --out resultados_validacion
```

También es accesible en Gradio → **Auditoría ética** → **Validación integral reproducible**, dentro de un acordeón cerrado por defecto.

## Comprobaciones

1. Cinco archivos de evidencia coinciden con los SHA-256 de `docs/manifiesto_evidencias_sha256.json`.
2. Dataset fijo: 576 grabaciones únicas, 72 artistas y seis perfiles; popularidad de artista comparable.
3. Reproducibilidad de 48 combinaciones de representación (artista / artista + etiqueta de muestreo), perfil y política, cotejadas con `robustness_by_profile.csv` (elegibles, puestos, grupos, similitud proxy, relajar topes).
4. Desglose de ranking revisado para el primer artista de cada combinación: los sumandos y el total coinciden con la puntuación que utiliza el motor.
5. Consistencia de exposición A/B/C/D en la representación con etiqueta de muestreo, contra el experimento de ablación original.
6. Supervisión humana en directorio temporal: clave incorrecta rechazada, bloqueo y reversión funcionales, manipulación de evento detectada por HMAC; la prueba no modifica registros históricos del usuario.
7. Verificación de ejecución local y exploración de **rutas versionadas** con Git para detectar carpetas conocidas de respuestas individuales, claves y registros privados. Sin repositorio Git, esta comprobación se marca **PENDIENTE**, no como superada.
8. Disponibilidad de agregados de evaluación humana: sin datos privados autorizados no se deduce ninguna puntuación; la ampliación humana continúa **PENDIENTE**.

## Resultado descriptivo reproducido

| Política | Posiciones totales | Posiciones de popularidad alta | Proporción | Similitud proxy media |
|---|---:|---:|---:|---:|
| A, 25 % y sin límite | 60 | 36 | 60 % | 0.310430 |
| B, 25 % y con límite | 60 | 21 | 35 % | 0.325951 |
| C, 5 % y sin límite | 60 | 18 | 30 % | 0.339983 |
| D, 5 % y con límite | 60 | 18 | 30 % | 0.335616 |

Estas proporciones describen **exposición entre los puestos del ranking** y no una tasa de discriminación o de gusto. La similitud proxy se basa en etiquetas musicales, **no** en satisfacción de oyentes. Los terciles son internos a la muestra ListenBrainz; no indican pertenencia a un grupo protegido ni permiten calificar a un artista como emergente.

## Decisión de uso y límites que permanecen

- **Demostración académica local:** permitida solo si las comprobaciones técnicas pasan; vigilar los resultados pendientes.
- **Uso real o despliegue público:** **NO APROBADO**. Faltan autenticación y autorización multiusuario, cifrado y política de retención verificable, recuperación ante eliminación/truncamiento del registro, revisión de seguridad, consentimiento y más participantes reales.
- El HMAC de eventos detecta alteraciones del contenido existentes, pero no prueba por sí solo que un archivo no fue borrado o truncado hasta un prefijo válido. Requiere anclaje, respaldo externo y custodia de claves.
- El nombre de una grabación ilustrativa puede ser no musical (p. ej., intervalo en directo); se requiere revisión del catálogo antes de mostrarla como canción.
- No publicar formularios P01–P05 ni claves de asignación. Los registros de evaluaciones sintéticas se mantienen separados y **no constituyen personas encuestadas**.

**Siguiente evidencia humana:** invitar participantes voluntarios con consentimiento, mostrar grabaciones comprobadas y registrar la valoración real de forma seudonimizada; documentar limitaciones de muestra y análisis. El informe en formato paper se redactará al final con la plantilla de la asignatura.
