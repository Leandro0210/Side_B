# SIDE B v0.4 — Supervisión, seguridad y responsabilidad

## Mantuvimos sin cambios

- 576 grabaciones, 72 artistas, políticas A/B/C/D, resultados de ablación y robustez.
- Las tres pestañas sencillas de Gradio.
- Separación entre los datos experimentales, la evidencia de recepción humana y las decisiones de supervisión; la evidencia pública vigente de recepción se limita a nueve relatos agregados.

## Añadimos

- Modo solo lectura por defecto para guardar decisiones.
- Clave local configurada por `SIDEB_REVIEW_TOKEN` antes de iniciar la app.
- Un campo de contraseña obligatorio por acción, sin almacenar la clave en los registros.
- Registro de decisiones con fecha UTC, alias, justificación, orden secuencial y cadena HMAC-SHA256.
- Verificación del registro antes de aplicar un bloqueo o consultar historial. Ante manipulación, se detiene el uso de ese registro.
- Escritura del CSV por archivo temporal y reemplazo; pruebas de validación de campos y fórmulas CSV.
- Elección de artistas: primero aparecen las recomendaciones Top-10 para facilitar una demostración reproducible.
- Matriz de riesgos, informe de controles, manifiesto SHA-256 y script de verificación.

## Cómo demostrarlo

1. Detén Gradio (`Ctrl+C`).
2. Usa el procedimiento de clave de `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md`.
3. Inicia Gradio y entra en `🔎 Auditoría ética` → `Supervisión humana`.
4. Bloquea un artista que figure en el Top-10 del perfil `rock` y modelo `C`.
5. En `🎧 Descubrir música` usa ese mismo contexto, genera la lista y comprueba que se excluye.
6. Vuelve a aprobar el artista y consulta el historial firmado.

**Precaución:** no exponer la aplicación a Internet; la clave compartida y el registro local no son autenticación multiusuario ni archivo inmutable.

## Calidad

- 47 pruebas ejecutadas: 46 superadas, 1 omitida por no haber un archivo opcional.
- `verificar_evidencias.py` confirmó 7/7 archivos originales sin modificación.
- Apertura HTTP de Gradio en `127.0.0.1:7860` verificada localmente.

Este registro describe la etapa v0.4; el manuscrito posterior se encuentra en `docs/manuscrito/`.
