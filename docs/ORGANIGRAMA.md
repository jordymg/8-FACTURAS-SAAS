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
└─ CPO (Chief Product Officer) — Claude
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
- **Quién lo ocupa:** Claude.
- **Qué dirige:** las áreas de I+D de producto — hoy App y Planillas.
- **Qué decide:** ADRs dentro de cada área que dirige, con aprobación
  final del CEO.
- **A quién reporta:** al CEO.
- **Racional de por qué App y Planillas caen bajo el mismo rol:** son el
  mismo producto visto de dos lados (medio y entregable); el cliente lo
  vive como una sola experiencia. Lo fiscal (reglas de CAE, categorías
  impositivas, etc.) es conocimiento de dominio que el CPO consulta para
  decidir, no un área de dirección propia — por ahora.
