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

## Post-MVP
- [ ] Guardar la imagen del comprobante en el Drive del cliente (`Facturas/{año}/{mes}/`,
      nombre `{fecha}_{proveedor}_{numero}.jpg`) — depende de: resultado del experimento
      aislado de OAuth con scope `drive.file` (fuera de este repo, ver STATUS.md)

Exit criterion: founder saves a real invoice from su celular a su propio Sheet via la URL pública. ✅ cumplido — probado en producción real (con un bug encontrado y ya resuelto en el camino).

## Phase 2 — Beta with real users
Goal: uncle + 1 more user run a full month unassisted.
- [ ] Month filter + export (.xlsx / share link)
- [ ] Photo-quality hint + error handling on extraction
- [ ] **Prioridad alta pre-lanzamiento**: reintentos automáticos ante 503 de
      Gemini + mensaje de error amigable (todavía no implementado)
- [ ] Onboarding: first-run explains flow in 3 screens
- [ ] Invoice counter + 250/month cap (soft, no payment yet)

Exit criterion: PRD §7 items 1–2 true (uncle's month + accountant accepts the sheet).

## Phase 3 — Launch
- [ ] Mercado Pago suscripciones ($1,999/month) + blocking logic
- [ ] Landing page (served from same Flask service)
- [ ] Deploy to production with custom domain
- [ ] Success metric tracking in place (paying users count)
- [ ] First real paying user completes core action
- [ ] **Política de acceso de soporte definida**: cuando un cliente necesita
      ayuda para cargar o revisar su planilla, podemos entrar a verla (la
      Service Account ya tiene acceso Editor) — reflejar esto en los
      términos de uso antes del lanzamiento (ver
      `docs/decisions/0004-service-account-sheets.md` para el porqué de que
      la SA tenga ese acceso)

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
