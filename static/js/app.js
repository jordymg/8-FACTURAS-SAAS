(function () {
  "use strict";

  const CAMPOS = window.__CAMPOS__ || [];
  // Campos que se muestran siempre aunque vengan vacíos, además de los
  // `required` (fecha, proveedor, total, moneda) — a diferencia de esos,
  // estos NO bloquean el guardado si quedan vacíos (ej. Factura B/C
  // legítimamente no discrimina neto/IVA). Ver ADR-0001 área App.
  const SIEMPRE_VISIBLES = ["neto", "iva_21"];

  const zona = document.getElementById("zona");
  const inputArchivos = document.getElementById("input-archivos");
  // Overlay de espera (ADR-0005 general) — cubre cold start y extracción
  // (reintentos automáticos ante 503 incluidos, invisibles para el
  // usuario). Reemplaza al viejo banner de texto #cargando.
  const overlayEsperaEl = document.getElementById("overlay-espera");
  const cardsEl = document.getElementById("cards");
  const btnGuardarLote = document.getElementById("btn-guardar-lote");
  const exitoTextoEl = document.getElementById("exito-texto");

  // Duración de la cuenta regresiva de la pantalla de éxito (ADR rediseño
  // de guardado, área App) — único lugar donde se define, para ajustarla
  // fácil (ej. bajarla a 2 segundos) sin tocar el resto de la lógica.
  const DURACION_CUENTA_REGRESIVA_SEG = 3;

  function showScreen(id) {
    document.querySelectorAll(".screen").forEach((s) => {
      s.classList.toggle("active", s.id === id);
      s.classList.toggle("hidden", s.id !== id);
    });
  }

  function esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── Selección de archivos: se procesan solos, sin botón manual ────────
  // Ver ADR-0001 área App (c): cada selección o drop es su propia tanda.
  function bloquearZona(bloqueada) {
    if (!zona) return;
    zona.classList.toggle("procesando", bloqueada);
    inputArchivos.disabled = bloqueada;
  }

  if (inputArchivos) {
    inputArchivos.addEventListener("change", () => {
      const nuevos = [...inputArchivos.files];
      inputArchivos.value = "";
      if (nuevos.length) procesar(nuevos);
    });
  }

  if (zona) {
    ["dragenter", "dragover"].forEach((ev) =>
      zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.add("arrastrando"); }));
    ["dragleave", "drop"].forEach((ev) =>
      zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.remove("arrastrando"); }));
    zona.addEventListener("drop", (e) => {
      const nuevos = [...e.dataTransfer.files];
      if (nuevos.length) procesar(nuevos);
    });
  }

  // ── Procesar con IA ────────────────────────────────────
  async function procesar(lista) {
    bloquearZona(true);
    overlayEsperaEl.classList.remove("hidden");
    const form = new FormData();
    lista.forEach((f) => form.append("archivos", f));

    let resultados;
    try {
      const resp = await fetch("/api/extract", { method: "POST", body: form });
      resultados = await resp.json();
    } catch (e) {
      overlayEsperaEl.classList.add("hidden");
      bloquearZona(false);
      alert("Error de red. Revisá tu conexión.");
      return;
    }

    overlayEsperaEl.classList.add("hidden");
    bloquearZona(false);
    showScreen("screen-review");
    cardsEl.innerHTML = "";
    resultados.forEach((r, i) => {
      cardsEl.appendChild(r.ok ? crearCardOk(r, lista[i]) : crearCardError(r, lista[i]));
    });
  }

  // ── Cards ───────────────────────────────────────────────
  function crearBtnDescartar(card) {
    const btn = document.createElement("button");
    btn.className = "btn-descartar";
    btn.type = "button";
    btn.innerHTML = '<span aria-hidden="true">✕</span> Descartar factura';
    btn.onclick = () => {
      card.remove();
      verificarFinTanda();
    };
    return btn;
  }

  function crearCardOk(r, archivo) {
    const card = document.createElement("div");
    card.className = "card pendiente";

    const header = document.createElement("div");
    header.className = "card-header";
    const titulo = document.createElement("span");
    titulo.textContent = r.nombre;
    header.appendChild(titulo);
    header.appendChild(crearBtnDescartar(card));
    card.appendChild(header);

    // Aviso de posible duplicado (ADR-0009 planillas) — no bloquea nada,
    // solo informa antes de que el usuario llegue al botón de guardar.
    if (r.duplicado) {
      const avisoDup = document.createElement("div");
      avisoDup.className = "aviso-duplicado";
      avisoDup.textContent = r.duplicado === "__MISMA_TANDA__"
        ? "Parece ser la misma factura que otra foto que subiste ahora."
        : `Esta factura ya la subiste el ${r.duplicado} a tu planilla.`;
      card.appendChild(avisoDup);
    }

    const body = document.createElement("div");
    body.className = "card-body";
    const grid = document.createElement("div");
    grid.className = "campos-grid";
    const inciertos = r.inciertos || [];
    let hayOcultos = false;
    CAMPOS.forEach((campo) => {
      const lbl = document.createElement("span");
      lbl.className = "campo-label";
      lbl.textContent = campo.label;
      let ctrl;
      const val = (r.fields && r.fields[campo.key]) || "";
      const enDuda = inciertos.includes(campo.key);
      if (campo.options) {
        ctrl = document.createElement("select");
        campo.options.forEach((op) => {
          const opt = document.createElement("option");
          opt.value = opt.textContent = op;
          if (op === val) opt.selected = true;
          ctrl.appendChild(opt);
        });
        if (campo.required && !campo.options.includes(val)) ctrl.classList.add("campo-vacio");
        ctrl.addEventListener("change", () => ctrl.classList.remove("campo-vacio", "campo-invalido", "campo-en-duda"));
      } else {
        ctrl = document.createElement("input");
        ctrl.type = "text";
        ctrl.value = val;
        if (campo.required && !val) ctrl.classList.add("campo-vacio");
        ctrl.addEventListener("input", () => {
          if (ctrl.value.trim()) ctrl.classList.remove("campo-vacio", "campo-invalido", "campo-en-duda");
          else if (campo.required) ctrl.classList.add("campo-vacio");
        });
      }
      // La IA completó este campo con baja certeza (ADR-0008): se resalta en
      // rojo para que el usuario lo corrobore, pero NO bloquea el guardado
      // — avanzar/guardar se toma como confirmación implícita.
      if (enDuda) ctrl.classList.add("campo-en-duda");
      ctrl.className = (ctrl.className ? ctrl.className + " " : "") + "campo-ctrl";
      ctrl.dataset.clave = campo.key;
      if (campo.required) ctrl.dataset.requerido = "true";

      // Campos ocultos por defecto (ADR-0001 área App, punto a): los
      // `required` y los de SIEMPRE_VISIBLES se muestran siempre; el resto
      // solo si la extracción trajo un valor — así nunca se pierde un dato
      // que la IA sí detectó, pero no se satura la tarjeta con campos vacíos.
      const siempreVisible = campo.required || SIEMPRE_VISIBLES.includes(campo.key);
      const item = document.createElement("div");
      item.className = "campo-item";
      if (!siempreVisible && !val) {
        item.classList.add("campo-oculto");
        hayOcultos = true;
      }
      item.appendChild(lbl);
      item.appendChild(ctrl);
      grid.appendChild(item);
    });
    body.appendChild(grid);
    if (hayOcultos) {
      const btnOcultos = document.createElement("button");
      btnOcultos.type = "button";
      btnOcultos.className = "btn-mostrar-ocultos";
      btnOcultos.textContent = "Mostrar campos ocultos";
      btnOcultos.onclick = () => {
        const mostrando = grid.classList.toggle("mostrar-ocultos");
        btnOcultos.textContent = mostrando ? "Ocultar campos vacíos" : "Mostrar campos ocultos";
      };
      body.appendChild(btnOcultos);
    }
    card.appendChild(body);

    const footer = document.createElement("div");
    footer.className = "card-footer";
    const msgVal = document.createElement("div");
    msgVal.className = "msg-validacion";
    footer.appendChild(msgVal);
    card.appendChild(footer);
    return card;
  }

  function crearCardError(r, archivo) {
    const card = document.createElement("div");
    card.className = "card con-error";
    const header = document.createElement("div");
    header.className = "card-header";
    const titulo = document.createElement("span");
    titulo.textContent = r.nombre;
    header.appendChild(titulo);
    header.appendChild(crearBtnDescartar(card));
    card.appendChild(header);

    const body = document.createElement("div");
    body.className = "card-body";
    const msg = document.createElement("div");
    msg.className = "error-msg";
    msg.textContent = r.error;
    body.appendChild(msg);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-reintentar-ia";
    btn.textContent = "Reintentar";
    btn.onclick = async () => {
      btn.disabled = true;
      btn.textContent = "Procesando…";
      msg.textContent = "";
      const form = new FormData();
      form.append("archivos", archivo);
      try {
        const resp = await fetch("/api/extract", { method: "POST", body: form });
        const [resultado] = await resp.json();
        card.replaceWith(resultado.ok ? crearCardOk(resultado, archivo) : crearCardError(resultado, archivo));
      } catch (e) {
        btn.disabled = false;
        btn.textContent = "Reintentar";
        msg.textContent = "Error de red.";
      }
    };
    body.appendChild(btn);
    card.appendChild(body);
    return card;
  }

  function validarCard(card, msgEl) {
    let valido = true;
    const problemas = [];
    card.querySelectorAll(".campo-invalido").forEach((el) => el.classList.remove("campo-invalido"));
    CAMPOS.forEach((campo) => {
      const ctl = card.querySelector(`[data-clave="${campo.key}"]`);
      if (!ctl || ctl.readOnly) return;
      const valor = ctl.value.trim();
      if (campo.required && !valor) { ctl.classList.add("campo-vacio"); valido = false; }
      // Nota (ADR-0008): "campo-en-duda" (baja certeza) es solo un aviso
      // visual — no bloquea el guardado, guardar es la confirmación.
      if (campo.key === "fecha" && valor && !/^\d{4}-\d{2}-\d{2}$/.test(valor)) {
        ctl.classList.remove("campo-vacio");
        ctl.classList.add("campo-invalido");
        problemas.push("Fecha: formato AAAA-MM-DD");
        valido = false;
      }
      const camposNumericos = [
        "neto", "iva_105", "iva_21", "iva_27", "otros_impuestos", "imp_internos", "total",
      ];
      if (camposNumericos.includes(campo.key) && valor && isNaN(Number(valor.replace(",", ".")))) {
        ctl.classList.add("campo-invalido");
        problemas.push(`${campo.label}: solo números`);
        valido = false;
      }
    });
    msgEl.textContent = valido ? "" : (problemas.length ? problemas.join(" · ") : "Completá los campos en naranja.");
    msgEl.style.display = valido ? "none" : "block";
    return valido;
  }

  // ── Guardado en lote (botón único) ─────────────────────
  // Un solo botón guarda todas las tarjetas visibles (no descartadas) de la
  // tanda; cada una sigue usando POST /api/invoices individualmente (mismo
  // flujo de siempre, incluido el contador mensual). Los campos en rojo
  // ("baja certeza", ADR-0008) y los avisos de duplicado (ADR-0009
  // planillas) no bloquean: apretar este botón cuenta como confirmación
  // implícita de todas las tarjetas visibles.
  function marcarErrorGuardado(card, mensaje) {
    // Reutiliza la clase visual "con-error" (borde rojo) que ya usan las
    // tarjetas con error de extracción — acá además se deja "pendiente"
    // para que el próximo click del botón único reintente solo esta.
    card.classList.add("con-error");
    let errDiv = card.querySelector(".save-error");
    if (!errDiv) {
      errDiv = document.createElement("div");
      errDiv.className = "error-msg save-error";
      card.querySelector(".card-footer").appendChild(errDiv);
    }
    errDiv.textContent = mensaje;
  }

  async function guardarTanda() {
    const cards = [...cardsEl.querySelectorAll(".card.pendiente")];
    if (!cards.length) return;

    btnGuardarLote.disabled = true;
    btnGuardarLote.textContent = "Guardando…";

    for (const card of cards) {
      if (!card.isConnected) continue; // se descartó mientras se guardaba el resto de la tanda
      const msgVal = card.querySelector(".msg-validacion");
      if (!validarCard(card, msgVal)) continue; // sigue pendiente, corrige y reintenta con el mismo botón

      const datos = {};
      card.querySelectorAll(".campo-ctrl").forEach((ctl) => { datos[ctl.dataset.clave] = ctl.value.trim(); });

      try {
        const resp = await fetch("/api/invoices", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(datos),
        });
        const resultado = await resp.json();
        if (resultado.ok) {
          card.classList.remove("pendiente", "con-error");
          card.classList.add("guardado");
          card.querySelectorAll(".campo-ctrl").forEach((ctl) => {
            ctl.readOnly = true;
            if (ctl.tagName === "SELECT") ctl.disabled = true;
          });
          msgVal.style.display = "none";
          const errDiv = card.querySelector(".save-error");
          if (errDiv) errDiv.remove();
          const okDiv = document.createElement("div");
          okDiv.className = "ok-msg";
          okDiv.textContent = "✓ Guardado en Sheets";
          card.querySelector(".card-footer").appendChild(okDiv);
        } else {
          marcarErrorGuardado(card, resultado.error);
        }
      } catch (e) {
        marcarErrorGuardado(card, "Error de red. Probá guardar de nuevo.");
      }
    }

    btnGuardarLote.disabled = false;
    btnGuardarLote.textContent = "Guardar en Sheets";
    verificarFinTanda();
  }

  // Se llama tras descartar una tarjeta o tras un intento de guardado en
  // lote: si ya no queda ninguna tarjeta pendiente de resolución (todas
  // guardadas o descartadas), cierra la tanda. Con al menos una guardada,
  // pantalla de éxito con cuenta regresiva; si se descartó todo sin guardar
  // nada, vuelve directo a la home sin pantalla de éxito.
  function verificarFinTanda() {
    if (cardsEl.querySelector(".card:not(.guardado)")) return;
    const guardadas = cardsEl.querySelectorAll(".card.guardado").length;
    if (guardadas > 0) {
      mostrarPantallaExito(guardadas);
    } else {
      showScreen("screen-capture");
      loadInvoices();
    }
  }

  // No cambia de pantalla — las tarjetas ya guardadas siguen visibles
  // arriba. La cuenta regresiva ocupa el lugar del botón único, en el
  // mismo screen-review, hasta que redirige sola a la home.
  function mostrarPantallaExito(cantidad) {
    const base = cantidad === 1 ? "Factura guardada." : "Facturas guardadas.";
    btnGuardarLote.classList.add("hidden");
    exitoTextoEl.classList.remove("hidden");

    const numeros = [DURACION_CUENTA_REGRESIVA_SEG + "…"];
    const render = () => {
      exitoTextoEl.textContent = `${base} Volviendo al inicio en ${numeros.join(" ")}`;
    };
    render();

    let tick = 0;
    const intervalo = setInterval(() => {
      tick++;
      if (tick < DURACION_CUENTA_REGRESIVA_SEG) {
        numeros.push((DURACION_CUENTA_REGRESIVA_SEG - tick) + "…");
        render();
      } else {
        clearInterval(intervalo);
        cardsEl.innerHTML = "";
        exitoTextoEl.classList.add("hidden");
        btnGuardarLote.classList.remove("hidden");
        showScreen("screen-capture");
        loadInvoices();
      }
    }, 1000);
  }

  if (btnGuardarLote) btnGuardarLote.addEventListener("click", guardarTanda);

  // ── Contador y aviso de tope mensual (ADR-0008) ────────
  // Se actualizan cada vez que se recargan las últimas facturas (volver a
  // la home) — el header no se vuelve a renderizar del lado del servidor
  // después de guardar, así que sin esto quedaba siempre en el valor con
  // el que cargó la página por primera vez.
  function actualizarContadorLimite(data) {
    const contadorEl = document.getElementById("header-contador");
    const avisoEl = document.getElementById("aviso-limite");
    if (typeof data.facturas_mes !== "number") return;
    if (contadorEl) contadorEl.textContent = `${data.facturas_mes}/${data.limite_mensual}`;
    if (avisoEl) {
      avisoEl.textContent = `Estás por llegar al límite de facturas de este mes (${data.facturas_mes} de ${data.limite_mensual}).`;
      avisoEl.classList.toggle("hidden", data.facturas_mes < data.umbral_aviso);
    }
  }

  // ── Últimas facturas ────────────────────────────────────
  async function loadInvoices() {
    const list = document.getElementById("invoice-list");
    if (!list) return;
    list.innerHTML = '<p class="list-placeholder">Cargando…</p>';
    try {
      const res = await fetch("/api/invoices");
      const data = await res.json();
      actualizarContadorLimite(data);
      const invoices = (data.invoices || []).slice(-10).reverse();
      if (!invoices.length) {
        list.innerHTML = '<p class="list-empty">Sin facturas aún.</p>';
        return;
      }
      list.innerHTML = invoices
        .map(
          (inv) => `<div class="invoice-item">
            <span class="inv-razon">${esc(inv.proveedor || "—")}</span>
            <span class="inv-total">$${esc(inv.total || "—")}</span>
            <span class="inv-fecha">${esc(inv.fecha || "")}</span>
          </div>`
        )
        .join("");
    } catch {
      list.innerHTML = '<p class="list-error">Error al cargar facturas.</p>';
    }
  }

  if (document.getElementById("screen-capture")) loadInvoices();

  // ── Carruseles rotativos tipo "tip" (ADR-0004 / ADR-0007 área App) ────
  // Un texto por vez, arranca en uno aleatorio, rota cada 9s con fade.
  // Reutilizada por el tip de la home y el carrusel de consejos de la
  // pantalla de revisión — cada llamado tiene su propio índice/timer,
  // así que no se pisan entre sí aunque compartan la misma función.
  function iniciarCarruselRotativo(elId, textos) {
    const el = document.getElementById(elId);
    if (!el || !textos.length) return;
    let i = Math.floor(Math.random() * textos.length);
    const mostrar = () => {
      el.textContent = `Tip — ${textos[i]}`;
      el.classList.remove("hidden");
      el.classList.remove("tip-oculto");
    };
    mostrar();
    setInterval(() => {
      el.classList.add("tip-oculto");
      setTimeout(() => {
        i = (i + 1) % textos.length;
        mostrar();
      }, 300);
    }, 9000);
  }

  iniciarCarruselRotativo("tip-rotativo", window.__TIPS__ || []);
  iniciarCarruselRotativo("consejo-revision-rotativo", window.__CONSEJOS_REVISION__ || []);
  iniciarCarruselRotativo("mensaje-espera-rotativo", window.__MENSAJES_ESPERA__ || []);
})();
