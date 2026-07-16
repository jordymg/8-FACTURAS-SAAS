# Roadmap — Facturas SaaS

> AI agents: work only on the CURRENT phase. Do not start future phases without an explicit instruction.

## Phase 1 — Core flow end-to-end (CURRENT)
Goal: one user (the founder) completes foto → extracción → revisión → Sheet with the production stack.
- [x] Prototipo del founder integrado: Service Account para Sheets, prompt/campos validados, UI multi-archivo con tarjetas (ver ADR-0004)
- [x] Google OAuth flow (solo identidad) + pantalla de conexión de planilla (Service Account)
- [x] PWA: captura multi-archivo (drag&drop) + tarjetas de revisión/edición
- [x] POST /api/invoices: append row (Sheet vía SA)
- [x] Probado end-to-end en local con cuenta real: login → conectar planilla → foto → extracción → guardar → aparece en el Sheet
- [x] Decisión MVP: no persistir la imagen (ni disco, ni Drive, ni S3) — se usa solo en memoria para la extracción y se descarta. Destraba el deploy sin resolver el storage definitivo.
- [x] Deploy to Render (single service) — `https://facturas-saas.onrender.com`
- [x] Issue #001 (facturas desencolumnadas en Sheets) diagnosticado por debug y resuelto — ver `docs/ISSUES.md`
- [x] Estructura v2 de la planilla (23 columnas, ADR-0005/0006/0007/0008/0009 área Planillas) — implementada, con Issues #002 y #003 encontrados y resueltos por el uso real

## Post-MVP
- [ ] Guardar la imagen del comprobante en el Drive del cliente (`Facturas/{año}/{mes}/`,
      nombre `{fecha}_{proveedor}_{numero}.jpg`) — depende de: resultado del experimento
      aislado de OAuth con scope `drive.file` (fuera de este repo, ver STATUS.md)

Exit criterion: founder saves a real invoice from su celular a su propio Sheet via la URL pública. ✅ cumplido — probado en producción real (con bugs encontrados y ya resueltos en el camino).

## Antes de vender — MVP persona a persona (ver ADR-0007 repo general)
El founder define el canal de venta inicial: **persona a persona, a
clientes conocidos, con demo presencial y cobro manual (efectivo)**. Esto
saca a Mercado Pago, landing y dominio propio como bloqueantes duros (pasan
a "Postergado" más abajo) y deja este checklist como lo único necesario
antes de vender:

- [ ] **Términos de uso, versión mínima** — HACER AHORA. Cubre: acceso
      Editor de la Service Account a la planilla conectada (incluye
      soporte), qué datos procesa la app, no-persistencia de imágenes,
      límites de responsabilidad. No busca ser exhaustivo legalmente
      todavía.
- [x] **Reintentos automáticos ante 503 de Gemini** — implementado
      2026-07-15 (handoff del CEO, tras sufrir un 503 real). 3 reintentos
      con backoff 2/4/8s (`app/services/gemini.py`), invisibles vía la
      pantalla de espera con carrusel (`docs/decisions/0005-pantalla-espera-cold-start.md`,
      ahora implementada). Mensaje de error amigable + reintento manual
      solo si se agotan los 3 reintentos. **Hallazgo pendiente de
      decisión del CEO** (no resuelto en esta sesión): el timeout default
      de gunicorn en Render (30s, sin override) podría no alcanzar en el
      peor caso (varios archivos de una tanda golpeando 503 a la vez) —
      ver el ADR-0005 para el detalle y la recomendación.
- [ ] **Onboarding de configuración de planilla** — el foco NO es un
      carrusel genérico de primera apertura, es el paso donde un usuario
      nuevo se puede caer: crear la planilla, compartirla con el mail de la
      SA, pegar la URL. Tiene que ser "a prueba de tontos". Diseño concreto
      pendiente de una conversación de diseño del área App — ver
      `docs/areas/app/PRODUCTO.md`.
- [ ] **Tope de 250 facturas/mes, versión soft** — contador en la DB de la
      app (no leyendo el Sheet), aviso al acercarse al límite (ej. al
      llegar a 200). Sin cobro online todavía, **no hay corte** — solo
      contador + avisos, para ver uso real. Diseño funcional completo en
      `docs/decisions/0008-tope-facturas-mensual.md`.

## Phase 2 — Beta with real users
Goal: uncle + 1 more user run a full month unassisted.
- [ ] Month filter + export (.xlsx / share link)
- [ ] Photo-quality hint + error handling on extraction

Exit criterion: PRD §7 items 1–2 true (uncle's month + accountant accepts the sheet).

## Phase 3 — Launch
- [ ] Success metric tracking in place (paying users count)
- [ ] First real paying user completes core action

### Postergado (ver ADR-0007 repo general) — necesario para escalar más allá de clientes conocidos, no olvidar
- [ ] Mercado Pago suscripciones ($1,999/month) + blocking logic
- [ ] Landing page (served from same Flask service) — esfuerzo bajo / impacto alto, cuando toque
- [ ] Deploy to production with custom domain

## Later / icebox
- ARCA/AFIP integration
- Multi-user / teams
- Native app
- Automatic categorization
- Stats dashboard
- Accountant multi-client mode
- Vista interna de solo-lectura / debug mode para soporte (post-MVP —
  alternativa más acotada al acceso Editor completo de la SA, evaluar
  cuando haya varios clientes reales)
- Upsell de facturas adicionales al superar el tope mensual (ver
  `docs/decisions/0008-tope-facturas-mensual.md`) — depende de que exista
  cobro online
