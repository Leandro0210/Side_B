> **Repositorio público:** no añadir `.venv`, claves, respuestas individuales de participantes, historial de supervisión ni archivos `private/`. No distribuir esos datos en archivos públicos. El manuscrito académico está disponible en `docs/manuscrito/`.

# SIDE B — Gradio simplificado

**SIDE B** es un prototipo universitario para investigar el peso de la popularidad en la exposición de artistas de un recomendador musical. Esta versión **simplifica la interfaz** sin cambiar el dataset, los algoritmos ni los resultados de auditoría.

## Abrir la aplicación

Desde PowerShell, en esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app_gradio.py
```

Abre `http://127.0.0.1:7860` si el navegador no se abre automáticamente. Para cerrar el programa, vuelve a PowerShell y pulsa **Ctrl+C**. Es una aplicación local; **no se comparte en internet**.

Si ya tienes SIDE B con GitHub y las dependencias instaladas, detén Gradio y actualiza tu copia local de `master` con `git pull`. Esta etapa incorpora archivos adicionales a `app_gradio.py`; no basta con reemplazar solo la interfaz. No necesitas recrear `.venv`.

## Navegación nueva (tres pestañas)

1. **🎧 Descubrir música:** elige un estilo musical; explora artistas sin entrar en parámetros científicos. La opción predeterminada es el modelo C (menos peso de popularidad). Puedes cambiar al A para ver un ranking con mayor peso de popularidad.
2. **⚖️ Comparar algoritmos:** compara por defecto A frente a C. Muestra primero un gráfico y una explicación breve; las tablas técnicas quedan dentro de una sección desplegable.
3. **🔎 Auditoría ética:** resumen de resultados, evidencia y limitaciones. La evaluación humana, supervisión, robustez y riesgos están disponibles en secciones desplegables.

Los parámetros avanzados —políticas B/D, representación con etiqueta de muestreo y Top-K— siguen disponibles sin saturar la pantalla principal.

## Qué mide y qué no mide

- Catálogo fijo: **576 grabaciones / 72 artistas** de MusicBrainz, con indicadores de popularidad observada en ListenBrainz.
- El algoritmo recomienda **artistas**, y muestra una grabación **ilustrativa** de cada uno. **No reproduce audio** ni verifica automáticamente si esa grabación se puede escuchar. Desde v0.9, elige una alternativa del mismo artista cuando el registro histórico es claramente una introducción, anuncio, *skit* o fragmento no apto; si no hay alternativa, muestra «sin canción ilustrativa».
- A: 25 % de peso de popularidad; C: 5 %. Los otros modelos B/D añaden una restricción de exposición por grupo.
- Baja/media/alta significan **terciles de oyentes de esta muestra**. No indican qué artistas son emergentes ni equivalen a grupos protegidos.
- La similitud se calcula con etiquetas musicales, **no** con valoraciones verificadas de usuarios.
- Los nueve relatos recibidos se analizan solo de forma **cualitativa y agregada**. No se atribuyen puntuaciones por canción que no fueron comunicadas.
- Las acciones de supervisión se registran aparte y solo modifican la **demostración** local, no los resultados científicos.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La metodología, diccionario de datos y reportes anteriores se conservan en `docs/` y en los scripts de investigación.

## Control de supervisión local (v0.4)

La pestaña **🔎 Auditoría ética** incluye supervisión humana protegida, verificación de decisiones y matriz de riesgos.
La **edición está deshabilitada por defecto** hasta configurar `SIDEB_REVIEW_TOKEN` (16+ caracteres).
Lee `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md` antes de crear decisiones reales de auditoría.

**IMPORTANTE:** si ya tienes un registro de decisiones de versiones anteriores sin firma HMAC, guárdalo aparte antes de actualizar; esta versión no lo acepta ni lo sobreescribe automáticamente. Mantén una única instancia local de SIDE B abierta.
El manuscrito académico basado en la plantilla Revista 3i está disponible en [`docs/manuscrito/`](docs/manuscrito/); la revisión editorial final se realiza por separado.

Comprueba que las evidencias del dataset y experimentos anteriores siguen intactas:

```powershell
.\.venv\Scripts\python.exe verificar_evidencias.py
```


## Privacidad y explicabilidad

En la pestaña Descubrir música se puede abrir «¿Por qué aparecen estos artistas?» para ver el desglose real de la puntuación. Ver [`docs/PRIVACIDAD_EXPLICABILIDAD.md`](docs/PRIVACIDAD_EXPLICABILIDAD.md) para limitaciones, tratamiento de respuestas y claves de auditoría. El sistema es **local**; no usar `share=True` ni publicarlo como un sitio sin otros controles.


## Validación integral local (v0.6)

