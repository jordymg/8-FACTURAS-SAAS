# PRD — Facturas SaaS (working name)

> AI agents: this is the source of truth for WHAT we're building and WHY. Read ARCHITECTURE.md for HOW, STATUS.md for current state, /decisions for settled choices. Do not re-open decisions recorded in /decisions.

## 1. Problem
Argentine monotributistas and small business owners (validated: founder, founder's uncle) struggle with registering received invoices (compras/gastos). Today they type each invoice by hand into a spreadsheet — or photograph them at month-end and hand the pile to their accountant — which costs hours per month and produces errors. The local market only covers invoice EMISSION (Facturitas, KOE, TusFacturasAPP); the reception side is served only by enterprise tools (Xtract, ERP-integrated, sales-led). See docs/handoffs/2026-07-03-competidores.md.

## 2. Solution in one sentence
A dead-simple PWA that lets a monotributista photograph a received invoice, auto-extract its fiscal data (CUIT, date, amounts, IVA), and save it to their own Google Sheet — ready to export to their accountant at month-end.

## 3. Success metric
10 paying users at ARS $1,999/month within 60 days of launch.

## 4. Users & roles
| Role | Description | Key need |
|------|-------------|----------|
| User (single role) | Monotributista / small business owner in Argentina | Register received invoices with zero friction and hand a clean sheet to their accountant |

## 5. MVP features

### F1 — Photo capture (PWA)
- **Why:** the core friction being removed is manual data entry (§1).
- **Acceptance criteria:**
  - [ ] Given the PWA is open on a phone, when the user taps "Nueva factura", then the camera opens and a photo can be taken or a file uploaded.

### F2 — Data extraction via Gemini
- **Why:** automation of the manual typing (§1). Prototype already achieves ~90% accuracy (Experiment 2).
- **Acceptance criteria:**
  - [ ] Given a legible invoice photo, when it is submitted, then the app returns: fecha, CUIT emisor, razón social, tipo de comprobante, número, neto, IVA, total.
  - [ ] Extraction completes in under 30 seconds.

### F3 — Review & correct screen
- **Why:** ~1 in 10 invoices needs manual correction (Experiment 2); user must trust the data.
- **Acceptance criteria:**
  - [ ] Given extracted data, when displayed, then every field is editable before saving.
  - [ ] Given the user edits a field, when they tap "Guardar", then the edited values (not the raw extraction) are persisted.

### F4 — Save to user's Google Sheet
- **Why:** the sheet IS the deliverable to the accountant (§1); user owns their data.
- **Acceptance criteria:**
  - [ ] Given a first-time user, when they sign in with Google, then the app creates (or connects to) a spreadsheet in their account.
  - [ ] Given a confirmed invoice, when saved, then a new row appears in the user's sheet with all fields plus a link to the invoice image.

### F5 — Invoice image stored in user's Google Drive
- **Why:** backup/audit trail for the accountant, at zero storage cost to us (ADR-0002).
- **Acceptance criteria:**
  - [ ] Given a saved invoice, when the row is created, then the original photo exists in a dedicated folder in the user's Drive and the row links to it.

### F6 — Month-end export
- **Why:** "pass the sheet to the accountant" is the end of the core flow (§2).
- **Acceptance criteria:**
  - [ ] Given a month with saved invoices, when the user taps "Exportar mes", then they get an .xlsx (or a share link to the sheet filtered by month) they can send to their accountant.

### F7 — Subscription at ARS $1,999/month, up to 250 invoices/month
- **Why:** validated price point (Experiment 1: 2/2 yes without hesitation).
- **Acceptance criteria:**
  - [ ] Given a user without an active subscription, when their trial/limit ends, then saving new invoices is blocked with a payment prompt.
  - [ ] Given an active subscriber, when they exceed 250 invoices in a calendar month, then further saves are blocked with an upgrade message.

## 6. Explicitly OUT of scope (MVP)
- ARCA/AFIP integration — deferred: export-to-accountant covers the fiscal need for now
- Multi-user / teams — single-user product
- Native mobile app — PWA only
- Automatic expense categorization — manual data is enough for the accountant
- Statistics dashboard — the Google Sheet already provides this
- Accountant-facing multi-client mode — post-MVP opportunity

## 7. Definition of DONE (MVP)
The MVP is done when ALL of these are true:
- [ ] Founder's uncle uses the app for one full month without help
- [ ] He delivers the resulting sheet to his accountant and the accountant accepts it
- [ ] Deployed and reachable at a public URL (Render)
- [ ] At least one real user (not the builder) completed the full core flow: foto → extracción → revisión → sheet → export

## 8. Risks & open questions
| Risk / question | Impact | Plan |
|-----------------|--------|------|
| Google OAuth verification (Sheets/Drive scopes) can take weeks | Blocks public launch | Start OAuth consent screen verification early; use test users meanwhile |
| Gemini API cost per invoice at scale | Margin erosion | Measure cost/invoice during beta; 250-invoice cap protects worst case |
| Payment rails in Argentina (Mercado Pago) | Blocks F7 | Integrate Mercado Pago suscripciones; manual transfer as fallback for first users |
| Blurry photos degrade extraction (~10% error) | User trust | Review screen (F3) + photo-quality hint before submit |

## 9. Grade
**A (8/8)** — 2026-07-03. Regrade after major edits.
