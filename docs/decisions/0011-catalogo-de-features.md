# ADR-0011: Catálogo de features (docs/FEATURES.md)

**Date:** 2026-07-12
**Status:** ADOPTADA

## Contexto
La empresa se piensa como algo que crece acoplando features que con el
tiempo exceden la carga de facturas. Faltaba un lugar único donde las
features (vigentes, en diseño, ideas) nazcan, se detallen y se ordenen —
hasta ahora quedaban repartidas entre ADRs, el backlog de PRODUCTO.md y
conversaciones. Además, el founder quiere que los pitches de venta y la
estrategia de marketing se deriven de un documento fuente.

## Decisión
- Se crea `docs/FEATURES.md` en el repo general (nivel PRD/ROADMAP/STATUS,
  transversal a las áreas): catálogo vivo de features.
- Es un documento **interno** — técnico, descriptivo y exhaustivo. El
  cliente no lo lee; los pitches se derivan de él.
- La descripción inicial presenta a la empresa por su capacidad de crecer
  por features, sin definirla solo por la carga de facturas.
- Cada entrada lleva una ficha de tags — online, estado, área, ADRs
  relacionados, precio posible, costo de realizarla, plan, origen,
  fechas, dependencias, métrica de éxito — más una explicación para
  cualquier persona y el detalle técnico/funcional. Los tags pueden
  simplificarse en el futuro si alguno no se usa.
- El precio se registra en dos dimensiones por feature: lo que se cree
  que se puede cobrar y lo que cuesta realizarla. El modelo final de
  cobro (por feature o por paquete) queda abierto.
- Las features nuevas pueden entrar como **idea casi vacía** — se
  especifican con el tiempo. Primera idea registrada así: "Reportes al
  contador".

## Alternativas consideradas
- Ubicarlo en docs/areas/: descartado — las áreas son por producto
  interno y este documento las cruza a todas.
- Carpeta nueva docs/product/: descartada por ahora — sería una carpeta
  con un solo archivo.
- Documento con doble capa (vendible + interna) para que lo lea el
  cliente: descartado — el founder definió que es 100% interno.

## Consecuencias
- Toda feature nueva o cambio de feature se registra en FEATURES.md
  además de sus ADRs (el catálogo referencia, no reemplaza).
- El backlog de ideas de docs/areas/planillas/PRODUCTO.md punto 8 sigue
  existiendo por ahora; su relación con el catálogo (absorción o
  convivencia) queda abierta.
- La feature "Reportes al contador" queda registrada como idea; su
  diseño (contenido del reporte, dónde vive, cuándo se genera) se
  discute en el área Planillas antes de implementar nada.
