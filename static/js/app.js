(function () {
  "use strict";

  let pendingImgToken = null;
  let pendingObjectUrl = null;

  function showScreen(id) {
    document.querySelectorAll(".screen").forEach((s) => {
      s.classList.toggle("active", s.id === id);
      s.classList.toggle("hidden", s.id !== id);
    });
  }

  function setStatus(msg, isError) {
    const el = document.getElementById("review-status");
    if (!el) return;
    el.textContent = msg;
    el.className = "status-msg" + (isError ? " error" : "");
  }

  function clearStatus() {
    const el = document.getElementById("review-status");
    if (el) el.className = "status-msg hidden";
  }

  function populateForm(fields) {
    const form = document.getElementById("review-form");
    if (!form) return;
    Object.entries(fields || {}).forEach(([key, val]) => {
      const input = form.elements[key];
      if (input && val !== null && val !== undefined) input.value = val;
    });
  }

  async function startExtract(file) {
    showScreen("screen-review");
    setStatus("Extrayendo datos…", false);
    document.getElementById("btn-save").disabled = true;

    if (pendingObjectUrl) URL.revokeObjectURL(pendingObjectUrl);
    pendingObjectUrl = URL.createObjectURL(file);
    document.getElementById("review-image").src = pendingObjectUrl;

    // Reset form
    document.getElementById("review-form").reset();

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("/api/extract", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Error desconocido");
      populateForm(data.fields);
      pendingImgToken = data.img_token;
      clearStatus();
      document.getElementById("btn-save").disabled = false;
    } catch (err) {
      setStatus("Error al extraer: " + err.message, true);
    }
  }

  // Photo input
  const photoInput = document.getElementById("photo-input");
  if (photoInput) {
    photoInput.addEventListener("change", async () => {
      const file = photoInput.files[0];
      if (!file) return;
      photoInput.value = "";
      await startExtract(file);
    });
  }

  // Save invoice
  const reviewForm = document.getElementById("review-form");
  if (reviewForm) {
    reviewForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btn-save");
      btn.disabled = true;
      setStatus("Guardando…", false);

      const data = { img_token: pendingImgToken };
      new FormData(reviewForm).forEach((val, key) => {
        data[key] = val === "" ? null : val;
      });

      try {
        const res = await fetch("/api/invoices", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || "Error al guardar");
        }
        pendingImgToken = null;
        showScreen("screen-capture");
        loadInvoices();
      } catch (err) {
        setStatus("Error: " + err.message, true);
        btn.disabled = false;
      }
    });
  }

  // Cancel
  const btnCancel = document.getElementById("btn-cancel");
  if (btnCancel) {
    btnCancel.addEventListener("click", () => {
      pendingImgToken = null;
      showScreen("screen-capture");
    });
  }

  // Load recent invoices
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
            <span class="inv-razon">${esc(inv.razon_social || "—")}</span>
            <span class="inv-total">$${esc(inv.total || "—")}</span>
            <span class="inv-fecha">${esc(inv.fecha || "")}</span>
          </div>`
        )
        .join("");
    } catch {
      list.innerHTML = '<p class="list-error">Error al cargar facturas.</p>';
    }
  }

  function esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Init
  if (document.getElementById("screen-capture")) loadInvoices();
})();
