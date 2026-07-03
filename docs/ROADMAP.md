# Roadmap — Facturas SaaS

> AI agents: work only on the CURRENT phase. Do not start future phases without an explicit instruction.

## Phase 1 — Core flow end-to-end (CURRENT)
Goal: one user (the founder) completes foto → extracción → revisión → Sheet with the production stack.
- [ ] Port Flask/Gemini prototype into repo structure — depends on: —
- [ ] Google OAuth flow + create/connect user Sheet & Drive folder — depends on: —
- [ ] PWA: capture screen + review/edit screen — depends on: prototype ported
- [ ] POST /api/invoices: append row + upload image — depends on: OAuth
- [ ] Deploy to Render (single service) — depends on: all above

Exit criterion: founder saves a real invoice from his phone to his own Sheet via the public URL.

## Phase 2 — Beta with real users
Goal: uncle + 1 more user run a full month unassisted.
- [ ] Month filter + export (.xlsx / share link)
- [ ] Photo-quality hint + error handling on extraction
- [ ] Onboarding: first-run explains flow in 3 screens
- [ ] Invoice counter + 250/month cap (soft, no payment yet)

Exit criterion: PRD §7 items 1–2 true (uncle's month + accountant accepts the sheet).

## Phase 3 — Launch
- [ ] Mercado Pago suscripciones ($1,999/month) + blocking logic
- [ ] Landing page (served from same Flask service)
- [ ] Deploy to production with custom domain
- [ ] Success metric tracking in place (paying users count)
- [ ] First real paying user completes core action

## Later / icebox
- ARCA/AFIP integration
- Multi-user / teams
- Native app
- Automatic categorization
- Stats dashboard
- Accountant multi-client mode
