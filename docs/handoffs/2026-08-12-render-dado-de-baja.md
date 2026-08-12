# Handoff — 2026-08-12 — Render dado de baja definitivamente, §6 se salta

**De:** Claudito (VPS, `vmi3497965.contaboserver.net`)
**Para:** Jordi (CEO) / Claude Code
**Tipo:** decisión del CEO durante la ejecución de la migración (ADR-0015),
cambia varias secciones vigentes del ADR y del runbook.

## Resumen
Jordi avisó en medio de la ejecución (§5 en curso) que **Render ya fue dado
de baja definitivamente** — no hay vuelta atrás, no está en standby. Esto
invalida varios supuestos que el ADR-0015 y `docs/ops/vps.md` daban por
sentados cuando se escribieron (documentación previa a la ejecución, hecha
antes de saber que la baja iba a ser tan abrupta).

## Decisiones tomadas (por Jordi, ejecutadas/a ejecutar por Claudito)
1. **Se salta §6 completo (migración de datos) — no se hace `pg_dump`/
   `pg_restore` desde Render.** No hay connection string externa que pedir,
   no aplica.
2. **La Postgres local arranca vacía.** La app crea su propio schema al
   levantar (`db.create_all()` + `_ensure_schema()` en `app/__init__.py`,
   como ya documentaba el runbook para el caso normal). Los usuarios que
   existían en Render **se pierden** — no hay forma de recuperarlos, Render
   ya no está. Van a tener que re-loguearse y reconectar su planilla una
   vez en `facturas.mcfly.ar`.
3. Con §6 fuera de juego, se disuelve el problema de orden que había
   señalado Claude Code (restore con `--clean` pisando usuarios reales
   creados durante una corrida temprana de la app) — ya no hay restore que
   pueda pisar nada. Orden simplificado: `sa.json` real + valores del `env`
   → `git pull` en `/srv/facturas-saas` → `systemctl restart facturas` →
   `systemctl status facturas`.

## Contexto: quién tenía usuarios reales en Render
No lo sé desde acá (Claudito no tiene visibilidad de la DB de Render, que
ya no existe). Si había usuarios reales de producción (no solo cuentas de
prueba), es información que solo tiene Jordi — puede valer la pena que lo
confirme para dimensionar el impacto real de "se pierden los usuarios
existentes".

## Cambios a los docs (para que los aplique Claude Code, no yo)
Estas secciones del repo dan por sentado que Render sigue vivo en standby
durante la transición — ya no es cierto:

1. **`docs/decisions/0015-migracion-render-a-vps-propio.md`**:
   - Punto 8 de la Decisión: "La URI de Render se **mantiene** durante toda
     la transición... se saca recién después del cutover confirmado" — ya
     no aplica, Render no existe más, la URI de Render en Google Console
     puede sacarse ahora (o queda inerte, sin urgencia, a criterio de
     Jordi).
   - Sección Consecuencias, "**Reversible durante la transición**: mientras
     Render siga levantado... revertir es volver a apuntar el DNS. Render
     se deja en standby unos días..." — **ya no es reversible de esa
     forma**. Conviene marcar esto explícitamente como cerrado/no vigente.
2. **`docs/ops/vps.md`**:
   - §1.3 (prerrequisitos 🔒): ya no hace falta la "connection string de la
     DB de Render (para el `pg_dump` de §6)".
   - **§6 completo** ("Migración de datos ⏳"): pasa a no aplicar. Sugerido
     dejarlo marcado como "SALTEADO — Render dado de baja antes del
     cutover, 2026-08-12" en vez de borrarlo (valor histórico de por qué se
     saltó).
   - §7 (Cutover): el paso "Dejar Render en standby unos días... recién
     después dar de baja el servicio de Render" ya no aplica — Render ya
     está de baja. El paso de sacar la URI de Render de Google Console deja
     de ser "recién después de confirmar estabilidad" y puede hacerse
     cuando Jordi quiera.
3. **`docs/STATUS.md`**: cuando se cierre la migración, la entrada
   correspondiente debería mencionar que no hubo migración de datos —
   arranque en limpio, usuarios de Render se re-loguean.

## Próximo paso (operativo, en curso)
Sigo esperando: `sa.json` real (el placeholder de antes no sirve) para
completar `/etc/facturas-saas/env` y `/etc/facturas-saas/sa.json`, después
`git pull` + `systemctl restart facturas` + reportar `systemctl status`.
