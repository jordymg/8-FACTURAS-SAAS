# WORKFLOW — Protocolo multi-IA

El repo es la única fuente de verdad. Claude Code es la única puerta de escritura (commit + push).

inbox/: carpeta de entrada. Cuando el usuario lo pida, leé los
archivos de inbox/, aplicalos donde corresponda (moverlos, reemplazar docs,
ejecutar lo que indiquen), y después BORRÁ el contenido de inbox/ (dejando
.gitkeep). Nunca dejes archivos procesados ahí.

## Empezar sesión (cualquier IA)
```
Leé docs/STATUS.md y docs/ del repo facturas-saas antes de hacer nada.
Contexto: [pegar STATUS.md si la IA no accede al repo]
Hoy vamos a: [tarea]
```

## Cerrar sesión
```
Actualizá docs/STATUS.md: qué se hizo hoy, qué queda pendiente,
decisiones tomadas. Dame el archivo completo listo para commitear.
```
- En Claude Code: agregar "commit y push".
- En otras IAs: usar el protocolo de handoff (abajo).
- El bloque **Next** de STATUS.md debe escribirse para alguien que no conoce el
  proyecto: pasos numerados, concretos, en lenguaje simple, indicando QUÉ hacer,
  DÓNDE y QUÉ se necesita para hacerlo. Antes de escribirlo, verificar con el
  usuario que cada punto siga pendiente.

## Handoff desde IA externa → Claude Code
Toda IA que NO puede pushear debe, al cerrar sesión, generar UN archivo:
`docs/handoffs/YYYY-MM-DD-tema.md` con:
1. **Resumen de la sesión** — qué se habló, con lujo de detalles.
2. **Decisiones tomadas** — y su justificación.
3. **Cambios a pushear** — lista exacta de archivos a crear/modificar con su contenido completo.
4. **STATUS.md actualizado** — el archivo completo, listo para reemplazar.

Luego, en Claude Code:
```
Leé este handoff, aplicá los cambios que indica, actualizá docs/STATUS.md
con la versión incluida, commit y push.
[pegar/adjuntar el archivo]
```

## Regla
Sesión que no cierra actualizando STATUS.md = información perdida para las demás IAs.

## Áreas
`docs/areas/{nombre}/` son unidades de I+D por producto. Cada una tiene
README (alcance), PRODUCTO.md (definición), STATUS.md y `decisions/` propios.
