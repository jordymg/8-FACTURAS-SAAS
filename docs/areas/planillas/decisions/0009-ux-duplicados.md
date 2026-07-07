# ADR-0009 (planillas): UX de detección de duplicados

**Date:** 2026-07-07
**Status:** ADOPTADA — no implementada todavía

## Contexto
La detección de duplicados por `cuit`+`numero` ya está decidida (ADR-0002,
"Python antes de escribir"), pero faltaba definir qué hace la app cuando
efectivamente detecta uno — el ADR-0002 solo decía que la detección existe,
no qué pasa después. Se ajustó el criterio de match dos veces, ambas por
casos reales encontrados al probar:
1. 2 campos (`cuit`+`numero`) eran insuficientes → se pasó a 3, sumando
   `fecha`.
2. Probando con una **factura en negro** (sin CAE, sin CUIT visible — común
   en tickets informales), el chequeo nunca detectaba el duplicado: al
   faltar el CUIT, la búsqueda ni se ejecutaba. `cuit` es exactamente el
   campo más probable de faltar en el tipo de comprobante que más necesita
   este aviso. Se reemplaza `cuit` por `proveedor` (nombre del emisor).

## Decisión
**Criterio de match, final**: `proveedor` + `numero` (N° de Factura) +
`fecha` (Emisión) — los 3 tienen que coincidir para considerarlo duplicado.
`proveedor` se compara sin importar mayúsculas/espacios extra (ej.
"CORRALON SA" y "Corralon SA" matchean). Reemplaza el criterio de
`cuit`+`numero` del ADR-0002 (y la versión intermedia `cuit`+`numero`+`fecha`
de este mismo ADR).

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
  `proveedor`+`numero`+`fecha` del comprobante recién extraído contra las
  filas ya cargadas.
- También se chequea contra otras fotos de la **misma tanda** (si se suben
  2 fotos de la misma factura juntas, ninguna está guardada todavía, así que
  el chequeo contra el Sheet no las vería entre sí).
- Requiere traer la `cargada_el` de la fila existente para mostrarla en el
  aviso.
- Riesgo aceptado: dos proveedores distintos con el mismo nombre exacto (muy
  poco común) y casualmente el mismo número de factura y fecha darían un
  falso positivo — aceptable porque no bloquea, solo avisa.
- Implementado.
