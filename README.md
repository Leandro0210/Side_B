> **Repositorio público:** no añadir `.venv`, claves, respuestas individuales de participantes, historial de supervisión ni archivos `private/`. El ZIP local puede contener estos datos; Git los excluye. El paper será la última etapa.

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

Si ya tienes SIDE B con Gradio y las dependencias instaladas, solo debes **detenerlo y reemplazar `app_gradio.py`** por el nuevo archivo. No es necesario volver a crear `.venv` ni descargar los datos.

## Navegación nueva (tres pestañas)

1. **🎧 Descubrir música:** elige un estilo musical; explora artistas sin entrar en parámetros científicos. La opción predeterminada es el modelo C (menos peso de popularidad). Puedes cambiar al A para ver un ranking con mayor peso de popularidad.
2. **⚖️ Comparar algoritmos:** compara por defecto A frente a C. Muestra primero un gráfico y una explicación breve; las tablas técnicas quedan dentro de una sección desplegable.
3. **🔎 Auditoría ética:** resumen de resultados, evidencia y limitaciones. La evaluación humana, supervisión, robustez y riesgos están disponibles en secciones desplegables.

Los parámetros avanzados —políticas B/D, representación con etiqueta de muestreo y Top-K— siguen disponibles sin saturar la pantalla principal.

## Qué mide y qué no mide

- Catálogo fijo: **576 grabaciones / 72 artistas** de MusicBrainz, con indicadores de popularidad observada en ListenBrainz.
- El algoritmo recomienda **artistas**, y muestra una grabación **ilustrativa** de cada uno. **No reproduce audio** ni verifica automáticamente si esa grabación se puede escuchar.
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

## Etapa actual: supervisión y seguridad (v0.4)

La pestaña **🔎 Auditoría ética** incluye supervisión humana protegida, verificación de decisiones y matriz de riesgos.
La **edición está deshabilitada por defecto** hasta configurar `SIDEB_REVIEW_TOKEN` (16+ caracteres).
Lee `docs/informes/CONTROLES_ETICOS_SEGURIDAD.md` antes de crear decisiones reales de auditoría.

**IMPORTANTE:** si ya tienes un registro de decisiones de versiones anteriores sin firma HMAC, guárdalo aparte antes de actualizar; esta versión no lo acepta ni lo sobreescribe automáticamente. Mantén una única instancia local de SIDE B abierta.
El paper académico se elaborará al final, cuando el docente entregue su plantilla.

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
