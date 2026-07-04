# Architecture — Facturas SaaS

> AI agents: HOW we build. Stack choices here are settled — see /decisions for rationale. Propose changes as new ADRs, don't silently deviate.

## 1. Stack
| Layer | Choice | ADR |
|-------|--------|-----|
| Frontend | PWA (HTML/JS/CSS, vanilla), drag&drop multi-archivo + cámara | 0001 |
| Backend / API | Python + Flask | 0001 |
| Database | User's own Google Sheet (one spreadsheet per user) + minimal app DB (SQLite → Postgres on Render) for users/subscriptions | 0001, 0002, 0004 |
| Auth | Google OAuth 2.0 — solo identidad (scopes: openid, email). Sheets se escriben con una Service Account, no con el token del usuario | 0004 |
| Payments | Mercado Pago suscripciones | 0003 |
| Hosting | Render (single Flask service serves landing + PWA + API) | 0001 |
| AI / external APIs | Gemini (vision, `response_schema` estructurado) for invoice data extraction | 0001, 0004 |

## 2. System overview
Foto/PDF (PWA, uno o varios) → Flask API → Gemini extrae los 9 campos (la imagen solo
vive en memoria durante este paso, no se persiste — MVP sin storage de imagen, ver
STATUS.md) → usuario revisa en tarjetas editables → Flask API → Service Account
escribe la fila en el Sheet del usuario (`gspread`) → export a fin de mes desde la
propia planilla.

App DB (`User`) guarda solo: identidad de Google, `spreadsheet_id` conectado, estado de
suscripción, contador de facturas del mes. No hay tokens OAuth que persistir — el login
es solo para identidad, la Service Account hace todo el acceso a Sheets.

## 3. Data model
### Invoice row (en la planilla del usuario, plantilla "Facturas AFIP")
Definido en `app/services/fields.py` — único lugar a tocar si cambian/agregan campos
o plantillas.

| Field | Type | Notes |
|-------|------|-------|
| fecha | date | AAAA-MM-DD |
| proveedor | string | razón social del emisor |
| cuit | string | CUIT del emisor, 11 dígitos |
| tipo | string | Factura A/B/C, Presupuesto, Nota de Crédito, etc. |
| numero | string | punto de venta + número |
| neto | number | vacío en Factura B/C si no se discrimina |
| iva | number | vacío en Factura B/C si no se discrimina |
| total | number | |
| moneda | string | ARS / USD |
| imagen | string | siempre vacío en el MVP — no se persiste la imagen (post-MVP) |
| cargada_el | datetime | timestamp del guardado |

### User (app DB)
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| google_sub | string | Google account id |
| email | string | |
| spreadsheet_id | string | planilla del usuario, compartida con la SA |
| sub_status | enum | trial / active / blocked |
| invoices_this_month | int | reset monthly, cap 250 |

## 4. API surface (MVP)
| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| GET | / | Landing page | none |
| GET | /app | PWA (captura + revisión + últimas facturas) | session |
| GET | /app/config | Conectar planilla (mostrar email de la SA, validar acceso) | session |
| GET | /auth/google, /oauth2callback | Login (identidad, sin scopes sensibles) | none |
| POST | /api/sheet/connect | valida que la SA puede abrir la planilla y la guarda en el User | session |
| POST | /api/extract | uno o varios archivos in → fields extraídos out (Gemini) por archivo | session |
| POST | /api/invoices | guarda fila revisada en el Sheet (SA); la imagen no se persiste (MVP) | session |
| GET | /api/invoices?month= | list rows (from Sheet) | session |
| POST | /api/export?month= | xlsx / share link for the month (pendiente) | session |
| POST | /api/mp/webhook | Mercado Pago subscription events (pendiente) | signature |

## 5. Environments & secrets
- Local: `flask run --port 5050` (el redirect_uri de OAuth registrado en Google Cloud
  Console para este client_id es `http://localhost:5050/oauth2callback` — entrar por
  `localhost`, no `127.0.0.1`, o Google rechaza con `redirect_uri_mismatch`) con `.env`
  (`GEMINI_API_KEY`, `GOOGLE_CLIENT_ID/SECRET`, `GOOGLE_SA_CREDENTIALS_FILE`)
- Credenciales de la Service Account: archivo JSON fuera del repo (`instance/`,
  gitignored), path apuntado por `GOOGLE_SA_CREDENTIALS_FILE`
- Production: Render web service, auto-deploy from GitHub `master`
- Secrets live in: Render dashboard env vars — never in the repo

## 6. Conventions
- Language: Python 3.11+, type hints
- One Flask app, blueprints per area (`auth`, `api`, `web`)
- Content separated from code: user-facing strings in external editable files
- One terminal command at a time in sessions; complete files, not fragments
- AI agents: never store invoice data in the app DB — the user's Sheet is the datastore
