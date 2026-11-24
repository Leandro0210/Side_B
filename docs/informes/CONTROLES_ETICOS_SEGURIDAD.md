# SIDE B — Supervisión, seguridad y responsabilidad (prototipo)

> Etapa anterior al paper académico: evidencia técnica verificable, sin atribuir capacidades de producción al prototipo.

## 1. Objetivo y alcance

SIDE B es un demostrador **local** de auditoría ética. El modelo A da 25 % de peso a popularidad y C, 5 %; los CSV de experimentos permanecen intactos. El módulo de supervisión altera **solamente** las recomendaciones de la pestaña «Descubrir música», al aplicar bloqueos por perfil/política/representación. La pestaña «Comparar algoritmos» usa el conjunto experimental original, sin esos bloqueos, para preservar comparabilidad.

## 2. Flujo humano y responsabilidad

1. Un auditor se identifica mediante **alias no personal** y clave local compartida en `SIDEB_REVIEW_TOKEN`.
2. Selecciona perfil, política, representación y artista elegible.
3. Registra una justificación de 10–500 caracteres y una decisión: **Aprobar**, **Solicitar revisión** o **Bloquear en demo**.
4. El sistema valida el contexto y anexa un evento firmado al registro `data/supervision/revisiones_demo.csv`.
5. Un bloqueo excluye al artista del ranking interactivo correspondiente; aprobarlo revierte el bloqueo. Solicitar revisión deja evidencia sin alterar el ranking.
6. Para consultar el historial de decisiones se solicita la clave de nuevo.

Las decisiones son **demostrativas**: no afectan plataformas musicales ni determinan derechos, ingresos o acceso a contenidos.

## 3. Controles implementados y pruebas

| Control | Comportamiento comprobable | Limitación |
|---|---|---|
| Solo lectura sin clave | Si no se configura `SIDEB_REVIEW_TOKEN` de 16+ caracteres no se permite escribir | La protección no sustituye identidad individual |
| Validación de clave | Se compara la clave en el servidor antes de guardar y de mostrar historial | Una clave compartida no distingue personas |
| Validación de entradas | Se comprueba elegibilidad, decisiones admitidas, formato de alias, justificación y rechazo de fórmulas CSV | No es una validación semántica humana del motivo |
| Integridad del registro | Eventos secuenciales con `previous_mac` y `entry_mac` HMAC-SHA256, verificados antes de aplicar bloqueos | No detecta borrado completo ni truncado final sin respaldo externo; quien conoce la clave podría recomputar firmas |
| Guardado consistente | Se escribe archivo temporal, se sincroniza y se reemplaza por ruta definitiva | Asegura consistencia en un solo proceso local, no bloqueo interprocesos |
| Separación de fuentes | Los experimentos, el dataset, P01 real y P02–P05 sintéticos no se sobrescriben | Valoraciones reales futuras requieren consentimiento y política de conservación |
| Sin exposición pública | Gradio se vincula a 127.0.0.1 con `share=False` | No protege si el equipo está comprometido |

## 4. Pruebas reproducibles

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Pruebas específicas `tests/test_security_controls.py`: clave ausente; clave incorrecta; bloqueo y restauración; solicitud de revisión; manipulación del CSV; historial protegido; rechazo de fórmulas y controles; preservación de dataset/experimentos; detección de clave diferente.

## 5. Matriz de riesgos

El registro `docs/matriz_riesgos.csv` tiene once riesgos con responsables funcionales, verificación técnica cuando existe y acciones residuales. Las puntuaciones son **estimaciones cualitativas**, no estadísticas medidas. **Las verificaciones no declaran riesgos cerrados** y no habilitan despliegue. Consulta `docs/informes/MATRIZ_RIESGOS_MITIGACION_V010.md` y ejecuta `python side_b_risk_register.py`.

## 6. Privacidad y custodia

- No se conectan cuentas de Spotify ni se descargan historiales privados.
- Las respuestas individuales no se incluyen en GitHub. El estudio actualizado contiene únicamente nueve relatos anonimizados en resumen agregado.
- No recolectar nombres, contactos o datos sensibles innecesarios en `reason` o `reviewer_alias`.
- Guardar la clave en un gestor local y nunca añadirla al repositorio, ZIP ni capturas.
- Al finalizar el curso, decidir con los participantes si se conservarán las evaluaciones reales; documentar consentimiento, acceso, retención y borrado antes de reclutar más personas.

## 7. Cómo habilitar el modo demostración (PowerShell)

En la misma terminal desde la que se iniciará SIDE B, ejecuta:

```powershell
$env:SIDEB_REVIEW_TOKEN = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(24))"
$env:SIDEB_REVIEW_TOKEN
.\.venv\Scripts\python.exe app_gradio.py
```

La segunda línea muestra la clave una sola vez para copiarla al campo de Gradio. **Guárdala en un gestor de contraseñas** y no la compartas en chats, informes ni repositorios. Debe conservarse igual al reiniciar; si la pierdes, no podrás verificar el registro antiguo. Para apagar, `Ctrl+C`. Para que no exista riesgo de conservar un secreto en el proyecto distribuido, el ZIP no incluye claves ni decisiones previas.

## 8. Prueba manual recomendada para la exposición

1. Inicia Gradio en local con clave y abre «Auditoría ética» → «Supervisión humana».
2. Selecciona **rock** y modelo **C**, copia el identificador de un artista elegible y anota su posición en «Descubrir música».
3. Guarda una decisión **Bloquear en demo** con justificación y clave. Vuelve a «Descubrir música» y comprueba que desaparece del ranking para ese contexto.
4. Guarda **Aprobar** con otra justificación y comprueba que reaparece. Consulta el historial firmado.
5. Para comprobar integridad, utiliza exclusivamente una **copia** del CSV de auditoría en un entorno de pruebas; edita una decisión y observa que se detecta la alteración. No manipules el registro principal.

## 9. Restricciones finales

Esto no constituye autenticación robusta, control multiusuario, auditoría legal ni certificación de seguridad. Para desplegar públicamente harían falta usuarios y roles individuales, TLS, almacenamiento protegido, registro externo inmutable con checkpoints, retención documentada, protección contra abuso y pruebas de seguridad adicionales. **No recomendamos desplegar públicamente esta versión.**

## 10. Integridad de los resultados científicos

El manifiesto `docs/manifiesto_evidencias_sha256.json` conserva SHA-256 de los datos y reportes originales. Puedes verificar los archivos sin acceder a la red mediante:

```powershell
.\.venv\Scripts\python.exe verificar_evidencias.py
```

Esta verificación detecta modificaciones respecto a la copia documentada, pero **no es una firma digital** ni una prueba de quién creó los datos. El registro de decisiones de la demostración se guarda separado de estos archivos.
