"""
Definición de campos de la plantilla activa ("Facturas AFIP").
Único lugar a editar si cambian, se agregan o se quitan columnas —
lo usan gemini.py (qué pedirle a la IA), sheets.py (encabezados/orden
de columnas) y el frontend (formulario de revisión).
"""

FIELDS = [
    {"key": "fecha", "label": "Fecha", "required": True,
     "description": "Fecha de emisión del comprobante, formato AAAA-MM-DD"},
    {"key": "proveedor", "label": "Proveedor", "required": True,
     "description": "Razón social de quien emite el comprobante"},
    {"key": "cuit", "label": "CUIT", "required": False,
     "description": "CUIT del proveedor (quien emite, no quien recibe), 11 dígitos"},
    {"key": "tipo", "label": "Tipo", "required": False,
     "description": "Tipo de comprobante: Factura A / Factura B / Factura C / Presupuesto / Nota de Crédito / Remito, etc."},
    {"key": "numero", "label": "Número", "required": False,
     "description": "Número del comprobante, formato punto de venta + número (ej. 0001-00004521)"},
    {"key": "neto", "label": "Neto", "required": False,
     "description": "Neto gravado (sin IVA), número con punto decimal. Vacío en Factura B/C si no se discrimina."},
    {"key": "iva", "label": "IVA", "required": False,
     "description": "Monto de IVA, número con punto decimal. Vacío en Factura B/C si no se discrimina."},
    {"key": "total", "label": "Total", "required": True,
     "description": "Total del comprobante, número con punto decimal"},
    {"key": "moneda", "label": "Moneda", "required": True, "options": ["ARS", "USD"],
     "description": "ARS si son pesos argentinos, USD si son dólares"},
]

FIELD_KEYS = [f["key"] for f in FIELDS]
