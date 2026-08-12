# Handoff — 2026-08-11 — Inspección §2.1 del runbook VPS (previa a provisión)

**De:** Claudito (VPS, `vmi3497965.contaboserver.net`)
**Para:** Jordi (CEO) / Claude Code
**Tipo:** informativo, no de cierre de sesión — no requiere reemplazar `docs/STATUS.md`.

## Resumen
Antes de tocar nginx/certbot/ufw, corrí la inspección que pide la nueva
§2.1 de `docs/ops/vps.md` (agregada por Claude Code tras confirmar que el
VPS no está vacío). Resultado completo abajo, con la decisión propuesta
para seguir con §2.2 en adelante.

## Hallazgos

**Puertos 80 / 443 / 8000 / 300x** (`ss -tlnp`):
- `80` y `443`: nginx (5 workers), escuchando en `0.0.0.0` e IPv6.
- `3001`: proceso `node` de PM2 (`cloudcli`).
- `3002`: `next-server` de PM2 (`losa-radiante`).
- `8000`: **libre** — nada escuchando. Usable tal cual lo sugiere el
  runbook para gunicorn.

**Reverse proxy:** solo `nginx` instalado (`/usr/sbin/nginx`). No hay
Caddy ni Apache.

**PM2** (`pm2 list`, user `jordi`, namespace `default`):
```
id  name            status   uptime
0   cloudcli        online   17h
1   losa-radiante   online   14h
```

**certbot / Let's Encrypt:**
- certbot ya instalado y en uso (no confundir con el `certbot certificates`
  que ya había corrido antes de este handoff).
- Certificados existentes: `code.mcfly.ar` y `mcfly.ar` (ambos ECDSA,
  vencen 2026-11-08/09).
- Timer de auto-renovación activo (`certbot.timer`), corrió hace 21 min,
  próxima corrida en ~9h — funcionando.

**ufw** (`ufw status verbose`):
- **Activo**, default `deny incoming` / `allow outgoing`.
- Reglas: `22/tcp`, `80/tcp`, `443/tcp` permitidos (IPv4 e IPv6).

## Decisión propuesta (para que la confirme Jordi antes de seguir)
1. **Reusar el nginx y el certbot existentes** — no instalar ninguno de
   los dos, coincide con el caso "ya están" que contempla §2.1/§4.3/§4.4
   del runbook.
2. **Puerto local para gunicorn: `8000`** — confirmado libre, tal cual lo
   documenta el runbook, sin necesidad de cambiarlo.
3. **No tocar `ufw`** — ya está activo con las reglas correctas
   (22/80/443), no se reconfigura como parte de esta migración.
4. Seguir con §2.2 tal cual: `sudo apt install -y postgresql
   postgresql-contrib python3-venv python3-pip` (sin `apt upgrade`, ya
   acordado con Jordi).

## Cambios al repo
**Ninguno necesario.** El runbook ya contempla en términos genéricos el
escenario "nginx/certbot ya están, se reusan" — estos hallazgos concretos
confirman ese escenario, no lo contradicen. No hace falta editar
`docs/ops/vps.md`. Si más adelante Jordi/Claude Code prefieren dejar
"puerto 8000 confirmado" por escrito en vez de "puerto libre a confirmar",
queda a su criterio — no es bloqueante.

## Próximo paso
A la espera de luz verde para seguir con §2.2 (instalar
`postgresql`/`python3-venv`), §3 (crear DB y usuario Postgres locales),
y §4.1–4.3 (clonar el repo en `/srv`, systemd apuntando a `127.0.0.1:8000`,
agregar un `server` block **nuevo** para `facturas.mcfly.ar` en nginx sin
tocar los de `mcfly.ar`/`code.mcfly.ar`). Certbot (§4.4) queda pendiente de
que el DNS de `facturas.mcfly.ar` resuelva (🔒, todavía no confirmado).
