# Runbook operativo — VPS propio (facturas.mcfly.ar)

> **Qué es este documento.** El how-to de operar la app en el servidor
> propio: cómo está (o va a estar) montada, y cómo se hacen las tareas que
> antes Render hacía solas (TLS, gestión de proceso, backups, deploy). No
> es un ADR — la *decisión* de migrar está en
> [ADR-0015](../decisions/0015-migracion-render-a-vps-propio.md); esto es la
> *ejecución*. Mantener este archivo al día cada vez que cambie algo del
> server.
>
> **Estado:** la migración está **planificada, no ejecutada todavía**. Las
> secciones marcadas ⏳ son pasos a hacer; las marcadas 🔒 son **solo del
> CEO (humano)** y no las puede hacer Claudito.

---

## 0. Destino: cómo queda montado el server

```
Internet (HTTPS)
   │
   ▼
facturas.mcfly.ar  ──►  nginx (:443, TLS Let's Encrypt)   [reverse proxy]
                            │  proxy_pass
                            ▼
                        gunicorn (127.0.0.1:8000)          [systemd, Restart=always]
                            │
                            ├─►  Postgres local (127.0.0.1:5432)   [datos de la app]
                            ├─►  Gemini API           (externo, extracción)
                            └─►  Google Sheets API     (externo, Service Account)
```

- **SO:** Ubuntu 24.04 (Contabo).
- **Dominio:** `facturas.mcfly.ar`.
- **App:** Flask servido por gunicorn, detrás de nginx. `ProxyFix` en la
  app (`app/__init__.py`) ya está — **no se toca**; depende de que nginx
  reenvíe los headers correctos (ver §4).
- **DB:** Postgres self-hosted (ADR-0015 §3). Los datos de facturas NO
  viven acá — viven en el Google Sheet de cada cliente. La DB local guarda
  solo identidad, planilla conectada y contador.

---

## 1. Prerrequisitos 🔒 (solo el CEO)

Nada de esto lo puede hacer Claudito. Hacerlos **antes** de que Claudito
empiece a provisionar, o el login/HTTPS no van a funcionar.

1. **DNS.** En el proveedor del dominio, crear un registro **A**
   `facturas.mcfly.ar` → IP del VPS. Verificar que propague
   (`dig facturas.mcfly.ar +short` debe devolver la IP).
2. **Google Cloud Console — redirect URI.** En el proyecto de la app →
   APIs y servicios → Credenciales → el cliente OAuth 2.0 de la app →
   "URIs de redireccionamiento autorizados" → Agregar:
   ```
   https://facturas.mcfly.ar/oauth2callback
   ```
   **No borrar la URI de Render todavía** — se saca recién después del
   cutover confirmado (§7), para poder volver atrás sin quedarse sin login.
3. **Secretos a mano** para pegar en el server (§5). Los **valores** los
   pone el CEO; ni Claudito ni Claude Code los tocan:
   `SECRET_KEY`, `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`,
   `GOOGLE_CLIENT_SECRET`, el JSON de la Service Account, y la connection
   string de la DB de Render (para el `pg_dump` de §6).

---

## 2. Provisión del sistema base ⏳ (Claudito)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip \
     postgresql postgresql-contrib \
     nginx \
     certbot python3-certbot-nginx \
     git ufw
```

Firewall:
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'      # abre 80 y 443
sudo ufw enable
sudo ufw status
```

---

## 3. Postgres local ⏳ (Claudito)

Crear DB y usuario dedicados (la contraseña la define el CEO o la genera
Claudito y la guarda en el EnvironmentFile de §5):

```bash
sudo -u postgres psql <<'SQL'
CREATE USER facturas WITH PASSWORD 'REEMPLAZAR_PASSWORD';
CREATE DATABASE facturas OWNER facturas;
SQL
```

La `DATABASE_URL` resultante (va en el EnvironmentFile, §5):
```
postgresql://facturas:REEMPLAZAR_PASSWORD@127.0.0.1:5432/facturas
```

> El código convierte `postgres://`→`postgresql://` solo — acá ya la
> escribimos como `postgresql://` directo. El schema se crea solo al
> arrancar la app (`db.create_all()` + `_ensure_schema()` en
> `app/__init__.py`), no hace falta correr migraciones a mano.

---

## 4. App + gunicorn + nginx ⏳ (Claudito)

### 4.1 Código y venv
```bash
sudo mkdir -p /srv && cd /srv
sudo git clone https://github.com/<owner>/facturas-saas.git
cd facturas-saas
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install gunicorn      # si no está ya en requirements
```

