# Handoff — 2026-07-03 — Mapa de competidores (Experimento 3)

## Resumen de la sesión
Se ejecutó el Experimento 3 del VALIDATION-PLAN (mapa de competidores). Una IA externa entregó 3 competidores (Tickploy, Clarifica, SpomBridge) que **no pudieron verificarse en la web — se descartan como probablemente inventados**. Se verificaron competidores reales mediante búsqueda web.

## Competidores verificados (Argentina)
| Empresa | Foco | Precio | Carga | Público |
|---|---|---|---|---|
| Facturitas (facturitas.app) | **Emisión** de facturas ARCA vía bot WhatsApp | $4.999/mes (WhatsApp), $7.999/mes (web + carga masiva) | WhatsApp, Excel masivo | Monotributistas |
| TusFacturasAPP (tusfacturas.app) | Emisión + gestión (libro IVA compras-ventas, stock, proveedores) | Planes por suscripción | Web, bot WhatsApp, API | Pymes, contadores, monotributistas |
| KOE (koe.com.ar) | **Emisión** por WhatsApp, facturación masiva | Planes mensuales/anuales | WhatsApp | Monotributistas, contadores, empresas |
| Xtract (xtract.app) | **Recepción**: contabilización automática de facturas (lectura + ingreso al ERP), autorización de facturas, digitalización de viáticos | Sin precio público — venta consultiva (contact sales + demo) | Recepción automática, integración con ERP/sistema contable | Empresas: CFOs, gerencias administrativas, cuentas por pagar. Teléfono +54 (Argentina) |

Referencia internacional (lado gastos): Billin, Contasimple, Quipu (España) hacen foto→OCR→registro de gastos, pero no están adaptadas a fiscalidad argentina.

## Conclusión / Decisión
- El mercado argentino está saturado del lado **emisión** de facturas.
- Del lado **recepción** existe Xtract (Argentina), pero apunta a empresas con ERP y CFO, venta consultiva sin precio público. El segmento monotributista / pequeño comercio / autoservicio sigue vacante.
- **Wedge ajustado:** registro de gastos por foto, fiscalidad argentina (CUIT, IVA, CAE), self-service y barato — el "Xtract para monotributistas". No es solo "más barato".
- Referencia de precio de mercado adyacente: ~$5.000 ARS/mes (Facturitas).

## Estado del Validation Gate
- Experimento 3: ✅ CUMPLIDO (gate Q4 pasa a PASS: wedge concreto identificado)
- Experimento 1 (2 conversaciones con precio: tío + ex): ⏳ pendiente, deadline 2026-07-16
- Experimento 2 (dogfooding con métricas): ⏳ pendiente, deadline 2026-07-16
- Gate actual: 3/4 condicional — falta evidencia de pago (Q3)

## Cambios a pushear
1. Crear `docs/handoffs/2026-07-03-competidores.md` con este archivo.
2. Actualizar `docs/STATUS.md` con la versión de abajo.

## STATUS.md actualizado (reemplazar completo)
```markdown
# STATUS

## Current phase
Validation — gate 3/4 condicional (falta Q3: evidencia de pago)

## Done
- Flask/Gemini prototype working
- Validation plan defined (3 experiments)
- Experimento 3 CUMPLIDO: mapa de competidores verificado
  (ver docs/handoffs/2026-07-03-competidores.md)
- Wedge definido: registro de gastos por foto, fiscalidad argentina,
  lado RECEPCIÓN (el mercado local solo cubre emisión)
- Precio de referencia mercado adyacente: ~$5.000 ARS/mes (Facturitas)

## Next
- Experimento 1: 2 conversaciones con precio (tío + ex), deadline 2026-07-16
- Experimento 2: dogfooding 2 semanas con métricas, deadline 2026-07-16
- Al completar: re-correr gate → si 3/4 firme, Discovery + PRD

## Blocked
- PRD, ARCHITECTURE, ROADMAP: hasta pasar el gate

## Decisiones
- 2026-07-03: descartados "Tickploy/Clarifica/SpomBridge" (no verificables,
  probablemente alucinados por IA externa). Usar solo competidores verificados.
```
