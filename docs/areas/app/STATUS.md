# STATUS — Área App (diseño/UX)

## Estado actual
**ADR-0001** — rediseño del formulario de revisión (ocultar campos poco
frecuentes salvo que tengan valor extraído — con Neto e IVA 21% siempre
visibles pero no bloqueantes, grilla responsiva en desktop, procesamiento
automático sin botón manual). Implementado en código desde el 2026-07-07.

**ADR-0002** — rediseño de la pantalla de inicio (sesión de diseño CEO+CPO,
2026-07-11): auto-procesamiento también en la pantalla de inicio (aplica el
mismo mecanismo de ADR-0001), texto de bienvenida sobre la dropzone,
contenido con ancho máximo en desktop. Implementado el mismo día. De paso
se agregó **cache-busting a `app.css`/`app.js`** (query param con el mtime
del archivo) — resuelve de raíz el problema de la sesión anterior (cambios
de código que no se veían reflejados en el navegador).

**ADR-0003 — corrige la Decisión 4 del ADR-0002** (mismo día, misma sesión
de diseño): el botón genérico "Ver planilla de Facturas" se reemplaza por
el **nombre real de la planilla conectada como link** (o "Conectá tu
planilla" sin conexión), más el **email de la cuenta logueada** — visible
siempre, sin acción de click. Header pasa a 4 zonas (título / nombre de
planilla / email / Configuración+Salir), 3 filas en mobile, 1 fila en
desktop. Requirió agregar `User.spreadsheet_title` — sin Alembic en el
proyecto, se agregó una auto-migración liviana al arrancar la app (ver
`app/__init__.py::_ensure_schema`) que sólo agrega la columna si falta,
sin destruir datos. **Probado de punta a punta contra la planilla de
referencia real** (no un mock): reconectar guardó el título real
("Facturas Proveedores - bot") y el header lo mostró correctamente.

**ADR-0004** — tips gestionables + textos de bienvenida/feedback en la home
(misma sesión de diseño): archivo editable `strings/tips.txt` (`app/services/tips.py::get_tips()`,
pensado para que la pantalla de espera del ADR-0005 lo reuse a futuro), un
tip rotando cada 9s con fade, y saludo/entrada/feedback arriba de la
dropzone. Tras probar en navegador, dos ajustes del founder: el bloque de
texto queda centrado y el saludo con la misma tipografía que la entrada
(antes más chico y gris); de paso se subió el contraste del borde de la
dropzone. **Confirmado funcionando.**

**Los 4 ADRs (0001, 0002, 0003, 0004) están implementados y CONFIRMADOS
funcionando** — el founder probó todo en navegador el 2026-07-11.

**Ajustes posteriores al probar (mismo día)**: el texto de entrada se
reescribió de nuevo ("Gracias por probar nuestra aplicación" + el objetivo
de la app, sin saludo separado) y se agregó un **contador `N/200` en el
header**, siempre visible, a la izquierda de "Configuración" — ver
ADR-0008 repo general para el diseño funcional del tope. Listo para
commitear.

**Dos bugs encontrados por el founder al probar de verdad**, ambos
resueltos (`docs/ISSUES.md`):
- **Issue #004**: el contador y el aviso del tope mensual no se
  actualizaban en el navegador después de guardar una factura (se
  renderizaban una sola vez del lado del servidor, y volver a la home es
  navegación client-side). Corregido: `GET /api/invoices` también manda el
  conteo, el frontend lo actualiza cada vez que se recarga la lista.
- **Issue #005** (no es de esta área, pero lo reportó probando acá): la
  misma foto de factura daba datos distintos entre extracciones — Gemini no
  tenía fijada la `temperature`. Se fija en 0
  (`app/services/gemini.py`, [ADR-0010 repo general](../../decisions/0010-extraccion-determinista-temperature-cero.md)).

Además, `docs/decisions/0009-comunicacion-nunca-mencionar-ia.md` (repo
general, transversal): ningún texto visible menciona IA/Gemini — auditoría
hecha y corregida en 3 lugares (2 de ellos fuera del área App). Ese mismo
ADR ahora también agrupa una segunda regla ("sin dos puntos en textos
nuevos"), sumada por el ADR-0004.

**Onboarding de configuración de planilla — implementado (2026-07-11)**
(`templates/config.html`, `strings/es.json`): pasó de 2 pasos genéricos a 3
pasos secuenciados y explicados, en el orden que resultó más práctico —
**Paso 1** copiar el email de la Service Account (acción rápida, sin salir
de la app), **Paso 2** crear la planilla nueva (link a `sheets.new`) o
abrir la que ya tenga, y compartirla pegando el email ya copiado, con
explicación de que los encabezados se arman solos al conectar; **Paso 3**
pegar el link de vuelta en la app. Ajustes visuales de paso: bordes de los
recuadros más visibles, botones "Copiar"/"Crear planilla nueva" con el
mismo estilo (fondo azul, texto blanco), estado "Copiado" en verde
cursiva.

**[ADR-0005 de esta área](decisions/0005-titulo-planilla-nueva.md)
(2026-07-11, con una corrección el mismo día)**: en la primera conexión
(nunca en reconexiones) el cliente puede elegir un título para su
planilla. **Primer intento** (probado, pero corregido antes de la versión
final): sugería un título precargado a partir del email. **Versión
final, a pedido del founder**: el campo arranca **en blanco** (placeholder
"Ej. Ferretería López") — el cliente escribe el nombre que quiera, y el
**sistema le agrega el año automáticamente** (el cliente no escribe el
año). Se renombra de verdad en Google Drive vía la API de Sheets
(`gspread.Spreadsheet.update_title()`).

**Además, el founder pidió crear pestañas de período al conectar** — esto
reabrió el [ADR-0003 del área Planillas](../planillas/decisions/0003-pestanas-por-periodo.md),
que pasó por **tres versiones en dos días**:
- **2026-07-11**: crear las 12 pestañas mensuales del ciclo anual todas de
  una, al conectar. Implementado y probado — pero en el camino se
  encontró un límite real de la API de Sheets (**Issue #006**,
  `docs/ISSUES.md`): crear 12 pestañas con el método directo (~7 llamadas
  de escritura cada una) hace ~80 llamadas seguidas, y **se probó de
  verdad contra la planilla de referencia — falló por cuota excedida de
  Google a partir de la pestaña #9**. Se resolvió agrupando todo en 2
  llamadas a la API (`batch_update` + `values_batch_update`) en vez de ~80.
- **2026-07-12, primer ajuste**: una pestaña mensual por vez, creada
  cuando hace falta (`JUL-26`, después `AGO-26`, etc.) — no las 12 de una.
- **2026-07-12, versión vigente**: simplificado más — **una sola pestaña
  por AÑO calendario** (ej. `"2026"`, sin abreviatura de mes). Conectar
  crea la pestaña del año en curso; la del año siguiente (`"2027"`) se
  crea recién cuando llega. El mecanismo en lotes que resolvió el Issue
  #006 se mantuvo (por si hiciera falta crear más de una pestaña junta a
  futuro), aunque con este ritmo (una vez por año) el límite de cuota deja
  de ser un riesgo real.

**Cierre del alcance acotado (2026-07-12, cuarta vuelta sobre el ADR-0003)**:
el founder probó cargar una factura real y notó que se seguía guardando en
"Hoja 1", no en la pestaña del año — el "alcance acotado" de las versiones
anteriores (solo crear pestañas, sin usarlas) nunca se había cerrado. Ya
está cerrado: `append_invoice`, `list_invoices` y `find_duplicate` ahora
usan de verdad la pestaña del año (por defecto, el año actual — no busca
en años anteriores, limitación aceptada). "Hoja 1" queda con los datos
reales de pruebas anteriores del founder, intacta pero sin uso — confirmado
explícitamente que no hace falta migrarla (estamos en desarrollo).

Todo esto (título en blanco + año automático + pestaña anual + guardar y
leer de esa pestaña) probado de punta a punta contra la API real de
Sheets: una factura de prueba se guardó en la pestaña del año correcto
(no en "Hoja 1"), se leyó de vuelta, y se detectó como duplicado al
intentar cargarla de nuevo. Todo restaurado a su estado original en la
planilla de referencia después de cada prueba, sin tocar los datos reales
de "Hoja 1". **Confirmado funcionando por el founder en navegador
(2026-07-12)** — cargó una factura real y quedó en la pestaña del año
correcto. Commiteado y desplegado a producción el mismo día.

Decisiones de diseño adoptadas en **otras** áreas que esta tiene que
reflejar cuando se implementen:
- Pantalla de espera / cold start —
  [`docs/decisions/0005-pantalla-espera-cold-start.md`](../../decisions/0005-pantalla-espera-cold-start.md)
  (repo general). Ahora **prioridad alta pre-lanzamiento**: también
  enmascara los reintentos automáticos ante 503 de Gemini (ver
  `docs/ROADMAP.md`).
- Aviso de duplicado detectado —
  [`docs/areas/planillas/decisions/0009-ux-duplicados.md`](../planillas/decisions/0009-ux-duplicados.md)
  (área planillas) — **ya implementado y confirmado en producción**.

## Next
1. Decidir si hace falta que "Últimas facturas"/duplicados busquen también
   en años anteriores (hoy solo miran el año actual) — limitación aceptada
   por ahora, ver ADR-0003 área Planillas.
2. Decidir qué hacer con los datos que quedaron en "Hoja 1" (facturas
   reales de pruebas del founder de antes de este cambio) — hoy no se
   leen más. ¿Migrarlos a mano a la pestaña "2026" en algún momento, o
   dejarlos como quedaron?
3. Probar el rediseño completo en el celular (mobile real, no solo
   navegador desktop) — pendiente en `docs/STATUS.md` general.
4. **Prioridad alta pre-lanzamiento**: implementar la pantalla de espera
   (`docs/decisions/0005-pantalla-espera-cold-start.md`, repo general) con
   el enmascaramiento de reintentos de Gemini.
5. Conversación de diseño dedicada más amplia, para completar el resto de
   `PRODUCTO.md`: pantallas, flujos, identidad visual.