### 4.2 systemd (gunicorn como servicio)
`/etc/systemd/system/facturas.service`:
```ini
[Unit]
Description=Facturas SaaS (gunicorn)
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/srv/facturas-saas
EnvironmentFile=/etc/facturas-saas/env
ExecStart=/srv/facturas-saas/.venv/bin/gunicorn wsgi:app \
          --bind 127.0.0.1:8000 --workers 3 --timeout 60
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

> **`--timeout 60`** resuelve el hallazgo abierto del
> [ADR-0005](../decisions/0005-pantalla-espera-cold-start.md) (el default de
> gunicorn son 30s, que podían no alcanzar cuando varios archivos de una
> tanda golpean 503 de Gemini y se reintentan). Acá se fija en el systemd,
> ya no en `render.yaml`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now facturas
sudo systemctl status facturas
```

### 4.3 nginx (reverse proxy)
`/etc/nginx/sites-available/facturas`:
```nginx
server {
    listen 80;
    server_name facturas.mcfly.ar;

    client_max_body_size 25M;   # las fotos de factura pesan varios MB

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Host  $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_read_timeout 90s;   # > gunicorn timeout, cubre extracciones lentas
    }
}
```

> ⚠️ **Crítico para el login:** `ProxyFix` está configurado con
> `x_proto=1, x_host=1`. nginx **debe** mandar `X-Forwarded-Proto` y
> `X-Forwarded-Host` (arriba). Sin eso, Flask arma el `redirect_uri` como
> `http://…` y Google rechaza el login (o oauthlib lo corta por transporte
> inseguro). El `Host`/`X-Forwarded-Host` también define el dominio del
> `redirect_uri` — tiene que resolver a `facturas.mcfly.ar` para que
> coincida con lo registrado en Google Console (§1.2).

```bash
sudo ln -s /etc/nginx/sites-available/facturas /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4.4 TLS (certbot)
```bash
sudo certbot --nginx -d facturas.mcfly.ar
```
certbot reescribe el `server` para 443 + redirección 80→443 e instala un
**systemd timer de auto-renovación** (`certbot.timer`). Verificar:
```bash
sudo systemctl list-timers | grep certbot
sudo certbot renew --dry-run
```

---

## 5. Variables de entorno ⏳ (Claudito arma el archivo, CEO pone los valores 🔒)

El servicio las lee de `/etc/facturas-saas/env` (referenciado por el
systemd, §4.2). Permisos cerrados: `sudo chmod 600` y dueño `root` o
`www-data`.

```ini
# /etc/facturas-saas/env
SECRET_KEY=<generado una vez, ESTABLE — si cambia, se invalidan todas las sesiones>
PRODUCTION=true
GEMINI_API_KEY=<...>
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_CLIENT_ID=<...>
GOOGLE_CLIENT_SECRET=<...>
GOOGLE_SA_CREDENTIALS_FILE=/etc/facturas-saas/sa.json
DATABASE_URL=postgresql://facturas:<password>@127.0.0.1:5432/facturas
# LOG_TIEMPOS=true   # default ya activado; setear a false para apagarlo
```

Notas:
1. **`PRODUCTION=true`** reemplaza al `RENDER=true` de Render — activa la
   cookie de sesión `Secure`. **Requiere el cambio de código pendiente**
   (ver §8): hasta que ese cambio esté, la app mira `RENDER`, no
   `PRODUCTION`.
2. **`SECRET_KEY` estable:** generarla una vez
   (`python -c "import secrets; print(secrets.token_hex(32))"`) y no
   cambiarla — la sesión persistente de 90 días
   ([ADR-0012](../decisions/0012-sesion-90-dias-oauth-sin-reconsentimiento.md))
   depende de que se mantenga.
3. **Service Account:** el JSON va como archivo en
   `/etc/facturas-saas/sa.json` (`chmod 600`), apuntado por
   `GOOGLE_SA_CREDENTIALS_FILE`. El código
   (`app/services/sheets.py::_sa_info`) acepta el archivo o, alternativa,
   el JSON inline en `GOOGLE_SA_CREDENTIALS_JSON` — en un VPS el archivo es
   más prolijo.
4. El `.env.example` del repo documenta el set de vars para desarrollo
   local; este archivo es el de producción del VPS.

---

## 6. Migración de datos ⏳ (Claudito ejecuta, CEO da la connection string 🔒)

Postgres → Postgres, limpio:

```bash
# 1. Dump desde Render (connection string externa que da el CEO)
pg_dump "postgresql://<render-external-connection-string>" -Fc -f /tmp/facturas.dump

# 2. Restore en el Postgres local
pg_restore --no-owner --role=facturas -d \
  "postgresql://facturas:<password>@127.0.0.1:5432/facturas" /tmp/facturas.dump

