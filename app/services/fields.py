"""
Campos que la IA extrae y el usuario puede editar en la tarjeta de revisión
— estructura v2 (ADR-0005 + ADR-0006, docs/areas/planillas/decisions/).
Único lugar a editar si cambian estos campos — lo usan gemini.py (qué
pedirle a la IA) y el frontend (formulario de revisión).

Cód. Proveedor, CUENTA y Fecha de Carga NO están acá: no los completa ni la
IA ni el usuario (ver ADR-0006) — se arman aparte en app/services/sheets.py,
que define el orden completo de columnas de la planilla.
"""

FIELDS = [
    {"key": "fecha", "label": "Emisión", "required": True,
     "description": "Fecha de emisión del comprobante, formato AAAA-MM-DD"},
    {"key": "proveedor", "label": "Proveedor", "required": True,
     "description": "Razón social de quien emite el comprobante"},
    {"key": "cuit", "label": "CUIT", "required": False,
     "description": "CUIT del proveedor (quien emite, no quien recibe), 11 dígitos"},
    {"key": "categoria", "label": "Categoría", "required": False,
     "description": (
         "Clasificación libre del gasto (ej. Combustible, Insumos, Servicios, Alquiler, "
         "Mantenimiento, Honorarios, etc.) según lo que se compró. No uses una lista fija: "
         "elegí la categoría que mejor describa el gasto según el proveedor y los ítems del "
         "comprobante."
     )},
    {"key": "tipo", "label": "Tipo Factura", "required": False,
     "description": (
         "Letra del comprobante (A, B, C, etc.) tal como está impresa. Si NO ves un CAE "
         "(Código de Autorización Electrónico — un número largo, generalmente junto a un "
         "código de barras o QR) en el comprobante, devolvé 'X' en vez de la letra impresa "
         "— indica un comprobante no autorizado por AFIP (en negro)."
     )},
    {"key": "punto_venta", "label": "Punto de Venta", "required": False,
     "description": "Punto de venta del comprobante (ej. 0001), sin el número de factura"},
    {"key": "numero", "label": "N° de Factura", "required": False,
     "description": "Número de factura, sin el punto de venta"},
    {"key": "neto", "label": "Neto Gravado", "required": False,
     "description": "Neto gravado (sin impuestos), número con punto decimal"},
    {"key": "iva_105", "label": "IVA 10,5%", "required": False,
     "description": "Monto de IVA a la alícuota del 10,5%, si el comprobante lo discrimina por separado"},
    {"key": "iva_21", "label": "IVA 21%", "required": False,
     "description": "Monto de IVA a la alícuota del 21%, si el comprobante lo discrimina por separado"},
    {"key": "iva_27", "label": "IVA 27%", "required": False,
     "description": "Monto de IVA a la alícuota del 27%, si el comprobante lo discrimina por separado"},
    {"key": "perc_iva", "label": "Perc. IVA", "required": False,
     "description": "Percepción de IVA, si el comprobante la discrimina por separado"},
    {"key": "perc_iibb_arba", "label": "Perc. IIBB ARBA", "required": False,
     "description": "Percepción de Ingresos Brutos de ARBA (provincia de Buenos Aires), si aparece"},
    {"key": "iibb_caba", "label": "IIBB CABA", "required": False,
     "description": "Ingresos Brutos de CABA, si aparece"},
    {"key": "ret_ganancias", "label": "Ret. Ganancias", "required": False,
     "description": "Retención de Impuesto a las Ganancias, si aparece"},
    {"key": "ret_iva", "label": "Ret. IVA", "required": False,
     "description": "Retención de IVA, si aparece"},
    {"key": "sirtac", "label": "SIRTAC", "required": False,
     "description": "Monto de SIRTAC, si aparece discriminado por separado"},
    {"key": "imp_internos", "label": "Imp. Internos", "required": False,
     "description": "Impuestos Internos, si aparecen discriminados por separado"},
    {"key": "total", "label": "Total Compra", "required": True,
     "description": "Total del comprobante, número con punto decimal"},
    {"key": "moneda", "label": "Moneda", "required": True, "options": ["ARS", "USD"],
     "description": "ARS si son pesos argentinos, USD si son dólares"},
]

FIELD_KEYS = [f["key"] for f in FIELDS]
