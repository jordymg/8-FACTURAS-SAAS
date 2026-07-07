# Producto: App (diseño/UX)

> Pendiente — el contenido completo de este archivo sale de una
> conversación de diseño dedicada, todavía no tuvo lugar. Por ahora el
> alcance (ver `README.md` de esta área) más las decisiones puntuales que
> ya se tomaron sueltas, antes de esa conversación.

## Alcance a definir
1. Pantallas: landing, configuración de planilla, captura, revisión,
   últimas facturas, pantalla de espera (cold start).
2. Flujo de uso de punta a punta: onboarding, carga diaria, casos de error.
3. Formulario de revisión: layout con ~20 campos por tarjeta — rediseño ya
   decidido, ver
   [`decisions/0001-rediseno-formulario-revision.md`](decisions/0001-rediseno-formulario-revision.md)
   (ocultar campos poco frecuentes salvo que tengan valor, grilla
   responsiva en desktop, procesamiento automático sin botón manual), sin
   implementar todavía.
4. Pantalla de espera / cold start de Render — ver
   [`docs/decisions/0005-pantalla-espera-cold-start.md`](../../decisions/0005-pantalla-espera-cold-start.md)
   del repo general (ya decidida, sin implementar). Ampliada: también
   enmascara los reintentos automáticos ante un 503 de Gemini — el usuario
   nunca ve un mensaje de "reintentando", ve el carrusel de tips.
5. UX de duplicados detectados — ver
   [`docs/areas/planillas/decisions/0009-ux-duplicados.md`](../planillas/decisions/0009-ux-duplicados.md)
   — **implementada y confirmada funcionando en producción** (no es un
   pendiente de diseño, solo referencia de dónde vive el aviso visual).

## Onboarding — foco definido (2026-07-07)
El founder aclaró que el onboarding **no** es un carrusel explicativo
genérico de primera apertura. El foco real es el paso crítico donde un
usuario nuevo se puede caer: **configurar la planilla** (crearla,
compartirla con el mail de la Service Account, pegar la URL en la app).

Requisito: ese paso tiene que ser "a prueba de tontos" — bien explicado,
guiando a alguien que nunca hizo esto. Diseño concreto (textos, capturas de
pantalla de ejemplo, dónde se muestran) todavía pendiente de la
conversación de diseño dedicada de esta área.

## Versionado
Todavía no hay una versión "v1" formalizada del diseño — la interfaz actual
se construyó de forma incremental durante la integración del prototipo y
los pivots de arquitectura (ver `docs/STATUS.md` general). Esta área se creó
para que, de acá en adelante, los cambios de diseño se decidan acá primero
— ver [`decisions/`](decisions/) para lo ya resuelto suelto, antes de la
conversación de diseño completa.
