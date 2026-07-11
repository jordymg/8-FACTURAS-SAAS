# ADR-0003 (app): Header de /app — nombre de la planilla como link + email del usuario

**Date:** 2026-07-11
**Status:** ADOPTADA e IMPLEMENTADA — origen: sesión de diseño CEO (Jordi) +
CPO (Claude), APROBADO por CEO. Confirmada funcionando por el founder en
navegador el 2026-07-11 (probada además de punta a punta contra la API
real de Sheets antes de esa confirmación visual).

## Relación con el ADR-0002
**Este ADR supersede la Decisión 4 del [ADR-0002](0002-rediseno-pantalla-inicio.md)**
(el botón "Ver planilla de Facturas" en el centro del header, implementado
en la sesión anterior sin commitear). El resto del ADR-0002 sigue vigente
sin cambios: auto-procesamiento en la pantalla de inicio, texto de
bienvenida, ancho máximo del contenido en desktop.

## Contexto
El botón genérico "Ver planilla de Facturas" se reemplaza por algo más
concreto: el nombre real de la planilla conectada, como link. Además se
agrega el email de la cuenta de Google logueada — el usuario puede tener
varias cuentas de Google y hoy no tiene forma de saber con cuál entró.

## Decisión A — Centro del header: nombre de la planilla como link
1. Se elimina el botón "Ver planilla de Facturas".
2. En su lugar: el **título real del spreadsheet en Google**, como link.
   Click → abre `https://docs.google.com/spreadsheets/d/{spreadsheet_id}`
   en pestaña nueva.
3. **Sin planilla conectada**: mismo lugar, texto exacto **"Conectá tu
   planilla"**, link a `/app/config` (misma pestaña) — empuja al paso
   crítico del onboarding.
4. **Obtención del nombre**: se lee el título del spreadsheet UNA vez, en
   `connect_spreadsheet()` (`app/services/sheets.py`), en el mismo paso
   donde ya se valida el acceso — y se persiste en
   `User.spreadsheet_title` (campo nuevo). **No se relee de Google en cada
   visita** (decisión explícita del CEO): si el usuario renombra la
   planilla en Google Sheets, el header muestra el nombre viejo hasta que
   reconecta.
5. **Usuarios ya conectados sin título guardado** (`spreadsheet_id`
   presente, `spreadsheet_title` nulo): **fallback elegido por el
   implementador** — se muestra el link con el texto genérico anterior
   ("Ver planilla de Facturas") hasta que reconecten. No se hizo backfill
   automático leyendo el título en el próximo uso — habría significado una
   llamada extra a la API de Sheets en cada carga de `/app` solo para los
   usuarios en este estado transitorio, contra el espíritu de "no releer
   en cada visita" del punto 4. El único usuario real hoy (`mcfly.ar@gmail.com`,
   cuenta de prueba) reconecta para probar este mismo ADR, así que el
   fallback prácticamente no se usa en la práctica.
6. **Nombres largos**: truncado con ellipsis (CSS `text-overflow`), límite
   más agresivo en mobile (220px) que en desktop (320px) — nunca rompe el
   layout del header.
7. El título "Facturas" (izquierda) no cambia — fuera de alcance.

## Decisión B — Email del usuario logueado
1. Se muestra el email de la cuenta de Google logueada — dato que ya existe
   (login openid + email, ADR-0004 general), no se piden scopes nuevos.
2. **Desktop**: en el header, entre el link central y los controles
   Configuración/Salir. Texto secundario/discreto, sin acción de click (es
   un `<span>`, no un link).
3. **Mobile**: el email pasa a su propio renglón, debajo del link de la
   planilla — texto chico, discreto, altura mínima. Visible siempre
   (decisión explícita del CEO, no se esconde en Configuración).
4. No se agrega botón de logout/cambio de cuenta nuevo — "Salir" ya cumple
   esa función (minimalismo pedido por el CEO).

## Implementación de la persistencia (sin framework de migraciones)
El proyecto no tiene Alembic/Flask-Migrate — el schema se crea con
`db.create_all()` en `app/__init__.py`, que **no altera tablas ya
existentes**. Agregar `spreadsheet_title` al modelo `User` no alcanza para
que la columna aparezca en una base ya creada (SQLite local o Postgres de
Render).

**Solución elegida**: un chequeo liviano al arrancar la app (`app/__init__.py`,
justo después de `db.create_all()`) que inspecciona las columnas reales de
`users` vía `sqlalchemy.inspect()` y, si falta `spreadsheet_title`, la
agrega con `ALTER TABLE users ADD COLUMN spreadsheet_title VARCHAR(256)` —
compatible con SQLite y Postgres por igual, idempotente (no falla si ya
existe), sin introducir una herramienta de migraciones formal para un solo
campo nuevo. Si el proyecto necesita más cambios de schema a futuro, ahí sí
vale la pena evaluar Alembic — por ahora es una sola columna nullable.

## Fuera de alcance
1. Logo/marca en lugar del título "Facturas" — futuro.
2. Refresco automático del nombre si se renombra en Google — aceptado como
   desfasaje, se corrige al reconectar.
3. Tips de la home / textos del carrusel de espera — otra sesión.

## Criterios de aceptación
1. Con planilla conectada: el centro del header muestra el nombre real de
   la planilla; click la abre en pestaña nueva.
2. Sin planilla: el centro muestra "Conectá tu planilla" y lleva a
   `/app/config`.
3. Un nombre de planilla muy largo no rompe el header en desktop ni mobile.
4. El email se ve: desktop en la línea del header, mobile en su propio
   renglón discreto. Sin regresión de layout.
5. No hay botón nuevo de logout/cambio de usuario; no se pidió scope nuevo
   de Google.
6. Reconectar la planilla actualiza el nombre guardado.
7. ADR creado, `docs/areas/app/STATUS.md` y `docs/STATUS.md` actualizados.
