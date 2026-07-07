# 📸 Facturas SaaS

**Foto de factura → datos procesados a tu planilla.**

Facturas SaaS es un sistema que elimina la carga manual de facturas de
compra. En vez de tipear una por una fecha, proveedor, CUIT, importes e
impuestos, el usuario le saca una foto a la factura desde su celular: una IA
lee el comprobante, extrae todos los datos fiscales, el usuario los revisa en
pantalla y el sistema los carga como una fila nueva en su propia planilla de
Google Sheets — la misma planilla que después usa día a día y le entrega a su
contador a fin de mes.

---

> ## ⚠️ 🤖 AI agents — READ THIS FIRST
> 1. **Read `/docs` before doing anything.**
> 2. **Update `docs/STATUS.md` before ending any session.**
> 3. **Follow `docs/WORKFLOW.md`.**

---

El sistema completo abarca:

1. **Una app web instalable** (se abre desde el navegador o se instala en el
   celular como una app más, sin pasar por ningún store).
2. **Un motor de extracción con IA** que interpreta la foto del comprobante y
   devuelve los datos fiscales estructurados.
3. **Una capa de validación** en el servidor (CUIT, duplicados, fechas,
   formatos) antes de escribir nada.
4. **La planilla del cliente** como destino final de los datos — el
   entregable real del servicio, que vive en la cuenta de Google del propio
   usuario, no en la nuestra.

### ¿Qué es eso de "app web instalable" (PWA)?

Técnicamente el frontend es una **PWA** (Progressive Web App): una página web
que se comporta como una app nativa. Se puede usar directo desde el navegador,
o "instalar" en el teléfono (queda con su ícono en la pantalla de inicio, se
abre a pantalla completa y accede a la cámara), sin descargarla de Google Play
ni App Store. Para este producto es la opción ideal: cero fricción de
instalación, una sola base de código, y la cámara del celular es todo el
hardware que hace falta.

---

## 🟢 Estado

**En producción:** https://facturas-saas.onrender.com (Render, auto-deploy
desde GitHub).

Fase 1 completada y probada end-to-end con datos reales. El detalle vivo de
qué está hecho, qué sigue y qué está bloqueado está siempre en
[`docs/STATUS.md`](docs/STATUS.md) — ese archivo, no este README, es la
foto actual del proyecto.

## 💡 El producto en una línea

La app es el **medio**; el entregable real es la **planilla**
("PLANILLA FACTURAS COMPRAS"): el Google Sheet del cliente donde queda
registrada cada factura, con formato pensado para el contador. Todo lo
relativo a la planilla (estructura, fórmulas, formato, versionado) se diseña
y decide en su propia área de I+D:
[`docs/areas/planillas/`](docs/areas/planillas/).

## ⚙️ Cómo funciona

1. El usuario saca una foto de la factura desde la PWA.
2. Gemini extrae los datos fiscales (la imagen se usa solo en memoria y se
   descarta — el MVP no persiste imágenes).
3. El usuario revisa/corrige los datos en una tarjeta editable.
4. La app valida en Python (CUIT, duplicados, fechas) y escribe la fila en
   el Google Sheet del usuario.

### Arquitectura de acceso a Sheets

Una **Service Account** centralizada escribe en la planilla de cada usuario:
el usuario comparte su Sheet con el mail de la SA como Editor y pega la URL
en la app — una sola vez. El login de Google pide solo identidad
(`openid` + `email`), sin scopes sensibles ni verificación de Google. El dato
vive siempre en la cuenta del propio usuario (user-owned storage). Ver
[`docs/decisions/0004-service-account-sheets.md`](docs/decisions/0004-service-account-sheets.md).

## 🛠 Stack

| Capa | Tecnología |
|---|---|
| Frontend | PWA (HTML/JS) |
| Backend | Flask (Python) |
| Extracción | Gemini |
| Datos del usuario | Google Sheets (vía Service Account) |
| Hosting | Render (auto-deploy desde GitHub) |
| Pagos (Fase 3) | Mercado Pago suscripciones |

Cada decisión de stack tiene su porqué documentado en
[`docs/decisions/`](docs/decisions/).

## 📐 Cómo trabajamos

Este repo está pensado para ser trabajado por **varias IAs en paralelo**
(Claude, Claude Code, etc.) sin repetir contexto ni re-discutir lo ya
decidido. Las reglas:

1. **Los docs son la memoria.** Toda sesión de trabajo (humana o IA) arranca
   leyendo `/docs` y termina actualizando `docs/STATUS.md`. El protocolo
   completo está en [`docs/WORKFLOW.md`](docs/WORKFLOW.md).
2. **Toda decisión significativa es un ADR.** Nada queda "decidido en una
   conversación": se escribe en `docs/decisions/` (o en el `decisions/` del
   área que corresponda) con Contexto / Decisión / Alternativas /
   Consecuencias. Eso evita que una IA futura vuelva a litigar algo cerrado.
3. **Áreas de I+D por producto.** Los "productos internos" del proyecto
   tienen su propia carpeta en `docs/areas/` con su `PRODUCTO.md`,
   `STATUS.md` y `decisions/` propios. Hoy existe una: **planillas** (el
   diseño de la planilla que recibe el cliente). Regla de oro: ningún cambio
   de estructura de la planilla se programa sin un ADR previo en esa área.
4. **Los problemas que muerden quedan escritos.** `docs/ISSUES.md` loguea
   los bugs que tocaron datos reales, que encontró el uso (no nosotros), o
   cuya causa es una rareza de un sistema externo que puede volver a
   aparecer. Objetivo: no pisar el mismo error dos veces.

## 📚 Documentación

| Doc | Qué contiene |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Qué construimos y por qué (grade A) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Cómo: stack, data model, API |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Fases y tareas |
| [`docs/STATUS.md`](docs/STATUS.md) | Estado vivo del proyecto |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | Protocolo multi-IA y handoffs |
| [`docs/ISSUES.md`](docs/ISSUES.md) | Log de problemas que tocaron datos reales o sorprendieron |
| [`docs/decisions/`](docs/decisions/) | ADRs generales (stack, storage, pricing, Service Account) |
| [`docs/areas/`](docs/areas/) | Unidades de I+D por producto (ej. la planilla) |
| [`VALIDATION.md`](VALIDATION.md) | Gate 4/4 y evidencia |

## 🚀 Correr local

```bash
pip install -r requirements.txt
cp .env.example .env   # completar claves
flask --app wsgi run
```

## 💰 Modelo de negocio

Plan único: **ARS $1.999/mes, hasta 250 facturas** (imágenes y export
incluidos), vía Mercado Pago suscripciones. Precio validado con usuarios
reales antes de construir — ver
[`docs/decisions/0003-pricing.md`](docs/decisions/0003-pricing.md).
