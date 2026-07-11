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

Además, el founder definió el foco del onboarding (ver `PRODUCTO.md`): no
es un carrusel genérico, es el paso de **configurar la planilla** (crearla,
compartirla con la SA, pegar la URL) — tiene que ser "a prueba de tontos".
Diseño concreto pendiente de la conversación de diseño dedicada.

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
1. Probar el rediseño completo en el celular (mobile real, no solo
   navegador desktop) — pendiente en `docs/STATUS.md` general.
2. **Prioridad alta pre-lanzamiento**: implementar la pantalla de espera
   (ADR-0005 repo general) con el enmascaramiento de reintentos de Gemini.
3. Diseñar el onboarding de configuración de planilla (ver `PRODUCTO.md`) —
   necesita una conversación de diseño dedicada.
4. Conversación de diseño dedicada más amplia, para completar el resto de
   `PRODUCTO.md`: pantallas, flujos, identidad visual.
