# STATUS

## Current phase
Phase 1 — en construcción. OAuth funcionando localmente. Extracción Gemini bloqueada.

## Done
- Validation Gate: 4/4 PASS (ver VALIDATION.md)
- Discovery completa: PRD, ARCHITECTURE, ROADMAP, ADRs 0001–0003
- Scaffold Phase 1: Flask app, blueprints (auth/api/web), modelos, servicios (Gemini/Sheets/Drive), PWA, render.yaml
- OAuth Google funcionando localmente (fix PKCE requests-oauthlib 2.x, fix OAUTHLIB_INSECURE_TRANSPORT)
- SDK Gemini migrado de google-generativeai → google-genai

## Next
- **PRIORIDAD: revisar prototipo del founder y reemplazar/adaptar el scaffold con su código**
  (El founder tiene un prototipo funcional — en la próxima sesión mostrarlo y extraer lo que vale: prompt de extracción, flujo UI, lógica que ya funciona)
- Conseguir API key de Gemini válida con créditos (la actual da 429 RESOURCE_EXHAUSTED)
- Completar Phase 1: guardar factura en Sheet + imagen en Drive, probar flow completo

## Blocked
- Extracción Gemini: API key agotada (429). Necesita key con créditos o free tier activo.

## Decisiones
- 2026-07-03: ADR-0001 stack, ADR-0002 user-owned storage, ADR-0003 price $1,999/250 facturas
- 2026-07-03: descartados "Tickploy/Clarifica/SpomBridge" (no verificables). Competidores reales: Facturitas, TusFacturasAPP, KOE, Xtract
- 2026-07-04: SDK google-generativeai deprecado → migrado a google-genai>=1.0
