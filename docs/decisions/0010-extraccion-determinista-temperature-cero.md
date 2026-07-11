# ADR-0010: Extracción de Gemini con temperature=0 (determinista)

**Date:** 2026-07-11
**Status:** ADOPTADA e IMPLEMENTADA

## Contexto
El founder probó subir la misma foto de una factura varias veces y obtuvo
valores levemente distintos entre una extracción y otra (ver Issue #005,
`docs/ISSUES.md`).

## Decisión
`app/services/gemini.py::extract_invoice()` fija `temperature=0` en el
`GenerateContentConfig` de la llamada a Gemini.

**Por qué**: la `temperature` controla cuánta variación/aleatoriedad tiene
el modelo al generar una respuesta. Sirve para texto creativo (donde
distintas respuestas válidas son deseables), pero para extraer datos de un
comprobante hay una sola lectura correcta — queremos que el modelo busque
siempre la interpretación más probable, no que "varíe" entre llamadas. Sin
fijarla, el valor por defecto permite esa variación, que es exactamente lo
que se vio como bug.

## Alternativas consideradas
- Dejar la temperature por defecto y resolver la inconsistencia comparando
  contra la extracción anterior: descartada — mucho más compleja, y no
  ataca la causa real (la aleatoriedad en sí), solo la disimula.

## Consecuencias
- Probado: dos llamadas seguidas con la misma imagen de prueba dieron un
  resultado idéntico (antes del fix no se había medido formalmente la
  inconsistencia, pero el reporte del founder con una foto real la
  confirmó).
- `temperature=0` reduce drásticamente la variación pero no es una
  garantía matemática absoluta de determinismo total al 100% — es una
  limitación conocida de los LLMs a nivel de infraestructura (no de este
  proyecto). Si vuelve a pasar con una foto real, reportarlo como nuevo
  Issue en `docs/ISSUES.md`.
- Si en el futuro se necesita AJUSTAR este valor (ej. si alguna vez se usa
  el modelo para algo que sí se beneficie de variación), el único lugar
  donde tocar es `app/services/gemini.py`, el parámetro `temperature` del
  `GenerateContentConfig`.
