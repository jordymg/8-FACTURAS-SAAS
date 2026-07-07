# ADR-0009 (planillas): UX de detección de duplicados

**Date:** 2026-07-07
**Status:** ADOPTADA — no implementada todavía

## Contexto
La detección de duplicados por `cuit`+`numero` ya está decidida (ADR-0002,
"Python antes de escribir"), pero faltaba definir qué hace la app cuando
efectivamente detecta uno — el ADR-0002 solo decía que la detección existe,
no qué pasa después. Además, se ajustó el criterio de match: 2 campos
(`cuit`+`numero`) eran insuficientes — se pasa a 3.

## Decisión
**Criterio de match, actualizado**: `cuit` + `numero` (N° de Factura) +
`fecha` (Emisión) — los 3 tienen que coincidir para considerarlo duplicado.
Corrige/precisa el criterio de 2 campos del ADR-0002.

Al detectar un duplicado, la tarjeta de revisión muestra un **aviso bien
visible, antes del botón de enviar**: "Esta factura ya la subiste el
[fecha] a tu planilla" (usando la `cargada_el` de la fila existente).

**No bloquea.** Si el usuario envía la factura igual, se toma como
confirmación de que la quiere cargar de todas formas — mismo principio de
no bloqueo que los campos en rojo del [ADR-0008](0008-manejo-de-duda-no-bloqueante.md)
(antes referenciado como ADR-0006 en la conversación de origen; ver esa
corrección de numeración).

## Consecuencias
- Requiere **buscar el duplicado en la planilla** antes de mostrar la
  tarjeta (justo después de la extracción con Gemini) — comparando
  `cuit`+`numero`+`fecha` del comprobante recién extraído contra las filas
  ya cargadas.
- Requiere traer la `cargada_el` de la fila existente para mostrarla en el
  aviso.
- Implementación: en curso.
