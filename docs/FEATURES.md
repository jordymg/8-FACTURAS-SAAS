# Catálogo de features — Facturas SaaS

> Documento vivo e INTERNO. No lo lee el cliente final — de acá se derivan
> los pitches de venta y la estrategia de marketing, pero este documento
> puede ser técnico, descriptivo y exhaustivo sin cuidarse de nada.

Este documento es el mapa completo de Facturas SaaS — todo lo que la
empresa hace hoy, lo que está construyendo y lo que imagina hacer. La
empresa crece por features: cada capacidad nueva que se suma al producto
es una entrada acá, con su explicación para cualquier persona, su detalle
técnico y su ficha completa (estado, precio posible, costo, dependencias).
Hoy la primera feature es la carga de facturas por foto; mañana serán
muchas más, y este documento es donde nacen, se detallan y se ordenan. De
acá salen los pitches de venta y la estrategia de marketing.

## Cómo se usa
- Toda feature nueva, cambio sobre una existente o idea futura se registra
  acá como una entrada, aunque arranque casi vacía (así funciona el ciclo
  natural — primero idea, después se especifica).
- Las decisiones que sustentan cada feature siguen viviendo en los ADRs;
  este catálogo las referencia, no las reemplaza.
- La ficha de tags puede simplificarse en el futuro si algún campo resulta
  no usarse.
- **Mantenedor: Claude 1 (CPO)** — toda entrada y cambio con aprobación
  del CEO. Ver `docs/ORGANIGRAMA.md`.

## Ficha de cada entrada (plantilla)
Cada feature se documenta con:

| Campo | Qué es |
|---|---|
| **Online** | Sí / No — si está funcionando en producción hoy |
| **Estado** | Idea / En diseño / En desarrollo / Online / Pausada / Descartada |
| **Área** | App, Planillas, o ambas (quién la dirige, ver docs/ORGANIGRAMA.md) |
| **ADRs relacionados** | Links a las decisiones que la sustentan |
| **Precio posible** | Lo que creemos que se puede cobrar por ella |
| **Costo de realizarla** | Esfuerzo/costo estimado de construirla |
| **Plan** | Si entra en el plan base o es un adicional/upsell |
| **Origen** | Founder / cliente real / detectada por uso |
| **Alta / última actualización** | Fechas |
| **Dependencias** | Qué otra feature o decisión necesita para existir |
| **Métrica de éxito** | Qué señal indica que funciona |

Debajo de la ficha, cada entrada tiene una **explicación para cualquier
persona** (que no conoce el sistema) y el **detalle técnico/funcional**
que haga falta.

---

## Feature 001 — Carga de facturas por foto

| Campo | Valor |
|---|---|
| Online | Sí |
| Estado | Online |
| Área | App + Planillas |
| ADRs relacionados | ADR-0001 a 0010 del repo general; ADR-0001 a 0010 del área Planillas |
| Precio posible | Incluida en el plan base (ARS $1.999/mes, ver docs/decisions/0003-pricing.md) |
| Costo de realizarla | Ya construida (MVP completo) |
| Plan | Base |
| Origen | Founder (visión fundacional del producto) |
| Alta / última actualización | 2026-07-12 / 2026-07-12 |
| Dependencias | Ninguna — es la feature fundacional |
| Métrica de éxito | Facturas cargadas por cliente por mes; precisión de la extracción; correcciones manuales por factura |

**Explicación**: el usuario le saca una foto a una factura de compra desde
el celular. Nuestro sistema lee el comprobante, extrae todos los datos
fiscales (fecha, proveedor, CUIT, importes, IVA por alícuota, percepciones,
retenciones), el usuario los revisa en una tarjeta editable y el registro
queda cargado como una fila nueva en su propia planilla de Google Sheets —
la misma que usa día a día y le entrega a su contador.

**Detalle técnico/funcional**: PWA + Flask + extracción con Gemini
(temperature=0, ADR-0010 general). Escritura vía Service Account en la
planilla del cliente (ADR-0004 general). Estructura v2 de 23 columnas
(ADR-0005/0006 área Planillas), regla de validez del comprobante por 4
vías de autorización con manejo de duda no bloqueante (ADR-0007/0008),
detección de duplicados no bloqueante (ADR-0009), pestaña por año
calendario (ADR-0003 área Planillas), tope mensual soft de 200 facturas
(ADR-0008 general).

---

## Feature 002 — Reportes al contador

| Campo | Valor |
|---|---|
| Online | No |
| Estado | Idea |
| Área | Planillas (probable participación de App) |
| ADRs relacionados | ADR-0003 área Planillas (pestaña anual, ya implementada — es la base) |
| Precio posible | A definir |
| Costo de realizarla | A definir |
| Plan | A definir |
| Origen | Founder |
| Alta / última actualización | 2026-07-12 / 2026-07-12 |
| Dependencias | Pestaña anual (ya online) |
| Métrica de éxito | A definir |

**Explicación**: la planilla organiza todo el año en una sola hoja; para
ver la data financiera mes a mes, el sistema genera reportes mensuales —
un detalle imprimible pensado para entregarle al contador.

**Detalle técnico/funcional**: a definir. Por ahora es una idea abierta a
propósito — se va a especificar en el área Planillas (contenido del
reporte, dónde vive, cuándo se genera) antes de tocar código.
