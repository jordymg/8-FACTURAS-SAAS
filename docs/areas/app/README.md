# Área: App (diseño/UX)

## Qué es
I+D de lo que el cliente **ve y toca** — la PWA que usa para sacar la foto,
revisar los datos y conectar su planilla. Es la contracara del área
[`planillas`](../planillas/): Planillas diseña el **entregable** (lo que
recibe el contador), App diseña el **medio** por el que el cliente carga los
datos. El README general lo resume como "la app es el medio; la planilla es
el entregable real".

Esta área **no está atada al hosting actual** (Render) — sobrevive a
cualquier migración de infraestructura futura, porque es sobre diseño y
experiencia de uso, no sobre dónde corre el servicio.

## Encargado
**CPO** — ver [`docs/ORGANIGRAMA.md`](../../ORGANIGRAMA.md).

## Alcance
- Identidad visual: colores, tipografía, logo.
- Pantallas y navegación (landing, configuración, captura, revisión,
  últimas facturas).
- Flujo de uso de punta a punta: foto → revisión → guardado.
- Formulario de revisión: layout con ~20 campos, pensado para mobile —
  estados visuales (vacío, inválido, en duda/baja certeza — ver
  [`decisions/0008` del área planillas](../planillas/decisions/0008-manejo-de-duda-no-bloqueante.md)
  para el mecanismo de duda que esta área debe reflejar visualmente).
- Pantalla de espera / cold start (ver
  [`docs/decisions/0005-pantalla-espera-cold-start.md`](../../decisions/0005-pantalla-espera-cold-start.md)
  del repo general).
- Onboarding: cómo se explica y se hace la conexión de la planilla la
  primera vez.
- Mensajes de error y estados vacíos.

## Qué NO es
- La estructura de la planilla (columnas, fórmulas, formato de Sheets) —
  eso es del área [`planillas`](../planillas/).
- La lógica de backend/extracción (prompt de Gemini, Service Account,
  validaciones en Python) — eso vive en el repo general
  (`app/services/`, `docs/decisions/`).
- Pricing o modelo de negocio — eso son ADRs generales
  (`docs/decisions/0003-pricing.md`).

## Contenido de esta área
| Archivo | Qué contiene |
|---|---|
| `PRODUCTO.md` | Definición del producto (pantallas, flujos, estados) — pendiente, sale de una conversación de diseño dedicada |
| `STATUS.md` | Estado vivo de este producto puntual |
| `decisions/` | ADRs propios de decisiones de diseño/UX |

## Regla
Todo cambio de flujo o pantalla significativo se decide acá, con un ADR en
`decisions/`, antes de tocar `templates/`, `static/js/app.js` o
`static/css/app.css` — mismo principio que el área Planillas.
