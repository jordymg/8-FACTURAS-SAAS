# ADR-0001 (planillas): Alternativa — la Service Account crea la planilla

**Date:** 2026-07-06
**Status:** NO ADOPTADA — documentada para el futuro

## Qué es la Service Account (SA)
Una cuenta de Google "robot" que usa nuestra app para escribir en las
planillas de los clientes. No es una persona; tiene su propio email (algo
tipo `facturas-bot@...iam.gserviceaccount.com`) y su propio Drive de 15GB.

## Flujo actual (no cambia)
El cliente comparte su propia planilla como Editor al email de la Service
Account, y pega la URL en `/app/config`. La planilla vive en el Drive del
cliente, en su cuenta.

## Alternativa documentada (no adoptada)
Usar **solo si el onboarding actual genera fricción o problemas**: en vez de
que el cliente cree y comparta su planilla, la Service Account crea la
planilla directamente y la comparte como Editor únicamente al email del
cliente (que ya tenemos del login con Google). El cliente la ve en
"Compartidos conmigo" sin configurar nada — cero pasos manuales de su lado.

La planilla viviría en el Drive de la Service Account, no en el del cliente.
El límite de 15GB de la SA alcanza de sobra para esto; quedarse sin espacio
ahí sería en los hechos una señal de éxito (muchísimos clientes activos).

## Descartado de plano
Hacer la planilla pública con permisos de edición (en vez de compartirla
puntualmente) — expondría datos fiscales del cliente a cualquiera con el
link.

## Por qué no se adopta ahora
El flujo actual (cliente comparte su propia planilla) ya funciona, ya está
probado en producción, y mantiene el dato en la cuenta del propio cliente,
no en la nuestra — consistente con [ADR-0002 del repo general](../../decisions/0002-user-owned-storage.md)
(user-owned storage). Esta alternativa queda como opción de mejora de
onboarding a evaluar si en el futuro el paso de "compartir la planilla"
resulta ser una barrera real para nuevos clientes.
