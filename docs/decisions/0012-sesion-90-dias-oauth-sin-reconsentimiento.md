# ADR-0012: Sesión persistente de 90 días renovables + OAuth sin re-consentimiento

**Date:** 2026-07-15
**Status:** ADOPTADA e IMPLEMENTADA

## Contexto
El CEO reportó, probando desde el celular, dos síntomas juntos: cada vez
que entra a la app le vuelve a pedir login, Y le vuelve a aparecer la
pantalla de permisos de Google, Y le llega un mail de Google avisando que
"autorizó la aplicación" de nuevo. Diagnóstico:
1. La sesión de Flask no era permanente (`session.permanent` nunca se
   seteaba) — sin eso, Flask emite una cookie de sesión "de navegador"
   (sin `Expires`/`Max-Age`), que el navegador descarta al cerrarse del
   todo.
2. El login (`app/blueprints/auth.py::google_login`) armaba la URL de
   autorización con `prompt="consent"` explícito, forzando la pantalla de
   permisos en cada login. Además, `access_type="offline"` — que genera un
   grant nuevo (de ahí el mail) — no se pasaba explícito, **pero
   `google-auth-oauthlib` lo pone en `"offline"` por default si no se
   especifica lo contrario** (`Flow.authorization_url` hace
   `kwargs.setdefault("access_type", "offline")`); hubo que pasar
   `access_type="online"` a propósito para desactivarlo — no alcanzaba con
   simplemente no mencionarlo.

El login solo usa scopes de identidad (`openid` + `email`, ver
[ADR-0004](0004-service-account-sheets.md)) — no hay refresh token ni
acceso offline que justifique ninguna de las dos cosas.

## Decisión
- **Sesión permanente de 90 días de inactividad, renovable.**
  `session.permanent = True` al loguear
  (`app/blueprints/auth.py::google_callback`).
  `PERMANENT_SESSION_LIFETIME` = 90 días, en una sola constante
  (`SESSION_LIFETIME_DIAS` en `app/__init__.py`).
  `SESSION_REFRESH_EACH_REQUEST = True` (default de Flask, seteado
  explícito) — la cookie se reemite en cada request, así el vencimiento
  corre desde el último uso, no desde el login.
- **Cookie de sesión endurecida**: `SESSION_COOKIE_HTTPONLY = True`,
  `SESSION_COOKIE_SAMESITE = "Lax"` (necesario para que sobreviva el
  redirect de vuelta desde Google), `SESSION_COOKIE_SECURE` = `True` solo
  en producción (detectado con la env var `RENDER=true` que Render define
  sola en todos sus servicios — en local, por HTTP, tiene que quedar en
  `False` o el navegador descarta la cookie).
- **Sin re-consentimiento de Google**: se saca `prompt="consent"` de
  `google_login()` (no se pasa `prompt` en absoluto) y se fuerza
  `access_type="online"` explícito, pisando el default de la librería. La
  pantalla de permisos de Google debería aparecer solo la primera vez que
  una cuenta usa la app; logins posteriores son un redirect silencioso,
  sin mail de "autorizaste la aplicación".
- **`SECRET_KEY` estable**: ya se leía de `os.environ["SECRET_KEY"]`
  (nunca generada en el proceso), y en `render.yaml` usa
  `generateValue: true` — confirmado contra la documentación de Render que
  esto genera el valor **una sola vez** al crear el servicio y lo persiste
  como env var fija; no se regenera en cada deploy/restart. No hizo falta
  cambiar nada acá, solo confirmarlo.

## Alternativas consideradas
- Sesión corta o no persistente — descartada: es la traba reportada por
  el CEO, y castiga al usuario activo, que es justo el perfil que se busca
  (uso diario desde el celular).
- Plazo corto tipo 7-30 días — descartado: no hay costo real en evitarlo
  (es inactividad renovable, no un plazo fijo desde el login), y el
  estándar de apps de uso diario es un plazo largo renovable.
- `prompt="select_account"` en vez de sin `prompt` — no se activó: sin
  necesidad reportada de elegir cuenta en cada login: si aparece esa
  necesidad más adelante, es un cambio de una línea.

## Consecuencias
- Un usuario activo no vuelve a ver el login de la app ni la pantalla de
  permisos de Google salvo que esté 90 días sin usarla.
- Un redeploy o restart del proceso en Render ya no desloguea a nadie
  (dependía únicamente de que `SECRET_KEY` sea estable, que ya lo era).
- Verificado en este entorno (sin browser real ni cuenta de Google
  disponible): valores de config de sesión, que la cookie emitida tiene
  `Expires`/`Max-Age` (no es "de navegador"), que sobrevive un restart del
  proceso simulado (misma `SECRET_KEY`, dos instancias de la app), que una
  sesión vencida obliga a re-loguear, y que la URL de autorización
  generada no lleva `prompt` ni `access_type=offline`.
- **No verificado, requiere confirmación real** (mismo tipo de límite que
  ADR-0006 área App): que Google efectivamente omite la pantalla de
  permisos y el mail en un segundo login real con una cuenta que ya
  autorizó antes, y el comportamiento en el celular con la PWA instalada.
  Son las pruebas 2 a 4 del handoff — quedan pendientes de que el CEO las
  corra contra producción/celular real.
