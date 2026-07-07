# ADR-0010 (planillas): Columnas custom por cliente — pregunta abierta

**Date:** 2026-07-07
**Status:** ABIERTA — no decidido, no implementar todavía

## Contexto
El punto de backlog "migración v1→v2 de planillas ya conectadas" se
reencuadró: el caso real no es migrar planillas viejas (a los clientes
nuevos se les indica crear una planilla nueva con la estructura de la
empresa, ADR-0005 v2), sino **qué hacer cuando un cliente pida una columna
extra propia** — ej. "necesito una columna para X" que no forma parte de la
estructura estándar de 23 columnas.

## Postura del founder (dirección, no solución)
Estar abiertos a este tipo de pedido, pero **sin caer en modificar la
planilla cliente por cliente** de forma ad hoc — eso no escala y complica
mantener una sola estructura de código (`app/services/fields.py`,
`sheets.py::ROW_KEYS`) para todos los usuarios.

## Preguntas sin resolver
- ¿Se soportan columnas custom de alguna forma estandarizada (ej. "columnas
  libres" al final de la tabla, que la app nunca toca pero tampoco pisa)?
- ¿Van al final de la tabla, o en otro lugar?
- ¿La app las ignora por completo (el cliente las agrega y mantiene a mano,
  sin que rompa nada de lo que la app sí escribe)?
- ¿Hay un límite de cuántas columnas custom se permiten?

## Por qué no se resuelve ahora
Es una pregunta de diseño de producto, no un bug ni un pedido urgente hoy
(el MVP se vende a clientes conocidos, ver ADR-0007 del repo general) — se
registra para no perderla, y se retoma en el área de Planillas cuando
aparezca el primer pedido real de este tipo.
