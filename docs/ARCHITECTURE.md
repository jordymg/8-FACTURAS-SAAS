# Architecture — Facturas SaaS

> AI agents: HOW we build. Stack choices here are settled — see /decisions for rationale. Propose changes as new ADRs, don't silently deviate.

## 1. Stack
| Layer | Choice | ADR |
|-------|--------|-----|
| Frontend | PWA (HTML/JS/CSS, vanilla or minimal framework), camera via `input capture` / MediaDevices | 0001 |
| Backend / API | Python + Flask | 0001 |
| Database | User's own Google Sheet (one spreadsheet per user) + minimal app DB (SQLite → Postgres on Render) for users/subscriptions | 0001, 0002 |
| Auth | Google OAuth 2.0 (scopes: Sheets, Drive file) | 0002 |
| Payments | Mercado Pago suscripciones | 0003 |
| Hosting | Render (single Flask service serves landing + PWA + API) | 0001 |
| AI / external APIs | Gemini (vision) for invoice data extraction | 0001 |

## 2. System overview
Phone (PWA) → photo → Flask API → Gemini (extract) → user reviews in PWA → Flask API → Google Sheets API (append row) + Google Drive API (store image) → month-end export from the sheet.

App DB stores only: user id, Google tokens (encrypted), subscription state, monthly invoice count.

## 3. Data model
### Invoice row (in user's Google Sheet)
| Field | Type | Notes |
|-------|------|-------|
| fecha | date | invoice date |
| tipo_comprobante | string | A/B/C, ticket, etc. |
| numero | string | punto de venta + número |
| cuit_emisor | string | 11 digits |
| razon_social | string | |
| neto | number | |
| iva | number | |
| total | number | |
| imagen_url | string | Drive link |
| cargada_el | datetime | timestamp of save |

### User (app DB)
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| google_sub | string | Google account id |
| email | string | |
| sheet_id | string | user's spreadsheet |
| drive_folder_id | string | invoice images folder |
| tokens | encrypted | OAuth refresh token |
| sub_status | enum | trial / active / blocked |
| invoices_this_month | int | reset monthly, cap 250 |

Relations: User 1—1 Sheet, User 1—1 Drive folder.

## 4. API surface (MVP)
| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| GET | / | Landing page | none |
| GET | /app | PWA | session |
| GET | /auth/google, /auth/callback | OAuth flow | none |
| POST | /api/extract | photo in → extracted fields out (Gemini) | session |
| POST | /api/invoices | save reviewed row to Sheet + image to Drive | session |
| GET | /api/invoices?month= | list rows (from Sheet) | session |
| POST | /api/export?month= | xlsx / share link for the month | session |
| POST | /api/mp/webhook | Mercado Pago subscription events | signature |

## 5. Environments & secrets
- Local: `flask run` with `.env` (GEMINI_API_KEY, GOOGLE_CLIENT_ID/SECRET, MP keys)
- Production: Render web service, auto-deploy from GitHub `master`
- Secrets live in: Render dashboard env vars — never in the repo

## 6. Conventions
- Language: Python 3.11+, type hints
- One Flask app, blueprints per area (`auth`, `api`, `web`)
- Content separated from code: user-facing strings in external editable files
- One terminal command at a time in sessions; complete files, not fragments
- AI agents: never store invoice data in the app DB — the user's Sheet is the datastore