Se añadió una comprobación reproducible del sistema que **no** sustituye una auditoría externa ni establece que un algoritmo sea justo:

```powershell
.\.venv\Scripts\python.exe validar_integral_side_b.py --out resultados_validacion
```

El diagnóstico comprueba SHA-256, reproduce **48 escenarios** de los cuatro modelos en seis perfiles y dos representaciones, verifica los desgloses de puntuación y simula una intervención humana autorizada en un directorio temporal. Comprueba los archivos **versionados** para evitar subir respuestas individuales si está disponible Git. En la pestaña **Auditoría ética → Validación integral reproducible** puedes ejecutarlo sin mostrar las tablas hasta solicitarlas.

**Estudio de recepción v0.8:** se recibieron nueve relatos de preferencias, publicados solo como cinco tendencias temáticas agregadas, sin nombres, datos personales ni notas individuales por canción. Los relatos son indirectos y no disponemos de consentimientos documentados, por lo que **no se calcula una mejora de relevancia A frente a C**. El diagnóstico conserva el estado de validación humana cuantitativa como **PENDIENTE**. El despliegue público **no está aprobado**.

Resultados y límites: [`docs/informes/VALIDACION_INTEGRAL_V06.md`](docs/informes/VALIDACION_INTEGRAL_V06.md) y [`docs/informes/ESTUDIO_EXPLORATORIO_V08.md`](docs/informes/ESTUDIO_EXPLORATORIO_V08.md).


## Control de calidad del catálogo (v0.9)

SIDE B ya distingue el **artista recomendado** de su **grabación de ejemplo**. El nuevo control de metadatos identificó cinco ejemplos originales problemáticos; propone cuatro alternativas del mismo artista y deja uno sin canción visible en vez de enseñar un intervalo de concierto. Las recomendaciones A/B/C/D no cambian y las valoraciones históricas no se reinterpretan.

Reproducir la revisión sin alterar el dataset:

```powershell
.\.venv\Scripts\python.exe side_b_catalog_quality.py --out data/catalogo_v09/revision_ilustraciones.csv
```

El panel incluye los casos pendientes dentro de **Auditoría ética → Calidad del catálogo**. Consulta [la metodología y limitaciones](docs/informes/CALIDAD_CATALOGO_V09.md) antes de interpretar las canciones: los metadatos no sustituyen una escucha humana ni demuestran correspondencia de género.


## Riesgos éticos y mitigaciones (v0.10)

Se documentaron **11 riesgos** con prioridad cualitativa, responsables por rol, comprobaciones técnicas y tareas pendientes.
Desde Gradio abre **Auditoría ética → Privacidad, riesgos y límites** y pulsa **Verificar controles y tareas pendientes** para consultar el diagnóstico sin saturar la pantalla principal.

```powershell
.\.venv\Scripts\python.exe side_b_risk_register.py --out resultados_riesgos
```

El informe reproducible y la decisión de **no desplegar públicamente** están en [`docs/informes/MATRIZ_RIESGOS_MITIGACION_V010.md`](docs/informes/MATRIZ_RIESGOS_MITIGACION_V010.md). Ningún riesgo se considera eliminado automáticamente; se necesita evidencia humana y una revisión de gobernanza para reevaluar el despliegue.

## Revisión final de la rúbrica y recursos para el paper (v0.12)

Se contrastaron los **siete criterios del proyecto final de auditoría ética (100 puntos)** con las evidencias existentes. **Los siete tienen fuentes identificadas**, cuatro con apoyo técnico sólido y tres con requisitos pendientes. Esto **no predice la calificación** ni convierte un control técnico en una garantía de equidad.

Para comprobar la revisión, las figuras reproducibles y sus fuentes:

```powershell
.\.venv\Scripts\python.exe side_b_rubric_review.py
.\.venv\Scripts\python.exe generar_figuras_paper.py --check
```

- [Revisión final de rúbrica v0.12](docs/informes/REVISION_FINAL_RUBRICA_V012.md)
- [Plan de figuras y tablas del paper](docs/guias/PLAN_FIGURAS_TABLAS_PAPER.md)
- [Guía de formato Revista 3i](docs/guias/FORMATO_PAPER_REVISTA_3I.md)

**Manuscrito académico:** consulta la [versión Word y PDF versionada](docs/manuscrito/) y sus [notas editoriales](docs/manuscrito/README.md). La versión del repositorio corresponde a la revisión editorial del 24 de noviembre de 2026; las correcciones posteriores del PDF se mantienen fuera del repositorio hasta su incorporación explícita. No incorporar puntuaciones humanas que no fueron registradas, no afirmar consentimientos inexistentes ni autorizar despliegue público.
