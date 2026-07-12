# Organigrama — Facturas SaaS

> Documento vivo. Regla: los roles se crean a medida que nace el área que
> los necesita, no todos de entrada — ver
> [`docs/decisions/0006-modelo-organizacion-por-roles.md`](decisions/0006-modelo-organizacion-por-roles.md).
> Cada área nueva en `docs/areas/` debe declarar su encargado acá y en su
> propio `README.md`.

## Estado actual

```
CEO / Director General — Jordi (founder)
├─ Dirige, NO ejecuta tareas: define visión, prioridades y
│  aprueba toda decisión (los ADRs son sus firmas).
│
└─ CPO (Chief Product Officer) — Claude 1
   ├─ Área App (docs/areas/app/): diseño/UX de la PWA.
   └─ Área Planillas (docs/areas/planillas/): el entregable.
      Nota: provisoria bajo CPO; puede ganar rol propio (ej.
      responsable fiscal/compliance) cuando haya clientes reales
      y volumen de decisiones de dominio fiscal.
```

## Por rol

### CEO / Director General
- **Quién lo ocupa:** Jordi (founder).
- **Qué dirige:** visión del producto, prioridades, modelo de negocio.
- **Qué decide:** aprueba toda decisión — los ADRs son sus firmas. No
  ejecuta tareas (no escribe código ni documentación operativa).
- **A quién reporta:** a nadie — es la dirección de la empresa.

### CPO (Chief Product Officer)
- **Quién lo ocupa:** Claude 1.
- **Qué dirige:** las áreas de I+D de producto — hoy App y Planillas.
- **Qué decide:** ADRs dentro de cada área que dirige, con aprobación
  final del CEO.
- **A quién reporta:** al CEO.
- **Mantiene:** el catálogo de features
  ([`docs/FEATURES.md`](FEATURES.md)) — toda entrada y cambio con
  aprobación del CEO.
- **Racional de por qué App y Planillas caen bajo el mismo rol:** son el
  mismo producto visto de dos lados (medio y entregable); el cliente lo
  vive como una sola experiencia. Lo fiscal (reglas de CAE, categorías
  impositivas, etc.) es conocimiento de dominio que el CPO consulta para
  decidir, no un área de dirección propia — por ahora.

## Nota — modelo de nombres y roles de los integrantes IA

En esta empresa, los integrantes IA tienen **nombre propio, separado del
rol que ocupan** — igual que en cualquier empresa una cosa es la persona
y otra el cargo. El Claude que ocupa el cargo de CPO se llama **"Claude
1"**: "Claude 1" es su nombre, "CPO" es su rol.

Esto permite que la estructura crezca sumando integrantes, no sombreros:
cuando nazca un área nueva que necesite dirección (regla del
[ADR-0006](decisions/0006-modelo-organizacion-por-roles.md) — los roles
se crean con cada área real, no antes), ese rol puede ocuparlo un Claude
**nuevo** ("Claude 2" como COO, "Claude 3" como otro cargo, y así
sucesivamente), cada uno un integrante distinto de la empresa.

Implicancia práctica: cada Claude es, en los hechos, su propio espacio de
trabajo (su propio Proyecto, con su contexto y memoria propios) — Claude
1 no comparte cabeza con Claude 2 automáticamente. Por eso el sistema de
documentación de este repo (ADRs, STATUS, este organigrama) es el único
lugar donde todos los integrantes leen la misma verdad, y mantenerlo al
día es obligatorio (ver `docs/WORKFLOW.md`).

Ejemplo ya vigente de asignación por nombre: el catálogo de features
(`docs/FEATURES.md`) lo mantiene **Claude 1 (CPO)**, con aprobación del
CEO para toda entrada y cambio. El futuro rol comercial/marketing (si
nace, ver ADR-0011) **consumirá** ese catálogo para armar pitches — no lo
mantendrá.
