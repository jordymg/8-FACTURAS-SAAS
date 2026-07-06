# Área: Planillas

I+D del producto **"PLANILLA FACTURAS COMPRAS"**. Acá se discute y decide TODO lo
relativo a la planilla: diseño, estructura, fórmulas, creación, mantenimiento,
mejora, entrega al contador.

Analogía: es el área de diseño + I+D de un producto dentro de una fábrica — la
"fábrica" es Facturas SaaS, y la planilla es uno de sus productos (el
entregable real que recibe el cliente final, el contador).

## Contenido de esta área
| Archivo | Qué contiene |
|---|---|
| `PRODUCTO.md` | Definición del producto: qué es, estructura, metodología, ciclo de vida, reglas, formato, versionado, backlog |
| `STATUS.md` | Estado vivo de este producto puntual (no confundir con el STATUS.md general del repo) |
| `decisions/` | ADRs propios de este producto (cambios de estructura, fórmulas, versión) |

## Regla
Todo cambio de estructura de la planilla (agregar/sacar/renombrar columnas,
cambiar de plantilla) se decide acá, con un ADR en `decisions/`, antes de
tocar `app/services/fields.py`.
