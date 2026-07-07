(function () {
  "use strict";

  const CAMPOS = window.__CAMPOS__ || [];

  let archivos = [];

  const zona = document.getElementById("zona");
  const inputArchivos = document.getElementById("input-archivos");
  const listaEl = document.getElementById("lista-archivos");
  const btnProcesar = document.getElementById("btn-procesar");
  const cargandoEl = document.getElementById("cargando");
  const cardsEl = document.getElementById("cards");
  const btnVolver = document.getElementById("btn-volver");

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

  // ── Selección de archivos ──────────────────────────────
  function actualizarLista() {
    listaEl.innerHTML = "";
    archivos.forEach((f, i) => {
      const li = document.createElement("li");
      const span = document.createElement("span");
      span.textContent = f.name;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "✕";
      btn.onclick = () => { archivos.splice(i, 1); actualizarLista(); };
      li.appendChild(span);
      li.appendChild(btn);
      listaEl.appendChild(li);
    });
    btnProcesar.disabled = archivos.length === 0;
  }

  function agregarArchivos(nuevos) {
    for (const f of nuevos) archivos.push(f);
    actualizarLista();
  }

  if (inputArchivos) {
    inputArchivos.addEventListener("change", () => {
      agregarArchivos([...inputArchivos.files]);
      inputArchivos.value = "";
    });
  }

  if (zona) {
    ["dragenter", "dragover"].forEach((ev) =>
      zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.add("arrastrando"); }));
    ["dragleave", "drop"].forEach((ev) =>
      zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.remove("arrastrando"); }));
    zona.addEventListener("drop", (e) => agregarArchivos([...e.dataTransfer.files]));
  }

  // ── Procesar con IA ────────────────────────────────────
  async function procesar(lista) {
    btnProcesar.disabled = true;
    cargandoEl.classList.remove("hidden");
    const form = new FormData();
    lista.forEach((f) => form.append("archivos", f));

    let resultados;
    try {
      const resp = await fetch("/api/extract", { method: "POST", body: form });
      resultados = await resp.json();
    } catch (e) {
      cargandoEl.classList.add("hidden");
      btnProcesar.disabled = archivos.length === 0;
      alert("Error de red. Revisá tu conexión.");
      return;
    }

    cargandoEl.classList.add("hidden");
    archivos = [];
    actualizarLista();
    showScreen("screen-review");
    cardsEl.innerHTML = "";
    resultados.forEach((r, i) => {
      cardsEl.appendChild(r.ok ? crearCardOk(r, lista[i]) : crearCardError(r, lista[i]));
    });
  }

  if (btnProcesar) btnProcesar.addEventListener("click", () => procesar(archivos));
  if (btnVolver) btnVolver.addEventListener("click", () => { showScreen("screen-capture"); loadInvoices(); });

  // ── Cards ───────────────────────────────────────────────
  function crearBtnDescartar(card, title) {
    const btn = document.createElement("button");
    btn.className = "btn-descartar";
    btn.type = "button";
    btn.textContent = "✕";
    btn.title = title;
    btn.onclick = () => card.remove();
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
    header.appendChild(crearBtnDescartar(card, "Descartar este comprobante"));
    card.appendChild(header);

    const body = document.createElement("div");
    body.className = "card-body";
    const grid = document.createElement("div");
    grid.className = "campos-grid";
    const inciertos = r.inciertos || [];
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
      // La IA no pudo determinar este campo con certeza (ADR-0007): queda
      // vacío y resaltado en rojo hasta que el usuario lo revise/complete.
      if (enDuda && !val) ctrl.classList.add("campo-en-duda");
      ctrl.dataset.dudoso = enDuda ? "true" : "false";
      ctrl.className = (ctrl.className ? ctrl.className + " " : "") + "campo-ctrl";
      ctrl.dataset.clave = campo.key;
      if (campo.required) ctrl.dataset.requerido = "true";
      grid.appendChild(lbl);
      grid.appendChild(ctrl);
    });
    body.appendChild(grid);
    card.appendChild(body);

    const footer = document.createElement("div");
    footer.className = "card-footer";
    const msgVal = document.createElement("div");
    msgVal.className = "msg-validacion";
    footer.appendChild(msgVal);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-guardar";
    btn.textContent = "Guardar en Sheets";
    btn.onclick = () => guardarCard(card, msgVal);
    footer.appendChild(btn);
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
    header.appendChild(crearBtnDescartar(card, "Descartar"));
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
    btn.textContent = "Reintentar con IA";
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
        btn.textContent = "Reintentar con IA";
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
      if (ctl.dataset.dudoso === "true" && !valor) {
        ctl.classList.add("campo-en-duda");
        problemas.push(`${campo.label}: la IA no está segura, revisar y completar`);
        valido = false;
      }
      if (campo.key === "fecha" && valor && !/^\d{4}-\d{2}-\d{2}$/.test(valor)) {
        ctl.classList.remove("campo-vacio");
        ctl.classList.add("campo-invalido");
        problemas.push("Fecha: formato AAAA-MM-DD");
        valido = false;
      }
      const camposNumericos = [
        "neto", "iva_105", "iva_21", "iva_27", "perc_iva", "perc_iibb_arba",
        "iibb_caba", "ret_ganancias", "ret_iva", "sirtac", "imp_internos", "total",
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

  async function guardarCard(card, msgVal) {
    if (!validarCard(card, msgVal)) return;
    const datos = {};
    card.querySelectorAll(".campo-ctrl").forEach((ctl) => { datos[ctl.dataset.clave] = ctl.value.trim(); });
    const btn = card.querySelector(".btn-guardar");
    btn.disabled = true;
    btn.textContent = "Guardando…";
    try {
      const resp = await fetch("/api/invoices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });
      const resultado = await resp.json();
      if (resultado.ok) {
        card.className = "card guardado";
        card.querySelectorAll(".campo-ctrl").forEach((ctl) => {
          ctl.readOnly = true;
          if (ctl.tagName === "SELECT") ctl.disabled = true;
        });
        const okDiv = document.createElement("div");
        okDiv.className = "ok-msg";
        okDiv.textContent = "✓ Guardado en Sheets";
        btn.replaceWith(okDiv);
        msgVal.style.display = "none";
      } else {
        btn.disabled = false;
        btn.textContent = "Reintentar guardar";
        let errDiv = card.querySelector(".save-error");
        if (!errDiv) {
          errDiv = document.createElement("div");
          errDiv.className = "error-msg save-error";
          btn.after(errDiv);
        }
        errDiv.textContent = resultado.error;
      }
    } catch (e) {
      btn.disabled = false;
      btn.textContent = "Reintentar guardar";
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
})();
