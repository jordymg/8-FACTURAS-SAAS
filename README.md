# Facturas SaaS

**Foto de factura → datos listos para tu contador.** PWA para monotributistas y pequeños comercios argentinos: sacás una foto de la factura recibida, la app extrae los datos fiscales (CUIT, fecha, IVA, total), los revisás y se guardan en TU planilla de Google Sheets, con la imagen original en TU Google Drive. A fin de mes, exportás y se la pasás al contador.

> **AI agents: read `/docs` before doing anything. Update `docs/STATUS.md` before ending any session. Follow `docs/WORKFLOW.md`.**

## Estado
Fase 1 en construcción — ver [`docs/STATUS.md`](docs/STATUS.md) y [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Stack
PWA (HTML/JS) · Flask (Python) · Gemini (extracción) · Google Sheets + Drive API (datos del usuario, en su cuenta) · Render (hosting) · Mercado Pago (suscripción, Fase 3).

Decisiones fundamentadas en [`docs/decisions/`](docs/decisions/).

## Correr local
```bash
pip install -r requirements.txt
cp .env.example .env   # completar claves
flask --app wsgi run
```

## Documentación
| Doc | Qué contiene |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Qué construimos y por qué (grade A) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Cómo: stack, data model, API |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Fases y tareas |
| [`docs/STATUS.md`](docs/STATUS.md) | Estado vivo del proyecto |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | Protocolo multi-IA y handoffs |
| [`VALIDATION.md`](VALIDATION.md) | Gate 4/4 y evidencia |

## Modelo de negocio
Plan único: **ARS $1.999/mes, hasta 250 facturas** (imágenes y export incluidos).
