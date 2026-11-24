# SIDE B · Privacidad y explicabilidad (prototipo local)

## Datos y finalidad

- **Datos públicos musicales:** MusicBrainz aporta metadatos de artista y grabación; ListenBrainz, indicadores de oyentes observados. Su cobertura no representa el mercado musical global.
- **Perfiles de escucha en la demo:** solo se selecciona un género de los seis disponibles. No se solicita nombre, correo, historial privado, cuenta de Spotify ni ubicación del oyente.
- **Evaluación real:** la encuesta usa identificadores P01, P02… y debe recopilarse solo con consentimiento, sin datos personales ni información identificativa en `notes`. Las respuestas individuales y la clave de asignación `private/` se conservan **fuera de GitHub**.
- **Supervisión local:** el auditor usa un alias y un motivo; el registro se guarda en `data/supervision/` (excluido de Git), con firma HMAC de integridad y clave en variable de entorno. No se deben incluir nombres, contactos ni datos personales en esos campos.
- **Retención recomendada:** conservar solo agregados de evaluación necesarios para el paper. Borrar las respuestas individuales tras el periodo académico y el consentimiento aplicable.

## Explicación fiel de cada recomendación

El ranking compara etiquetas musicales de **artistas** con el perfil seleccionado mediante TF-IDF y similitud coseno. El score suma:

`ranking_score = (1 - w) × content_similarity + w × popularity_percentile`

Con `w=0.25` (A/B) o `w=0.05` (C/D). Los modelos B y D incorporan además un tope de exposición por tercil de popularidad, que puede relajarse si hay pocos candidatos. El desglose muestra los sumandos efectivos, el grupo y procedencia de metadatos de la grabación ilustrativa. La puntuación matemática no indica que al oyente le guste esa canción ni prueba que el modelo sea justo.

## Limitaciones y amenazas restantes

- La mayoría de las grabaciones carece de etiquetas específicas; los géneros del artista no validan el contenido de cada canción.
- El muestreo tiene concentración geográfica y sesgos de disponibilidad.
- La popularidad es **relativa a la muestra** y a ListenBrainz; popularidad baja no implica ser emergente ni pertenece a un grupo legalmente protegido.
- El control por clave local no sustituye autenticación multiusuario, almacenamiento cifrado, respaldo remoto ni despliegue seguro.
- El HMAC detecta alteraciones de entradas existentes con el secreto intacto, pero **no prueba que no se haya eliminado el archivo o su tramo final**; se requiere anclaje y respaldos externos para eso.
- El sistema se inicia exclusivamente en `127.0.0.1`, `share=False`. No se ha preparado para exposición pública.

## Evidencia para el paper

Usar CSV agregados, capturas que no muestren claves ni respuestas individuales, comprobaciones de integridad, pruebas unitarias y explicaciones reproducibles. Distinguir siempre resultados del modelo, relatos cualitativos y calificaciones efectivamente recibidas por canción.