# 3. Borrar el dump (tiene datos de usuarios)
shred -u /tmp/facturas.dump
```

> La tabla real a migrar es `users` (identidad, planilla conectada,
> contador). Si algo del schema se desincroniza, el arranque de la app lo
> reconcilia (`_ensure_schema`), pero el objetivo es que el restore ya
> traiga todo.

---

## 7. Cutover ⏳ + 🔒

1. Con DNS ya apuntando al VPS (§1.1) y todo lo anterior verde, **el CEO
   prueba el login real de Google de punta a punta** en
   `https://facturas.mcfly.ar` (esto Claudito no lo puede hacer — necesita
   navegador y la cuenta Google real). Confirmar: login sin
   `redirect_uri_mismatch`, sesión que persiste, y una carga de factura de
   prueba que escriba en el Sheet.
2. **Apagar el monitor de UptimeRobot** (cuenta del CEO, fuera del repo) —
   ya no hace falta, el VPS no duerme
   ([ADR-0013](../decisions/0013-keep-alive-render-free.md), sección
   "Retiro 2026-08-11").
3. Dejar Render **en standby unos días** como red de seguridad. Recién
   cuando el VPS demuestre estar estable: dar de baja el servicio de Render
   y **sacar la URI de Render** de Google Console.

---

## 8. Cambio de código pendiente (lo hace Claude Code en el repo, no Claudito)

El único cambio de código de la migración: en `app/__init__.py`, la cookie
`Secure` hoy se activa con `os.getenv("RENDER") == "true"`. Hay que pasarlo
a `PRODUCTION`.

> ⚠️ **Cuidado con el auto-deploy de Render.** Mientras Render siga siendo
> la producción activa, `master` se auto-deploya ahí. Si el cambio pasa a
> mirar **solo** `PRODUCTION`, Render (que setea `RENDER`, no `PRODUCTION`)
> se queda sin cookie `Secure`. Para no romper la producción viva durante
> la transición, el cambio debe **aceptar las dos** vars:
> ```python
> app.config["SESSION_COOKIE_SECURE"] = (
>     os.getenv("PRODUCTION") == "true" or os.getenv("RENDER") == "true"
> )
> ```
> Después del cutover, cuando Render se dé de baja, se simplifica a solo
> `PRODUCTION`.

---

## 9. Operación día a día (lo que antes hacía Render)

| Tarea | Render lo hacía solo | En el VPS |
|---|---|---|
| **Deploy** | auto en cada push a `master` | manual: ver §9.1 |
| **TLS + renovación** | automático | certbot + `certbot.timer` (§4.4) |
| **Gestión de proceso** | automático | `systemd` (`facturas.service`) |
| **Backups de DB** | automático | cron de `pg_dump` (§9.3) |
| **Logs** | dashboard | `journalctl` (§9.2) |

### 9.1 Deploy manual
```bash
cd /srv/facturas-saas
git pull
.venv/bin/pip install -r requirements.txt   # solo si cambió requirements
sudo systemctl restart facturas
sudo systemctl status facturas
```
(El auto-deploy no se reconstruye por ahora — ADR-0015 §4. Se agrega si el
deploy manual llega a doler.)

### 9.2 Logs
```bash
journalctl -u facturas -f                 # app (incluye las líneas LOG_TIEMPOS)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 9.3 Backups de Postgres
Cron diario (ej. 03:00), reteniendo unos días:
```bash
# /etc/cron.d/facturas-backup
0 3 * * * root pg_dump "postgresql://facturas:<password>@127.0.0.1:5432/facturas" \
  -Fc -f /var/backups/facturas/$(date +\%F).dump && \
  find /var/backups/facturas -name '*.dump' -mtime +7 -delete
```
Crear `/var/backups/facturas` con permisos cerrados antes.

### 9.4 Health check
`GET https://facturas.mcfly.ar/health` → `200 {"status":"ok"}` sin tocar
DB/Sheets/Gemini. Sirve para monitoreo del VPS
([ADR-0013](../decisions/0013-keep-alive-render-free.md): el endpoint queda,
como health check real; lo que se retira es el keep-alive/UptimeRobot).

---

## 10. Cómo se le pasa esto a Claudito

Quién es Claudito y el reparto de trabajo completo (Jordi / Claude Code /
Claudito) está en [`docs/ops/claudito.md`](claudito.md) — ese es el doc que
Claudito lee primero para saber que él es Claudito.

- Este runbook es **la tarea**: Claudito ejecuta las secciones ⏳ (§2, §3,
  §4, y su parte de §5, §6), no las 🔒 (esas las hace el CEO).
- **Claudito no commitea al repo.** Si necesita ajustar algo del repo
  (config, un fix), lo devuelve como handoff en `docs/handoffs/` y lo
  integra Claude Code. Regla del `WORKFLOW.md`: un solo escritor del repo.
- El cambio de código de §8 lo hace Claude Code, no Claudito — justamente
  por la regla anterior y por el cuidado con el auto-deploy.
