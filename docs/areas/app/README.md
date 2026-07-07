# Área: App (diseño/UX)

I+D del **diseño y la experiencia de uso de la app** — la PWA que el cliente
usa para sacar la foto, revisar los datos y conectar su planilla. Acá se
discute y decide todo lo relativo a pantallas, flujos de uso, y estados de
la interfaz (no la planilla en sí — eso vive en
[`docs/areas/planillas/`](../planillas/)).

Analogía: si `planillas` es el diseño del **producto entregable** (lo que
recibe el contador), esta área es el diseño del **canal** por el que el
cliente carga los datos — el README general lo resume como "la app es el
medio; la planilla es el entregable real".

## Alcance
- Diseño de pantallas (landing, configuración, captura, revisión, últimas
  facturas).
- Flujo de uso de punta a punta (onboarding, carga diaria, estados de
  error).
- Formulario de revisión: layout, agrupación de campos, estados visuales
  (vacío, inválido, en duda/baja certeza — ver
  [`decisions/0008` del área planillas](../planillas/decisions/0008-manejo-de-duda-no-bloqueante.md)
  para el mecanismo de duda que esta área debe reflejar visualmente).
- Pantalla de espera / cold start (ver
  [`docs/decisions/0005-pantalla-espera-cold-start.md`](../../decisions/0005-pantalla-espera-cold-start.md)
  del repo general).

## Contenido de esta área
| Archivo | Qué contiene |
|---|---|
| `PRODUCTO.md` | Definición del producto (pantallas, flujos, estados) — pendiente, sale de una conversación de diseño dedicada |
| `STATUS.md` | Estado vivo de este producto puntual |
| `decisions/` | ADRs propios de decisiones de diseño/UX |

## Regla
Todo cambio de flujo o pantalla significativo se decide acá, con un ADR en
`decisions/`, antes de tocar `templates/`, `static/js/app.js` o
`static/css/app.css`.
