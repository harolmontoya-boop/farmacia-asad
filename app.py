import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import os, json, re, io
from datetime import datetime, date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# -------------------------------------------------------------
# 1. CONFIGURACIÓN GENERAL Y DIRECTORIOS LOCALES
# -------------------------------------------------------------
st.set_page_config(
    page_title="ASAD IPS - Servicio Farmacéutico",
    page_icon="💊",
    layout="wide"
)

DIR_DATOS = "datos"
DIR_ACTAS_GEN = os.path.join(DIR_DATOS, "actas", "generadas")
DIR_ACTAS_FIR = os.path.join(DIR_DATOS, "actas", "firmadas")
DIR_DISP_FIR = os.path.join(DIR_DATOS, "dispensacion", "firmadas")
DIR_CONTEOS_PDF = os.path.join(DIR_DATOS, "conteos", "actas_pdf")
DIR_RESPEL_ARCH = os.path.join(DIR_DATOS, "respel", "archivos")

for d in [DIR_DATOS, DIR_ACTAS_GEN, DIR_ACTAS_FIR, DIR_DISP_FIR, DIR_CONTEOS_PDF, DIR_RESPEL_ARCH]:
    os.makedirs(d, exist_ok=True)

RUTA_CFG = os.path.join(DIR_DATOS, "config_ubicaciones.json")

def normalizar(t):
    s = str(t).lower()
    for a, b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")): 
        s = s.replace(a, b)
    return re.sub(r'_+', '_', re.sub(r'[^a-z0-9_]', '_', s)).strip('_')

# -------------------------------------------------------------
# 2. CONFIGURACIÓN Y CONTROL AMBIENTAL
# -------------------------------------------------------------
def cargar_cfg():
    if not os.path.exists(RUTA_CFG):
        init = {
            "Sede Ibagué": {"Ambientes": ["Farmacia Dispensación", "Farmacia Almacenamiento"], "Neveras": ["Nevera Farmacia", "Nevera toma de muestras 01"]},
            "Sede Fusagasugá": {"Ambientes": ["Ambiente Almacén N°1", "Ambiente Almacén N°2"], "Neveras": ["Nevera toma de muestra de laboratorio"]}
        }
        with open(RUTA_CFG, "w", encoding="utf-8") as f: 
            json.dump(init, f, ensure_ascii=False, indent=4)
        return init
    with open(RUTA_CFG, "r", encoding="utf-8") as f: 
        return json.load(f)

def guardar_ub(sede, tipo, nom):
    c = cargar_cfg()
    if sede in c and tipo in c[sede] and nom not in c[sede][tipo]:
        c[sede][tipo].append(nom)
        with open(RUTA_CFG, "w", encoding="utf-8") as f: 
            json.dump(c, f, ensure_ascii=False, indent=4)
        return True
    return False

def ruta_temp(fec, sede, tipo, esp):
    p = "ambiente" if tipo == "Ambientes" else "nevera"
    return os.path.join(DIR_DATOS, f"temp_{p}_{normalizar(sede)}_{normalizar(esp)}_{fec.year}_{fec.month:02d}.xlsx")

def cargar_temp(fec, sede, tipo, esp):
    r = ruta_temp(fec, sede, tipo, esp)
    cols = ["Día", "Temp Amb (M)", "Temp Amb (T)", "Humedad % (M)", "Humedad % (T)", "Responsable (M)", "Responsable (T)", "Estado", "Observaciones"] if tipo == "Ambientes" else ["Día", "Temp Nevera (M)", "Temp Nevera (T)", "Responsable (M)", "Responsable (T)", "Estado", "Observaciones"]
    if os.path.exists(r): 
        return pd.read_excel(r)
    df = pd.DataFrame(index=range(31), columns=cols)
    df["Día"] = list(range(1, 32))
    df["Estado"] = "Pendiente"
    df.to_excel(r, index=False)
    return df

# -------------------------------------------------------------
# 3. KARDEX, FEFO Y SEMAFORIZACIÓN (RESOLUCIÓN 3100)
# -------------------------------------------------------------
COLS_K = {
    "Medicamentos": ("Medicamentos", ["Item", "Factura_Remision", "Proveedor", "Fecha Ingreso", "Nombre Comercial", "Principio Activo", "Forma Farmaceutica", "Concentracion", "Presentacion", "Via Administracion", "Unidad Medida", "Laboratorio", "Lote", "Registro INVIMA", "Estado INVIMA", "Temp Transporte", "Fecha Caducidad", "Analisis Calidad", "Defecto Critico", "Cantidad", "Responsable Tecnico", "Cargo Responsable", "Semaforizacion"], "Fecha Caducidad"),
    "Dispositivos Médicos": ("Dispositivos_Medicos", ["Item", "Factura_Remision", "Proveedor", "Fecha Ingreso", "Nombre Dispositivo", "Marca", "Laboratorio", "Serie", "Lote", "Presentacion Comercial", "Registro INVIMA", "Estado INVIMA", "Clasificacion Riesgo", "Fecha Caducidad", "Analisis Calidad", "Defecto Critico", "Cantidad", "Responsable Tecnico", "Cargo Responsable", "Semaforizacion"], "Fecha Caducidad"),
    "Insumos": ("Insumos", ["Item", "Factura_Remision", "Proveedor", "Fecha Ingreso", "Nombre Insumo", "Marca", "Laboratorio", "Serie", "Lote", "Presentacion", "Registro INVIMA", "Estado INVIMA", "Clasificacion Riesgo", "Fecha Caducidad", "Analisis Calidad", "Defecto Critico", "Cantidad", "Responsable Tecnico", "Cargo Responsable", "Semaforizacion"], "Fecha Caducidad"),
    "Reactivos": ("Reactivos", ["Item", "Factura_Remision", "Proveedor", "Fecha Ingreso", "Nombre Reactivo", "Marca", "Laboratorio", "Lote", "Presentacion", "Registro INVIMA", "Estado INVIMA", "Clasificacion Riesgo", "Temp Transporte", "Fecha Vencimiento", "Analisis Calidad", "Defecto Critico", "Cantidad", "Responsable Tecnico", "Cargo Responsable", "Semaforizacion"], "Fecha Vencimiento")
}

def ruta_kardex(sede): 
    return os.path.join(DIR_DATOS, f"kardex_{normalizar(sede)}.xlsx")

def cargar_k(sede, cat):
    r = ruta_kardex(sede)
    sh, cols, _ = COLS_K[cat]
    if not os.path.exists(r):
        with pd.ExcelWriter(r, engine="openpyxl") as w:
            for c, (s, cl, _) in COLS_K.items(): 
                pd.DataFrame(columns=cl).to_excel(w, sheet_name=s, index=False)
    try:
        df = pd.read_excel(r, sheet_name=sh)
        for c in cols:
            if c not in df.columns: 
                df[c] = np.nan
        return df[cols]
    except Exception: 
        return pd.DataFrame(columns=cols)

def guardar_k(sede, cat, df):
    r = ruta_kardex(sede)
    sh, _, _ = COLS_K[cat]
    with pd.ExcelWriter(r, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name=sh, index=False)

def semaforo(v):
    if pd.isna(v) or str(v).strip() in ["", "nan", "N/A", "NaT", "None"]: 
        return "SIN FECHA", 999
    try:
        f = datetime.strptime(str(v)[:10], "%Y-%m-%d").date() if "-" in str(v)[:10] else datetime.strptime(str(v)[:10], "%d/%m/%Y").date()
    except Exception: 
        return "FECHA INVÁLIDA", 999
    dias = (f - date.today()).days
    m = dias / 30.4375
    if dias < 0: 
        return "🔴 VENCIDO", 0
    if m <= 3: 
        return f"🔴 CRÍTICO ({max(0,int(m))} m)", int(m)
    if m <= 6: 
        return f"🟡 ALERTA ({int(m)} m)", int(m)
    return f"🟢 ÓPTIMO ({int(m)} m)", int(m)

def plantilla_kardex(cat):
    _, cols, _ = COLS_K[cat]
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        pd.DataFrame(columns=[c for c in cols if c not in ["Item", "Semaforizacion"]]).to_excel(w, index=False, sheet_name=cat[:31])
    return out.getvalue()

def exportar_kardex_activo(sede):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        for cat, (sh, cols, col_f) in COLS_K.items():
            df = cargar_k(sede, cat)
            if not df.empty:
                df_act = df[pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0) > 0].copy()
                if col_f in df_act.columns: 
                    df_act["Semaforizacion"] = df_act[col_f].apply(lambda x: semaforo(x)[0])
                df_act["Item"] = range(1, len(df_act) + 1)
                df_act.to_excel(w, sheet_name=sh, index=False)
            else:
                pd.DataFrame(columns=cols).to_excel(w, sheet_name=sh, index=False)
    return out.getvalue()

def buscar_soporte(dir_base, prefijo):
    if os.path.exists(dir_base):
        for a in os.listdir(dir_base):
            if a.startswith(prefijo): 
                return os.path.join(dir_base, a), a
    return None, None

def guardar_archivo(dir_base, archivo, nombre_base):
    _, ext = os.path.splitext(archivo.name)
    nom = f"{nombre_base}{ext.lower()}"
    with open(os.path.join(dir_base, nom), "wb") as f: 
        f.write(archivo.getbuffer())
    return nom

def smart_col(col_map, *keys):
    for k in keys:
        for norm, orig in col_map.items():
            if norm == k: 
                return orig
    for k in keys:
        for norm, orig in col_map.items():
            if k == "NOMBRE" and ("BOD" in norm or "BO2" in norm): 
                continue
            if k in norm: 
                return orig
    return None

# GENERADOR PDF RECEPCIÓN TÉCNICA
def generar_pdf_recepcion(datos, df_items):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), leftMargin=25, rightMargin=25, topMargin=25, bottomMargin=25)
    st_th = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.white, alignment=1)
    st_td = ParagraphStyle('TD', fontName='Helvetica', fontSize=7, alignment=1)
    st_tdl = ParagraphStyle('TDL', fontName='Helvetica', fontSize=7, alignment=0)
    st_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=9.5, alignment=1, textColor=colors.HexColor('#003366'))
    st_h2 = ParagraphStyle('H2', fontName='Helvetica', fontSize=7.5, alignment=1, textColor=colors.HexColor('#333333'))
    
    elems = [
        Table([[Paragraph("<b>ASAD ASISTENCIA EN SALUD DOMICILIARIA SAS</b><br/><font size=6.5>HABILITACIÓN SERVICIO FARMACÉUTICO - RESOLUCIÓN 3100 DE 2019</font>", st_h1),
                Paragraph("<b>ACTA INSTITUCIONAL DE RECEPCIÓN TÉCNICA DE INSUMOS</b><br/><font size=6.5>Proceso: Gestión de Recursos Físicos / Calidad Asistencial</font>", st_h1),
                Paragraph(f"<b>CÓDIGO:</b> GCA-DC-FT-04<br/><b>VERSIÓN:</b> 002<br/><b>FECHA:</b> {datos['fecha']}", st_h2)]], colWidths=[240, 310, 190],
              style=[('BOX', (0,0), (-1,-1), 1, colors.HexColor('#003366')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#003366')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 3)]),
        Spacer(1, 6),
        Table([[Paragraph(f"<b>SEDE:</b> {datos['sede']}", st_tdl), Paragraph(f"<b>PROVEEDOR:</b> {datos['proveedor']}", st_tdl), Paragraph(f"<b>N° FACTURA:</b> {datos['factura']}", st_tdl), Paragraph(f"<b>CATEGORÍA:</b> {datos['categoria']}", st_tdl)],
               [Paragraph(f"<b>FECHA INGRESO:</b> {datos['fecha']}", st_tdl), Paragraph(f"<b>RESPONSABLE:</b> {datos['responsable']}", st_tdl), Paragraph(f"<b>CARGO:</b> {datos['cargo']}", st_tdl), Paragraph(f"<b>TOTAL ÍTEMS:</b> {len(df_items)}", st_tdl)]],
              colWidths=[185, 195, 185, 175], style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 3)]),
        Spacer(1, 6)
    ]
    
    rows = [[Paragraph(h, st_th) for h in ["#", "Descripción del Insumo / Medicamento", "Lote", "Venc.", "INVIMA", "Estado", "Cant.", "Inspección", "Defecto", "Semaforización"]]]
    for idx, r in df_items.iterrows():
        nom = r.get("Nombre Comercial") or r.get("Nombre Dispositivo") or r.get("Nombre Insumo") or r.get("Nombre Reactivo") or "N/A"
        rows.append([Paragraph(str(idx+1), st_td), Paragraph(str(nom), st_tdl), Paragraph(str(r.get("Lote","N/A")), st_td), Paragraph(str(r.get("Fecha Caducidad") or r.get("Fecha Vencimiento") or "N/A")[:10], st_td),
                     Paragraph(str(r.get("Registro INVIMA","N/A")), st_td), Paragraph(str(r.get("Estado INVIMA","VIGENTE"))[:7], st_td), Paragraph(str(r.get("Cantidad","0")), st_td),
                     Paragraph(str(r.get("Analisis Calidad","OK"))[:6], st_td), Paragraph(str(r.get("Defecto Critico","NO APLICA"))[:12], st_td), Paragraph(str(r.get("Semaforizacion","N/A")), st_td)])
    
    elems.append(Table(rows, colWidths=[20, 205, 60, 55, 80, 50, 40, 45, 75, 110], repeatRows=1,
                       style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#003366')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                              ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 2), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])]))
    elems.append(Spacer(1, 6))
    elems.append(Table([[Paragraph("<b>CONCEPTO TÉCNICO (RESOLUCIÓN 3100 DE 2019):</b> Se certifica la inspección física y organoléptica de los insumos, rotulado normativo, vigencia de Registro Sanitario INVIMA y concordancia de lote/vencimiento. Productos declarados <b>CONFORMES Y APROBADOS</b> para dispensación.", ParagraphStyle('C', fontName='Helvetica', fontSize=6.5, leading=9))]], colWidths=[740],
                       style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#059669')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ecfdf5')), ('PADDING', (0,0), (-1,-1), 4)]))
    elems.append(Spacer(1, 8))
    elems.append(Table([[Paragraph("<b>ENTREGADO POR (PROVEEDOR / TRANSPORTE):</b><br/><br/><br/>____________________________________________<br/>Nombre y C.C.:", st_tdl),
                         Paragraph(f"<b>RECIBIDO Y APROBADO POR (ASAD IPS):</b><br/><br/><br/>____________________________________________<br/>Firma: {datos['responsable']}<br/>Cargo: {datos['cargo']}", st_tdl)]], colWidths=[370, 370],
                       style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 6)]))
    doc.build(elems)
    pdf = buf.getvalue()
    nom_pdf = f"Acta_Recepcion_{normalizar(datos['sede'])}_{normalizar(datos['factura'])}.pdf"
    with open(os.path.join(DIR_ACTAS_GEN, nom_pdf), "wb") as f: 
        f.write(pdf)
    return pdf, nom_pdf

# -------------------------------------------------------------
# 4. DISPENSACIÓN Y CRUCE DE SALIDAS
# -------------------------------------------------------------
COLS_DISP = ["ID_Entrega", "Fecha_Entrega", "Documento_Paciente", "Nombre_Paciente", "Horario", "Municipio", "Categoria", "Producto", "Cantidad_Entregada", "Cantidad_Descontada_Kardex", "Deficit_Pendiente", "Lotes_Descontados", "Acta_Numero", "Estado_Soporte", "Archivo_Soporte"]
def ruta_disp(sede): 
    return os.path.join(DIR_DATOS, f"dispensacion_{normalizar(sede)}.xlsx")

def cargar_disp(sede):
    r = ruta_disp(sede)
    return pd.read_excel(r) if os.path.exists(r) else pd.DataFrame(columns=COLS_DISP)

def guardar_disp(sede, df): 
    df.to_excel(ruta_disp(sede), index=False)

def resumir_actas(df_disp):
    if df_disp.empty or "Acta_Numero" not in df_disp.columns: 
        return pd.DataFrame()
    v = df_disp[~df_disp["Acta_Numero"].astype(str).str.strip().isin(["N/A", "nan", "", "None"])].copy()
    if v.empty: 
        return pd.DataFrame()
    return v.groupby("Acta_Numero").agg(
        Documento=("Documento_Paciente", "first"), 
        Paciente=("Nombre_Paciente", "first"), 
        Fecha=("Fecha_Entrega", "first"),
        Insumos_Distintos=("Producto", "nunique"), 
        Total_Unidades=("Cantidad_Entregada", "sum"),
        Estado_Soporte=("Estado_Soporte", lambda x: "🟢 Custodiada / Firmada" if (x == "🟢 Custodiada / Firmada").any() else "🟡 Pendiente de Soporte"),
        Archivo_Soporte=("Archivo_Soporte", "first")
    ).reset_index()

def buscar_prod_kardex(sede, nom_prod):
    tgt = str(nom_prod).strip().upper()
    if not tgt: 
        return None, None, None, None, None
    for cat, (sh, cols, col_f) in COLS_K.items():
        df_c = cargar_k(sede, cat)
        if df_c.empty: 
            continue
        col_nom = "Nombre Comercial" if cat == "Medicamentos" else ("Nombre Dispositivo" if cat == "Dispositivos Médicos" else ("Nombre Insumo" if cat == "Insumos" else "Nombre Reactivo"))
        if col_nom not in df_c.columns: 
            continue
        m = df_c[df_c[col_nom].astype(str).str.strip().str.upper() == tgt]
        if not m.empty: 
            return cat, col_nom, col_f, m[col_nom].iloc[0], df_c
        for k_val in df_c[col_nom].dropna().unique():
            k_n = str(k_val).strip().upper()
            if (k_n in tgt and len(k_n)>=4) or (tgt in k_n and len(tgt)>=4):
                return cat, col_nom, col_f, k_val, df_c
    return None, None, None, None, None

# -------------------------------------------------------------
# 5. CONTEO CÍCLICO Y AUDITORÍA CIEGA
# -------------------------------------------------------------
COLS_CNT_RES = ["Consecutivo", "Fecha", "Sede", "Auxiliar", "Auditor", "Total_Items", "Items_Conformes", "Items_Discrepancias", "Porcentaje_ERI", "Archivo_Acta_PDF"]
COLS_CNT_DET = ["Consecutivo", "Item", "Codigo", "Producto", "Lote", "Cantidad_Sistema", "Conteo_Fisico", "Diferencia", "Estado", "Observaciones"]
def ruta_conteos(sede): 
    return os.path.join(DIR_DATOS, "conteos", f"conteos_{normalizar(sede)}.xlsx")

def cargar_conteos(sede):
    r = ruta_conteos(sede)
    if os.path.exists(r):
        try: 
            return pd.read_excel(r, sheet_name="Resumen_Auditorias"), pd.read_excel(r, sheet_name="Detalle_Items")
        except Exception: 
            pass
    return pd.DataFrame(columns=COLS_CNT_RES), pd.DataFrame(columns=COLS_CNT_DET)

def guardar_conteo(sede, df_res, df_det):
    r = ruta_conteos(sede)
    h_res, h_det = cargar_conteos(sede)
    with pd.ExcelWriter(r, engine="openpyxl") as w:
        pd.concat([h_res, df_res], ignore_index=True).to_excel(w, sheet_name="Resumen_Auditorias", index=False)
        pd.concat([h_det, df_det], ignore_index=True).to_excel(w, sheet_name="Detalle_Items", index=False)

def prox_consecutivo_conteo(sede):
    df_res, _ = cargar_conteos(sede)
    pfx = f"AUD-{date.today().year}-"
    if df_res.empty or "Consecutivo" not in df_res.columns: 
        return f"{pfx}0001"
    nums = [int(c.split("-")[-1]) for c in df_res["Consecutivo"].dropna().astype(str) if c.startswith(pfx) and c.split("-")[-1].isdigit()]
    return f"{pfx}{(max(nums)+1 if nums else 1):04d}"

def generar_pdf_conteo(datos, df_det):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), leftMargin=25, rightMargin=25, topMargin=25, bottomMargin=25)
    st_th = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.white, alignment=1)
    st_td = ParagraphStyle('TD', fontName='Helvetica', fontSize=7, alignment=1)
    st_tdl = ParagraphStyle('TDL', fontName='Helvetica', fontSize=7, alignment=0)
    st_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=9.5, alignment=1, textColor=colors.HexColor('#003366'))
    st_h2 = ParagraphStyle('H2', fontName='Helvetica', fontSize=7.5, alignment=1, textColor=colors.HexColor('#333333'))
    
    elems = [
        Table([[Paragraph("<b>ASAD ASISTENCIA EN SALUD DOMICILIARIA SAS</b><br/><font size=6.5>HABILITACIÓN SERVICIO FARMACÉUTICO - RESOLUCIÓN 3100 DE 2019</font>", st_h1),
                Paragraph("<b>ACTA INSTITUCIONAL DE AUDITORÍA Y CONTEO CÍCLICO FÍSICO</b><br/><font size=6.5>Proceso: Gestión de Recursos Físicos / Control y Custodia de Farmacia</font>", st_h1),
                Paragraph(f"<b>CÓDIGO:</b> GCA-DC-FT-08<br/><b>VERSIÓN:</b> 001<br/><b>CONSECUTIVO:</b> {datos['consecutivo']}", st_h2)]], colWidths=[240, 310, 190],
              style=[('BOX', (0,0), (-1,-1), 1, colors.HexColor('#003366')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#003366')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 3)]),
        Spacer(1, 6),
        Table([[Paragraph(f"<b>SEDE:</b> {datos['sede']}", st_tdl), Paragraph(f"<b>FECHA:</b> {datos['fecha']}", st_tdl), Paragraph(f"<b>MODALIDAD:</b> Conteo Ciego (Sin sesgo)", st_tdl), Paragraph(f"<b>TOTAL ÍTEMS:</b> {len(df_det)}", st_tdl)],
               [Paragraph(f"<b>AUXILIAR (CONTEO):</b> {datos['auxiliar']}", st_tdl), Paragraph(f"<b>AUDITOR:</b> {datos['auditor']}", st_tdl), Paragraph(f"<b>EXACTITUD ERI:</b> <b>{datos['eri']}%</b>", st_tdl), Paragraph(f"<b>DISCREPANCIAS:</b> {datos['discrepancias']}", st_tdl)]],
              colWidths=[200, 190, 180, 170], style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 3)]),
        Spacer(1, 6)
    ]
    rows = [[Paragraph(h, st_th) for h in ["#", "Código", "Descripción del Insumo / Medicamento", "Lote", "Stock Sistema", "Conteo Físico", "Diferencia", "Estado Auditoría", "Observaciones"]]]
    for idx, r in df_det.iterrows():
        dif = r.get("Diferencia", 0)
        rows.append([Paragraph(str(idx+1), st_td), Paragraph(str(r.get("Codigo","N/A")), st_td), Paragraph(str(r.get("Producto","N/A")), st_tdl), Paragraph(str(r.get("Lote","N/A")), st_td),
                     Paragraph(str(r.get("Cantidad_Sistema", 0)), st_td), Paragraph(str(r.get("Conteo_Fisico", 0)), st_td), Paragraph(f"+{dif}" if dif>0 else str(dif), st_td),
                     Paragraph(str(r.get("Estado","Conforme")), st_td), Paragraph(str(r.get("Observaciones","Sin novedad"))[:35], st_tdl)])
    elems.append(Table(rows, colWidths=[20, 50, 220, 60, 60, 60, 50, 90, 130], repeatRows=1,
                       style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#003366')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                              ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 2), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])]))
    elems.append(Spacer(1, 6))
    elems.append(Table([[Paragraph(f"<b>DICTAMEN TÉCNICO:</b> Procedimiento de conteo físico ciego a la muestra de farmacia. Exactitud de Registro (ERI): <b>{datos['eri']}%</b>. Diferencias consignadas para investigación interna sin alteración del Kardex contable.", ParagraphStyle('D', fontName='Helvetica', fontSize=6.5, leading=9))]], colWidths=[740],
                       style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#0284c7')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')), ('PADDING', (0,0), (-1,-1), 4)]))
    elems.append(Spacer(1, 8))
    elems.append(Table([[Paragraph(f"<b>REALIZÓ CONTEO FÍSICO:</b><br/><br/><br/>____________________________________________<br/>Firma: {datos['auxiliar']}<br/>Cargo: Auxiliar del Servicio Farmacéutico", st_tdl),
                         Paragraph(f"<b>AUDITÓ Y VERIFICÓ:</b><br/><br/><br/>____________________________________________<br/>Firma: {datos['auditor']}<br/>Cargo: Coordinador de Recursos Físicos / Regente", st_tdl)]], colWidths=[370, 370],
                       style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 6)]))
    doc.build(elems)
    pdf = buf.getvalue()
    nom_pdf = f"Acta_Conteo_{normalizar(datos['sede'])}_{datos['consecutivo']}.pdf"
    with open(os.path.join(DIR_CONTEOS_PDF, nom_pdf), "wb") as f: 
        f.write(pdf)
    return pdf, nom_pdf

# -------------------------------------------------------------
# 6. ARCHIVO DE DEVOLUCIONES Y RESPEL
# -------------------------------------------------------------
COLS_RESPEL = ["ID_Archivo", "Fecha_Cargue", "Fecha_Documento", "Sede", "Tipo_Documento", "Numero_Acta_Manifiesto", "Entidad_Tercero", "Motivo_Detalle", "Responsable", "Nombre_Archivo"]
def ruta_respel(sede): 
    return os.path.join(DIR_DATOS, "respel", f"archivo_respel_{normalizar(sede)}.xlsx")

def cargar_respel(sede):
    r = ruta_respel(sede)
    return pd.read_excel(r) if os.path.exists(r) else pd.DataFrame(columns=COLS_RESPEL)

def guardar_respel(sede, df): 
    df.to_excel(ruta_respel(sede), index=False)

# -------------------------------------------------------------
# 7. MENÚ LATERAL Y NAVEGACIÓN DE FARMACIA
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏥 **ASAD IPS**")
    st.caption("Macroproceso: Recursos Físicos")
    st.caption("Subproceso: **Servicio Farmacéutico**")
    st.markdown("---")

    modulo = option_menu(
        menu_title=None,
        options=["Factores Ambientales", "Recepción y Kardex", "Semaforización (FEFO)", "Dispensación", "Conteo Cíclico", "Devoluciones / RESPEL"],
        icons=["thermometer-half", "box-seam", "traffic-light", "bag-check", "clipboard-check", "trash"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#ffffff"},
            "icon": {"font-size": "15px"},
            "nav-link": {
                "font-size": "14px", "text-align": "left", "margin": "2px 0px",
                "padding": "10px 14px", "border-bottom": "1px solid #f1f5f9",
                "border-radius": "6px", "color": "#334155", "--hover-color": "#f8fafc"
            },
            "nav-link-selected": {"background-color": "#007bc7", "color": "#ffffff", "font-weight": "600"}
        }
    )
    st.markdown("---")
    st.caption("Sistema de Aseguramiento de Calidad\nResolución 3100 de 2019")

st.markdown("## 💊 Servicio Farmacéutico")

cfg = cargar_cfg()

# =============================================================
# SUBMÓDULO 1: FACTORES AMBIENTALES
# =============================================================
if modulo == "Factores Ambientales":
    st.markdown("#### **Control de Temperatura y Humedad**")
    c0, c1, c2, c3 = st.columns([1.2, 1.2, 1.6, 1.0])
    sede_activa = c0.selectbox("🏢 Sede Operativa:", ["Sede Ibagué", "Sede Fusagasugá"], key="amb_sede_activa")
    tipo_ctrl = c1.selectbox("⚙️ Tipo de Control:", ["Ambientes", "Neveras"], key="t_tipo")
    esp_ctrl = c2.selectbox(f"📍 Seleccione {'Ambiente' if tipo_ctrl=='Ambientes' else 'Nevera'}:", cfg[sede_activa][tipo_ctrl], key="t_esp")
    fec_ctrl = c3.date_input("📅 Fecha:", datetime.now(), key="t_fec")
    
    with st.expander("➕ Añadir nuevo ambiente o nevera"):
        ca1, ca2, ca3 = st.columns([1,1,2])
        n_s = ca1.selectbox("Sede:", list(cfg.keys()), key="add_s")
        n_t = ca2.selectbox("Tipo:", ["Ambientes", "Neveras"], key="add_t")
        n_n = ca3.text_input("Nombre del nuevo espacio / equipo:")
        if st.button("Guardar Ubicación"):
            if n_n.strip() and guardar_ub(n_s, n_t, n_n.strip()):
                st.success("Añadido con éxito.")
                st.rerun()

    t1, t2, t3 = st.tabs(["📝 Registro Diario", "📊 Planilla Mensual y Promedios", "📈 Gráfica de Tendencia"])
    df_t = cargar_temp(fec_ctrl, sede_activa, tipo_ctrl, esp_ctrl)
    d_idx = fec_ctrl.day - 1

    with t1:
        if st.checkbox(f"Marcar día {fec_ctrl.day} como DÍA NO LABORADO (Fin de semana / Festivo / Cierre)", key="chk_nolab"):
            st.info("El día quedará registrado como NO LABORADO.")
            r_obs = st.text_input("Observación:", value="Día no hábil / Cierre")
            r_usr = st.text_input("Responsable del reporte:")
            if st.button("Guardar como No Laborado"):
                df_t.at[d_idx, "Estado"] = "NO LABORADO"
                df_t.at[d_idx, "Observaciones"] = r_obs
                df_t.at[d_idx, "Responsable (M)"] = r_usr
                df_t.to_excel(ruta_temp(fec_ctrl, sede_activa, tipo_ctrl, esp_ctrl), index=False)
                st.success("Guardado.")
                st.rerun()
        else:
            turno = st.radio("Turno:", ["Mañana (AM)", "Tarde (PM)"], horizontal=True)
            suf = "(M)" if turno == "Mañana (AM)" else "(T)"
            with st.form("form_temp"):
                if tipo_ctrl == "Ambientes":
                    c_tmp, c_hum = st.columns(2)
                    v_t = c_tmp.number_input(f"Temp. Ambiente {suf} (°C):", value=float(df_t.at[d_idx, f"Temp Amb {suf}"]) if pd.notna(df_t.at[d_idx, f"Temp Amb {suf}"]) else 23.0, step=0.1)
                    v_h = c_hum.number_input(f"Humedad Relativa {suf} (%):", value=float(df_t.at[d_idx, f"Humedad % {suf}"]) if pd.notna(df_t.at[d_idx, f"Humedad % {suf}"]) else 55.0, step=0.1)
                    if v_t > 30.0: 
                        st.warning("⚠️ Temp. superior a 30°C.")
                    if v_h < 50.0 or v_h > 70.0: 
                        st.warning("⚠️ Humedad fuera de rango normativo (50%-70%).")
                else:
                    tarde_na = False
                    if turno == "Mañana (AM)":
                        c_fr, c_chk = st.columns([1, 1.5])
                        v_fr = c_fr.number_input("Temp. Nevera (M) (°C):", value=float(df_t.at[d_idx, "Temp Nevera (M)"]) if pd.notna(df_t.at[d_idx, "Temp Nevera (M)"]) else 4.0, step=0.1)
                        tarde_na = c_chk.checkbox("📦 Asentar turno Tarde como N/A (Sin servicio)")
                    else:
                        es_na = st.checkbox("Turno Tarde: Sin servicio (Marcar N/A)", value=(df_t.at[d_idx, "Temp Nevera (T)"] == "N/A"))
                        v_fr = "N/A" if es_na else st.number_input("Temp. Nevera (T) (°C):", value=float(df_t.at[d_idx, "Temp Nevera (T)"]) if (pd.notna(df_t.at[d_idx, "Temp Nevera (T)"]) and df_t.at[d_idx, "Temp Nevera (T)"] != "N/A") else 4.0, step=0.1)
                
                resp = st.text_input(f"Responsable {suf}:", value=str(df_t.at[d_idx, f"Responsable {suf}"]) if pd.notna(df_t.at[d_idx, f"Responsable {suf}"]) else "")
                obs = st.text_area("Observaciones:", value=str(df_t.at[d_idx, "Observaciones"]) if pd.notna(df_t.at[d_idx, "Observaciones"]) else "")
                
                if st.form_submit_button("Guardar Registro"):
                    if not resp.strip(): 
                        st.error("Digite el nombre del responsable.")
                    else:
                        if tipo_ctrl == "Ambientes":
                            df_t.at[d_idx, f"Temp Amb {suf}"] = v_t
                            df_t.at[d_idx, f"Humedad % {suf}"] = v_h
                        else:
                            if turno == "Mañana (AM)":
                                df_t.at[d_idx, "Temp Nevera (M)"] = v_fr
                                if tarde_na: 
                                    df_t.at[d_idx, "Temp Nevera (T)"] = "N/A"
                                    df_t.at[d_idx, "Responsable (T)"] = resp
                            else:
                                df_t.at[d_idx, "Temp Nevera (T)"] = v_fr
                        df_t.at[d_idx, f"Responsable {suf}"] = resp.strip()
                        df_t.at[d_idx, "Estado"] = "Laborado"
                        if obs.strip(): 
                            df_t.at[d_idx, "Observaciones"] = obs.strip()
                        df_t.to_excel(ruta_temp(fec_ctrl, sede_activa, tipo_ctrl, esp_ctrl), index=False)
                        st.success("Guardado exitoso.")
                        st.rerun()

    with t2:
        st.write(f"### Sábana de Control: **{sede_activa}** — *{esp_ctrl}* ({fec_ctrl.strftime('%B %Y')})")
        if tipo_ctrl == "Ambientes":
            m_t = pd.to_numeric(pd.concat([df_t["Temp Amb (M)"], df_t["Temp Amb (T)"]]), errors="coerce").dropna()
            m_h = pd.to_numeric(pd.concat([df_t["Humedad % (M)"], df_t["Humedad % (T)"]]), errors="coerce").dropna()
            c1, c2 = st.columns(2)
            c1.metric("Promedio Temp.", f"{m_t.mean():.1f} °C" if not m_t.empty else "0.0 °C", "Máx 30°C", delta_color="off")
            c2.metric("Promedio Humedad", f"{m_h.mean():.1f} %" if not m_h.empty else "0.0 %", "50% - 70%", delta_color="off")
        else:
            m_f = pd.to_numeric(pd.concat([df_t["Temp Nevera (M)"], df_t["Temp Nevera (T)"]]), errors="coerce").dropna()
            st.metric("Promedio Nevera", f"{m_f.mean():.1f} °C" if not m_f.empty else "0.0 °C", "2°C - 8°C", delta_color="off")
        st.dataframe(df_t, use_container_width=True, hide_index=True)
        with open(ruta_temp(fec_ctrl, sede_activa, tipo_ctrl, esp_ctrl), "rb") as f:
            st.download_button("📥 Descargar Planilla Excel", data=f, file_name=f"temp_{normalizar(sede_activa)}_{normalizar(esp_ctrl)}_{fec_ctrl.year}_{fec_ctrl.month:02d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with t3:
        df_g = df_t[df_t["Estado"] == "Laborado"].copy()
        if not df_g.empty:
            if tipo_ctrl == "Ambientes":
                df_g["Temp Prom"] = df_g[["Temp Amb (M)", "Temp Amb (T)"]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
                df_g["Hum Prom"] = df_g[["Humedad % (M)", "Humedad % (T)"]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
                st.line_chart(df_g.set_index("Día")[["Temp Prom", "Hum Prom"]])
            else:
                df_g["Temp Nevera"] = df_g[["Temp Nevera (M)", "Temp Nevera (T)"]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
                st.line_chart(df_g.set_index("Día")[["Temp Nevera"]])

# =============================================================
# SUBMÓDULO 2: RECEPCIÓN TÉCNICA Y KARDEX
# =============================================================
elif modulo == "Recepción y Kardex":
    st.markdown("#### **Recepción Técnica y Kardex Institucional**")
    c_s, c_k = st.columns([1.5, 2.0])
    sede_activa = c_s.selectbox("🏢 Sede Operativa:", ["Sede Ibagué", "Sede Fusagasugá"], key="rec_sede_activa")
    cat_k = c_k.selectbox("📦 Categoría:", list(COLS_K.keys()), key="rk_cat")
    k1, k2, k3 = st.tabs(["📥 Registro Individual", "📂 Cargue Masivo con Acta PDF", "📋 Kardex Activo e Historial de Actas"])

    with k1:
        df_k = cargar_k(sede_activa, cat_k)
        with st.form("form_recep_ind"):
            st.write(f"##### Recepción Técnica: **{cat_k}** (Ítem #{len(df_k)+1})")
            c1, c2, c3 = st.columns(3)
            fac = c1.text_input("N° Factura / Remisión (*):")
            prov = c2.text_input("Proveedor:")
            f_ing = c3.date_input("Fecha Ingreso:", datetime.now())
            
            c4, c5, c6 = st.columns(3)
            p_nom = c4.text_input("Nombre Comercial / Descripción (*):")
            p_lot = c5.text_input("Lote (*):")
            p_inv = c6.text_input("Registro Sanitario INVIMA:")
            
            c7, c8, c9 = st.columns(3)
            f_venc = c7.date_input("Fecha Caducidad / Vencimiento:", datetime.now())
            p_cant = c8.number_input("Cantidad Recibida (*):", min_value=1, step=1, value=10)
            p_cal = c9.selectbox("Inspección Organoléptica:", ["OK (Conforme / Aprobado)", "RECHAZADO"])
            
            c10, c11 = st.columns(2)
            resp_rec = c10.text_input("Responsable Técnico (*):", value="Harol Montoya")
            cargo_rec = c11.selectbox("Cargo:", ["Auxiliar del Servicio Farmacéutico", "Regente de Farmacia", "Químico Farmacéutico", "Coordinador de Recursos Físicos"])
            
            sem_txt, _ = semaforo(f_venc)
            st.info(f"🚦 **Semaforización Automática (FEFO):** {sem_txt}")
            
            if st.form_submit_button("Guardar en Kardex y Emitir Acta PDF"):
                if not fac.strip() or not p_nom.strip() or not p_lot.strip() or not resp_rec.strip():
                    st.error("Factura, Producto, Lote y Responsable son obligatorios.")
                else:
                    col_nom = "Nombre Comercial" if cat_k=="Medicamentos" else ("Nombre Dispositivo" if cat_k=="Dispositivos Médicos" else ("Nombre Insumo" if cat_k=="Insumos" else "Nombre Reactivo"))
                    col_fec = COLS_K[cat_k][2]
                    row_dict = {
                        "Item": len(df_k)+1, "Factura_Remision": fac.strip(), "Proveedor": prov.strip() or "PROVEEDOR GENERAL", "Fecha Ingreso": f_ing.strftime("%Y-%m-%d"),
                        col_nom: p_nom.strip(), "Lote": p_lot.strip(), "Registro INVIMA": p_inv.strip(), "Estado INVIMA": "VIGENTE",
                        col_fec: f_venc.strftime("%Y-%m-%d"), "Cantidad": p_cant, "Analisis Calidad": p_cal, "Defecto Critico": "NO APLICA",
                        "Responsable Tecnico": resp_rec.strip(), "Cargo Responsable": cargo_rec, "Semaforizacion": sem_txt
                    }
                    df_new = pd.DataFrame([row_dict])
                    guardar_k(sede_activa, cat_k, pd.concat([df_k, df_new], ignore_index=True))
                    pdf_b, nom_p = generar_pdf_recepcion({'sede': sede_activa, 'proveedor': prov or 'PROVEEDOR GENERAL', 'factura': fac.strip(), 'categoria': cat_k, 'fecha': f_ing.strftime("%Y-%m-%d"), 'responsable': resp_rec.strip(), 'cargo': cargo_rec}, df_new)
                    st.session_state["pdf_ind"] = (pdf_b, nom_p)
                    st.success("Guardado con éxito.")
                    st.rerun()

        if "pdf_ind" in st.session_state:
            st.download_button(f"📥 Descargar Acta PDF ({st.session_state['pdf_ind'][1]})", data=st.session_state["pdf_ind"][0], file_name=st.session_state["pdf_ind"][1], mime="application/pdf")

    with k2:
        st.write(f"##### 📂 Cargue Masivo ({cat_k})")
        st.download_button("📥 Descargar Plantilla Excel", data=plantilla_kardex(cat_k), file_name=f"plantilla_{normalizar(cat_k)}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        c1, c2 = st.columns(2)
        m_fac = c1.text_input("N° Factura / Remisión (*):", key="m_fac")
        m_prov = c2.text_input("Proveedor:", key="m_prov")
        c3, c4 = st.columns(2)
        m_resp = c3.text_input("Responsable Técnico (*):", key="m_resp", value="Harol Montoya")
        m_cargo = c4.selectbox("Cargo:", ["Auxiliar del Servicio Farmacéutico", "Regente de Farmacia", "Químico Farmacéutico", "Coordinador de Recursos Físicos"], key="m_cargo")
        up_k = st.file_uploader("Subir archivo Excel diligenciado:", type=["xlsx", "xls"], key="up_k_mas")
        if up_k and m_fac.strip() and m_resp.strip():
            try:
                df_raw = pd.read_excel(up_k)
                cmap = {re.sub(r'\\s+', ' ', str(c).upper().strip()): c for c in df_raw.columns}
                c_nom = smart_col(cmap, "NOMBRE", "PRODUCTO", "DESCRIPCION", "INSUMO", "MEDICAMENTO")
                c_lot = smart_col(cmap, "LOTE")
                c_cnt = smart_col(cmap, "CANTIDAD", "CANT")
                c_fec = smart_col(cmap, "CADUCIDAD", "VENCIMIENTO", "FECHA")
                if c_nom and c_cnt:
                    col_nom = "Nombre Comercial" if cat_k=="Medicamentos" else ("Nombre Dispositivo" if cat_k=="Dispositivos Médicos" else ("Nombre Insumo" if cat_k=="Insumos" else "Nombre Reactivo"))
                    col_fec = COLS_K[cat_k][2]
                    df_proc = pd.DataFrame()
                    df_proc["Factura_Remision"] = m_fac.strip()
                    df_proc["Proveedor"] = m_prov.strip() or "PROVEEDOR GENERAL"
                    df_proc["Fecha Ingreso"] = date.today().strftime("%Y-%m-%d")
                    df_proc[col_nom] = df_raw[c_nom].astype(str).str.strip()
                    df_proc["Lote"] = df_raw[c_lot].astype(str).str.strip() if c_lot else "NA"
                    df_proc["Cantidad"] = pd.to_numeric(df_raw[c_cnt], errors="coerce").fillna(0).astype(int)
                    df_proc[col_fec] = pd.to_datetime(df_raw[c_fec], errors="coerce").dt.strftime("%Y-%m-%d").fillna("N/A") if c_fec else "N/A"
                    df_proc["Semaforizacion"] = df_proc[col_fec].apply(lambda x: semaforo(x)[0])
                    df_proc["Registro INVIMA"] = "N/A"
                    df_proc["Estado INVIMA"] = "VIGENTE"
                    df_proc["Analisis Calidad"] = "OK (Conforme)"
                    df_proc["Defecto Critico"] = "NO APLICA"
                    df_proc["Responsable Tecnico"] = m_resp.strip()
                    df_proc["Cargo Responsable"] = m_cargo
                    df_proc = df_proc[df_proc["Cantidad"] > 0]
                    st.dataframe(df_proc.head(5), use_container_width=True)
                    if st.button("🚀 Confirmar e Importar al Kardex"):
                        cur_k = cargar_k(sede_activa, cat_k)
                        final_k = pd.concat([cur_k, df_proc], ignore_index=True)
                        final_k["Item"] = range(1, len(final_k) + 1)
                        guardar_k(sede_activa, cat_k, final_k)
                        pdf_b, nom_p = generar_pdf_recepcion({'sede': sede_activa, 'proveedor': m_prov or 'PROVEEDOR GENERAL', 'factura': m_fac.strip(), 'categoria': cat_k, 'fecha': date.today().strftime("%Y-%m-%d"), 'responsable': m_resp.strip(), 'cargo': m_cargo}, df_proc)
                        st.session_state["pdf_mas"] = (pdf_b, nom_p)
                        st.success("Importación exitosa.")
                        st.rerun()
            except Exception as e: 
                st.error(f"Error: {e}")
        if "pdf_mas" in st.session_state:
            st.download_button(f"📥 Descargar Acta Oficial ({st.session_state['pdf_mas'][1]})", data=st.session_state["pdf_mas"][0], file_name=st.session_state["pdf_mas"][1], mime="application/pdf")

    with k3:
        df_k = cargar_k(sede_activa, cat_k)
        st.write(f"Mostrando **{len(df_k)}** productos en Kardex ({cat_k}):")
        st.dataframe(df_k, use_container_width=True, hide_index=True)
        c_e1, c_e2 = st.columns(2)
        c_e1.download_button("🟢 Descargar Kardex Activo (Stock > 0)", data=exportar_kardex_activo(sede_activa), file_name=f"kardex_activo_{normalizar(sede_activa)}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if os.path.exists(ruta_kardex(sede_activa)):
            with open(ruta_kardex(sede_activa), "rb") as fk:
                c_e2.download_button("📁 Descargar Kardex Completo (Con Ceros)", data=fk, file_name=f"kardex_completo_{normalizar(sede_activa)}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.divider()
        st.markdown("### 📑 Custodia de Actas de Recepción Firmadas")
        facs = [f for f in df_k["Factura_Remision"].dropna().unique() if str(f).strip() not in ["N/A","nan",""]]
        if facs:
            sel_fac = st.selectbox("Seleccione Factura:", facs, key="sb_fac_cust")
            sub_f = df_k[df_k["Factura_Remision"] == sel_fac]
            c_g, c_f = st.columns(2)
            with c_g:
                r_gen = os.path.join(DIR_ACTAS_GEN, f"Acta_Recepcion_{normalizar(sede_activa)}_{normalizar(sel_fac)}.pdf")
                if os.path.exists(r_gen):
                    with open(r_gen, "rb") as fg: 
                        st.download_button("📥 Descargar Acta Oficial Emitida (PDF)", data=fg, file_name=os.path.basename(r_gen), mime="application/pdf")
                else:
                    if st.button("📄 Generar Acta Oficial PDF Ahora"):
                        generar_pdf_recepcion({'sede': sede_activa, 'proveedor': str(sub_f.iloc[0].get("Proveedor","PROVEEDOR")), 'factura': sel_fac, 'categoria': cat_k, 'fecha': str(sub_f.iloc[0].get("Fecha Ingreso", date.today().strftime("%Y-%m-%d"))), 'responsable': str(sub_f.iloc[0].get("Responsable Tecnico","Auxiliar")), 'cargo': str(sub_f.iloc[0].get("Cargo Responsable","Auxiliar"))}, sub_f)
                        st.rerun()
            with c_f:
                r_fir, n_fir = buscar_soporte(DIR_ACTAS_FIR, f"Acta_Firmada_{normalizar(sede_activa)}_{normalizar(sel_fac)}")
                if r_fir:
                    st.success(f"🟢 ACTA CUSTODIADA: `{n_fir}`")
                    with open(r_fir, "rb") as ff: 
                        st.download_button("📥 Descargar Acta Firmada", data=ff, file_name=n_fir)
                else: 
                    st.warning("🟡 Pendiente de adjuntar acta escaneada firmada.")
                up_fir = st.file_uploader(f"Subir soporte firmado para {sel_fac}:", type=["pdf","jpg","png"], key="up_fir_k")
                if up_fir and st.button("💾 Guardar Soporte Firmado"):
                    guardar_archivo(DIR_ACTAS_FIR, up_fir, f"Acta_Firmada_{normalizar(sede_activa)}_{normalizar(sel_fac)}")
                    st.success("Guardado.")
                    st.rerun()

# =============================================================
# SUBMÓDULO 3: SEMAFORIZACIÓN (FEFO)
# =============================================================
elif modulo == "Semaforización (FEFO)":
    st.markdown("#### **Semaforización y Rotación FEFO (First Expired, First Out)**")
    c_s, _ = st.columns([1.5, 2.5])
    sede_activa = c_s.selectbox("🏢 Sede a Auditar:", ["Sede Ibagué", "Sede Fusagasugá"], key="fefo_sede_activa")
    items_fefo = []
    for cat, (_, _, col_f) in COLS_K.items():
        df_c = cargar_k(sede_activa, cat)
        if not df_c.empty:
            for _, r in df_c.iterrows():
                nom = r.get("Nombre Comercial") or r.get("Nombre Dispositivo") or r.get("Nombre Insumo") or r.get("Nombre Reactivo") or "N/A"
                stxt, sval = semaforo(r.get(col_f))
                items_fefo.append({
                    "Categoría": cat, "Producto": nom, "Lote": r.get("Lote","N/A"), "Cantidad": r.get("Cantidad",0),
                    "Vencimiento": str(r.get(col_f,"N/A"))[:10], "Factura": r.get("Factura_Remision","N/A"), "Estado": stxt, "Meses": sval
                })
    if items_fefo:
        df_ff = pd.DataFrame(items_fefo).sort_values(by="Meses", ascending=True)
        venc = len(df_ff[df_ff["Estado"].str.contains("🔴")])
        aler = len(df_ff[df_ff["Estado"].str.contains("🟡")])
        opti = len(df_ff[df_ff["Estado"].str.contains("🟢")])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Ítems", len(df_ff))
        c2.metric("Críticos (≤ 3m)", venc, delta=f"-{venc}" if venc else "0", delta_color="inverse")
        c3.metric("Alerta (3-6m)", aler)
        c4.metric("Óptimos (> 6m)", opti)
        st.dataframe(df_ff[["Estado", "Factura", "Categoría", "Producto", "Lote", "Cantidad", "Vencimiento"]], use_container_width=True, hide_index=True)
    else: 
        st.info("No hay inventario en Kardex.")

# =============================================================
# SUBMÓDULO 4: DISPENSACIÓN Y CRUCE DE SALIDAS
# =============================================================
elif modulo == "Dispensación":
    st.markdown("#### **Dispensación de Insumos / Medicamentos a Pacientes**")
    c_s, _ = st.columns([1.5, 2.5])
    sede_activa = c_s.selectbox("🏢 Sede de Operación:", ["Sede Ibagué", "Sede Fusagasugá"], key="disp_sede_activa")
    d1, d2, d3 = st.tabs(["📂 Carga de Salidas (Manager Clinic / Excel)", "📑 Custodia Digital por N° de Acta (NRO_ES)", "📊 Consolidado de Insumos"])
    df_disp = cargar_disp(sede_activa)

    with d1:
        st.write("##### 📂 Carga de Entregas a Domicilio")
        up_sal = st.file_uploader("Subir reporte de salidas (ej: ADA.xlsx):", type=["xlsx", "xls"], key="up_sal_mgr")
        if up_sal:
            try:
                df_raw = pd.read_excel(up_sal).dropna(how="all", axis=0)
                cmap = {re.sub(r'\\s+', ' ', str(c).upper().strip()): c for c in df_raw.columns}
                c_act = smart_col(cmap, "NRO_ES", "NRO ES", "ACTA", "REMISION")
                c_doc = smart_col(cmap, "NIT", "DOCUMENTO", "CEDULA")
                c_pac = smart_col(cmap, "NOMBRE", "PACIENTE")
                c_prd = smart_col(cmap, "PRODUCTO", "INSUMO", "MEDICAMENTO")
                c_cnt = smart_col(cmap, "CANTIDAD", "CANT")
                c_fec = smart_col(cmap, "FECHA", "FEC")
                c_not = smart_col(cmap, "NOTA", "SERVICIO", "OBSERVACION")
                if c_prd and c_cnt:
                    df_sal = pd.DataFrame()
                    df_sal["Acta"] = df_raw[c_act].dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip() if c_act else "N/A"
                    df_sal["Documento"] = df_raw[c_doc].dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip() if c_doc else "N/A"
                    df_sal["Paciente"] = df_raw[c_pac].astype(str).str.strip() if c_pac else "PACIENTE"
                    df_sal["Horario"] = df_raw[c_not].astype(str).str.strip() if c_not else "N/A"
                    df_sal["Municipio"] = "IBAGUE" if "ibague" in sede_activa.lower() else "FUSAGASUGA"
                    df_sal["Producto"] = df_raw[c_prd].astype(str).str.strip()
                    df_sal["Cantidad"] = pd.to_numeric(df_raw[c_cnt], errors="coerce").fillna(0).astype(int)
                    df_sal["Fecha"] = pd.to_datetime(df_raw[c_fec], errors="coerce").dt.strftime("%Y-%m-%d").fillna(date.today().strftime("%Y-%m-%d")) if c_fec else date.today().strftime("%Y-%m-%d")
                    df_sal = df_sal[(df_sal["Producto"] != "") & (df_sal["Cantidad"] > 0)]
                    
                    actas_prev = set(df_disp["Acta_Numero"].dropna().astype(str).str.strip().unique()) - {"N/A", ""}
                    df_nuevas = df_sal[~df_sal["Acta"].isin(actas_prev)]
                    if len(df_sal) > len(df_nuevas):
                        st.warning(f"🔒 Se omitieron {df_sal['Acta'].nunique() - df_nuevas['Acta'].nunique()} actas ya registradas previamente.")
                    
                    if not df_nuevas.empty:
                        st.write(f"Pre-balance de stock para **{df_nuevas['Acta'].nunique()} Actas Nuevas** ({len(df_nuevas)} líneas):")
                        agrup = df_nuevas.groupby("Producto")["Cantidad"].sum().reset_index()
                        bal = []
                        for _, r in agrup.iterrows():
                            cat, col_n, col_f, knom, df_k_cur = buscar_prod_kardex(sede_activa, r["Producto"])
                            stk = df_k_cur[df_k_cur[col_n].astype(str).str.strip().str.upper() == str(knom).strip().upper()]["Cantidad"].sum() if cat else 0
                            defic = max(0, r["Cantidad"] - stk)
                            bal.append({"Producto": r["Producto"], "Stock Kardex": int(stk), "A Despachar": int(r["Cantidad"]), "Déficit": int(defic), "Estado": "🟢 Conforme" if defic==0 else f"🔴 Déficit (-{defic})"})
                        st.dataframe(pd.DataFrame(bal), use_container_width=True, hide_index=True)
                        
                        if st.button("🚀 Confirmar Descuento en Kardex y Registrar Salidas"):
                            k_dfs = {cat: cargar_k(sede_activa, cat) for cat in COLS_K.keys()}
                            nuevas_ent = []
                            prox_id = len(df_disp) + 1
                            for _, r_sal in df_nuevas.iterrows():
                                cat, col_n, col_f, knom, _ = buscar_prod_kardex(sede_activa, r_sal["Producto"])
                                desc = 0
                                defic = r_sal["Cantidad"]
                                lotes_u = []
                                if cat:
                                    tdf = k_dfs[cat]
                                    sub_k = tdf[tdf[col_n].astype(str).str.strip().str.upper() == str(knom).strip().upper()].copy()
                                    sub_k["c_num"] = pd.to_numeric(sub_k["Cantidad"], errors="coerce").fillna(0)
                                    sub_k = sub_k[sub_k["c_num"] > 0].sort_values(by=col_f, ascending=True)
                                    rem = r_sal["Cantidad"]
                                    for kidx, krow in sub_k.iterrows():
                                        disp_l = krow["c_num"]
                                        if disp_l >= rem:
                                            tdf.at[kidx, "Cantidad"] = int(disp_l - rem)
                                            desc += rem
                                            lotes_u.append(f"{krow['Lote']} ({rem})")
                                            rem = 0
                                            break
                                        else:
                                            tdf.at[kidx, "Cantidad"] = 0
                                            desc += disp_l
                                            lotes_u.append(f"{krow['Lote']} ({int(disp_l)})")
                                            rem -= disp_l
                                    defic = rem
                                nuevas_ent.append({
                                    "ID_Entrega": f"ENT-{prox_id:04d}", "Fecha_Entrega": r_sal["Fecha"], "Documento_Paciente": r_sal["Documento"],
                                    "Nombre_Paciente": r_sal["Paciente"], "Horario": r_sal["Horario"], "Municipio": r_sal["Municipio"],
                                    "Categoria": cat or "NO REGISTRADO", "Producto": r_sal["Producto"], "Cantidad_Entregada": r_sal["Cantidad"],
                                    "Cantidad_Descontada_Kardex": desc, "Deficit_Pendiente": defic, "Lotes_Descontados": ", ".join(lotes_u) or "Sin stock",
                                    "Acta_Numero": r_sal["Acta"], "Estado_Soporte": "🟡 Pendiente de Soporte", "Archivo_Soporte": "N/A"
                                })
                                prox_id += 1
                            for cat, kdf in k_dfs.items(): 
                                guardar_k(sede_activa, cat, kdf)
                            guardar_disp(sede_activa, pd.concat([df_disp, pd.DataFrame(nuevas_ent)], ignore_index=True))
                            st.success("Salidas descontadas correctamente.")
                            st.rerun()
            except Exception as e: 
                st.error(f"Error: {e}")

    with d2:
        df_disp = cargar_disp(sede_activa)
        df_res_act = resumir_actas(df_disp)
        if not df_res_act.empty:
            c1, c2, c3 = st.columns(3)
            tot_a = len(df_res_act)
            fir_a = len(df_res_act[df_res_act["Estado_Soporte"] == "🟢 Custodiada / Firmada"])
            c1.metric("Total Actas (NRO_ES)", tot_a)
            c2.metric("🟢 Custodiadas", fir_a)
            c3.metric("🟡 Pendientes", tot_a - fir_a)
            st.dataframe(df_res_act, use_container_width=True, hide_index=True)
            st.divider()
            sel_act = st.selectbox("Seleccione N° Acta para custodiar soporte:", df_res_act["Acta_Numero"].tolist(), key="sb_act_cust")
            sub_act = df_disp[df_disp["Acta_Numero"] == sel_act]
            ca1, ca2 = st.columns([1.5, 2])
            with ca1:
                st.info(f"📋 **Acta:** `{sel_act}` | 👤 **Paciente:** {sub_act.iloc[0]['Nombre_Paciente']}\n\n🪪 **Cédula:** {sub_act.iloc[0]['Documento_Paciente']} | 📦 **Insumos:** {len(sub_act)} ({sub_act['Cantidad_Entregada'].sum()} und)")
            with ca2:
                r_sop, n_sop = buscar_soporte(DIR_DISP_FIR, f"Acta_Paciente_{normalizar(sede_activa)}_{normalizar(sel_act)}")
                if r_sop:
                    st.success(f"🟢 CUSTODIADA: `{n_sop}`")
                    with open(r_sop, "rb") as fs: 
                        st.download_button("📥 Descargar Acta Firmada", data=fs, file_name=n_sop)
                else: 
                    st.warning("🟡 Pendiente de adjuntar escaneado.")
                up_sop = st.file_uploader(f"Subir soporte para Acta {sel_act}:", type=["pdf","jpg","png"], key="up_sop_act")
                if up_sop and st.button(f"💾 Guardar Soporte Acta {sel_act}"):
                    nom_g = guardar_archivo(DIR_DISP_FIR, up_sop, f"Acta_Paciente_{normalizar(sede_activa)}_{normalizar(sel_act)}")
                    mask = df_disp["Acta_Numero"] == sel_act
                    df_disp.loc[mask, "Estado_Soporte"] = "🟢 Custodiada / Firmada"
                    df_disp.loc[mask, "Archivo_Soporte"] = nom_g
                    guardar_disp(sede_activa, df_disp)
                    st.success("Custodiada correctamente.")
                    st.rerun()
            st.write("##### Insumos amparados en esta Acta:")
            st.dataframe(sub_act[["Producto", "Cantidad_Entregada", "Cantidad_Descontada_Kardex", "Deficit_Pendiente", "Lotes_Descontados", "Estado_Soporte"]], use_container_width=True, hide_index=True)
        else: 
            st.info("No hay salidas registradas.")

    with d3:
        if not df_disp.empty:
            res_ins = df_disp.groupby(["Producto", "Categoria"]).agg(Total_Entregado=("Cantidad_Entregada", "sum"), Descontado=("Cantidad_Descontada_Kardex", "sum"), Deficit=("Deficit_Pendiente", "sum"), Lineas=("ID_Entrega", "count")).reset_index()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Unidades", int(res_ins["Total_Entregado"].sum()))
            c2.metric("Descontado Kardex", int(res_ins["Descontado"].sum()))
            def_t = int(res_ins["Deficit"].sum())
            c3.metric("Déficit Total", def_t, delta=f"-{def_t}" if def_t else "0", delta_color="inverse")
            c4.metric("Insumos Distintos", len(res_ins))
            st.dataframe(res_ins, use_container_width=True, hide_index=True)
            out_d = io.BytesIO()
            with pd.ExcelWriter(out_d, engine="openpyxl") as w:
                res_ins.to_excel(w, index=False, sheet_name="Totales")
                df_disp.to_excel(w, index=False, sheet_name="Detalle")
            st.download_button("📥 Descargar Reporte Consolidado Excel", data=out_d.getvalue(), file_name=f"reporte_salidas_{normalizar(sede_activa)}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# =============================================================
# SUBMÓDULO 5: CONTEO CÍCLICO (AUDITORÍA CIEGA)
# =============================================================
elif modulo == "Conteo Cíclico":
    st.markdown("#### **Auditoría de Farmacia y Conteo Cíclico Físico**")
    st.caption("Conteo ciego (sin ver saldo del sistema), cálculo de ERI y emisión de Acta Oficial sin alteración de Kardex.")
    c_s, c_c = st.columns([1.5, 2.5])
    sede_activa = c_s.selectbox("🏢 Sede a Auditar:", ["Sede Ibagué", "Sede Fusagasugá"], key="cnt_sede_activa")
    prox_c = prox_consecutivo_conteo(sede_activa)
    c_c.info(f"📋 **Consecutivo de Auditoría en Curso:** `{prox_c}`")
    cc1, cc2 = st.tabs(["📝 Nuevo Conteo Ciego (Auditoría)", "📑 Historial de Actas y Métricas"])

    with cc1:
        c1, c2, c3 = st.columns([1.5, 1.5, 1.0])
        aux_c = c1.text_input("Auxiliar que realizó el conteo (*):", value="Andrea Gómez")
        aud_c = c2.text_input("Auditor / Responsable Técnico (*):", value="Harol Montoya")
        fec_c = c3.date_input("Fecha Auditoría:", datetime.now())
        up_cnt = st.file_uploader("Subir muestra de inventario desde Manager Clinic:", type=["xlsx", "xls"], key="up_cnt_m")
        if up_cnt:
            try:
                df_raw = pd.read_excel(up_cnt).dropna(how="all", axis=0)
                cmap = {re.sub(r'\\s+', ' ', str(c).upper().strip()): c for c in df_raw.columns}
                c_cod = smart_col(cmap, "CODIGO", "COD", "ID")
                c_prd = smart_col(cmap, "PRODUCTO", "DESCRIPCION", "NOMBRE", "INSUMO", "MEDICAMENTO")
                c_lot = smart_col(cmap, "LOTE", "SERIE")
                c_cnt = smart_col(cmap, "CANTIDAD", "SALDO", "EXISTENCIA", "STOCK")
                if c_prd and c_cnt:
                    df_m = pd.DataFrame()
                    df_m["Codigo"] = df_raw[c_cod].dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip() if c_cod else "N/A"
                    df_m["Producto"] = df_raw[c_prd].astype(str).str.strip()
                    df_m["Lote"] = df_raw[c_lot].dropna().astype(str).str.strip() if c_lot else "NA"
                    df_m["Cantidad_Sistema"] = pd.to_numeric(df_raw[c_cnt], errors="coerce").fillna(0).astype(int)
                    df_m = df_m[df_m["Producto"] != ""]
                    
                    st.success(f"📦 Muestra cargada: **{len(df_m)} insumos**. Ingrese la cantidad contada en cada casilla:")
                    st.info("🔒 **Conteo Ciego:** La cantidad en sistema está oculta para evitar sesgos.")
                    
                    with st.form("form_conteo_ciego"):
                        cnt_vals, obs_vals = [], []
                        for idx_p, row_p in df_m.iterrows():
                            st.markdown(f"###### **#{idx_p+1}: {row_p['Producto']}**")
                            c_i, c_n, c_o = st.columns([2.0, 1.2, 2.0])
                            c_i.caption(f"**Código:** `{row_p['Codigo']}` | **Lote:** `{row_p['Lote']}`")
                            cnt_vals.append(c_n.number_input("Cantidad Contada (*):", min_value=0, step=1, value=0, key=f"c_in_{idx_p}"))
                            obs_vals.append(c_o.text_input("Observación física:", value="Sin novedad", key=f"o_in_{idx_p}"))
                            st.write("---")
                        
                        if st.form_submit_button("📊 Finalizar Conteo, Revelar Balance y Emitir Acta PDF"):
                            if not aux_c.strip() or not aud_c.strip(): 
                                st.error("Diligencie Auxiliar y Auditor.")
                            else:
                                df_eval = df_m.copy()
                                df_eval["Item"] = range(1, len(df_eval)+1)
                                df_eval["Conteo_Fisico"] = cnt_vals
                                df_eval["Observaciones"] = obs_vals
                                df_eval["Diferencia"] = df_eval["Conteo_Fisico"] - df_eval["Cantidad_Sistema"]
                                df_eval["Estado"] = df_eval["Diferencia"].apply(lambda d: "🟢 Conforme" if d==0 else (f"🔴 Faltante ({abs(d)})" if d<0 else f"🔵 Sobrante (+{d})"))
                                tot = len(df_eval)
                                conf = len(df_eval[df_eval["Diferencia"]==0])
                                disc = tot - conf
                                eri = round((conf/tot)*100, 1) if tot>0 else 0.0
                                
                                d_aud = {"consecutivo": prox_c, "sede": sede_activa, "fecha": fec_c.strftime("%Y-%m-%d"), "auxiliar": aux_c.strip(), "auditor": aud_c.strip(), "eri": eri, "discrepancias": disc}
                                pdf_b, nom_p = generar_pdf_conteo(d_aud, df_eval)
                                
                                d_res = pd.DataFrame([{"Consecutivo": prox_c, "Fecha": d_aud["fecha"], "Sede": sede_activa, "Auxiliar": d_aud["auxiliar"], "Auditor": d_aud["auditor"], "Total_Items": tot, "Items_Conformes": conf, "Items_Discrepancias": disc, "Porcentaje_ERI": eri, "Archivo_Acta_PDF": nom_p}])
                                d_det = df_eval[["Item", "Codigo", "Producto", "Lote", "Cantidad_Sistema", "Conteo_Fisico", "Diferencia", "Estado", "Observaciones"]].copy()
                                d_det["Consecutivo"] = prox_c
                                guardar_conteo(sede_activa, d_res, d_det)
                                st.session_state["pdf_cnt"] = (pdf_b, nom_p)
                                st.success(f"Auditoría {prox_c} completada y archivada.")
                                st.rerun()
            except Exception as e: 
                st.error(f"Error: {e}")
        if "pdf_cnt" in st.session_state:
            st.download_button(f"📥 Descargar Acta Conteo PDF ({st.session_state['pdf_cnt'][1]})", data=st.session_state["pdf_cnt"][0], file_name=st.session_state["pdf_cnt"][1], mime="application/pdf")

    with cc2:
        h_res, h_det = cargar_conteos(sede_activa)
        if not h_res.empty:
            st.dataframe(h_res, use_container_width=True, hide_index=True)
            sel_c = st.selectbox("Seleccione Auditoría a consultar:", h_res["Consecutivo"].tolist(), key="sb_c_hist")
            sub_d = h_det[h_det["Consecutivo"] == sel_c]
            r_act = os.path.join(DIR_CONTEOS_PDF, f"Acta_Conteo_{normalizar(sede_activa)}_{sel_c}.pdf")
            if os.path.exists(r_act):
                with open(r_act, "rb") as fa: 
                    st.download_button("📥 Descargar Acta PDF", data=fa, file_name=os.path.basename(r_act), mime="application/pdf")
            st.write(f"##### Detalle de Hallazgos ({sel_c}):")
            st.dataframe(sub_d[["Item", "Codigo", "Producto", "Lote", "Cantidad_Sistema", "Conteo_Fisico", "Diferencia", "Estado", "Observaciones"]], use_container_width=True, hide_index=True)
        else: 
            st.info("No hay auditorías registradas.")

# =============================================================
# SUBMÓDULO 6: ARCHIVO DE DEVOLUCIONES Y RESPEL
# =============================================================
elif modulo == "Devoluciones / RESPEL":
    st.markdown("#### **Archivo Digital de Devoluciones, Bajas y Manifiestos RESPEL**")
    c_s, _ = st.columns([1.5, 2.5])
    sede_activa = c_s.selectbox("🏢 Sede de Custodia:", ["Sede Ibagué", "Sede Fusagasugá"], key="resp_sede_activa")
    r1, r2 = st.tabs(["📤 Cargar y Radicar Documento", "📑 Archivo y Consulta de Soportes"])
    df_resp = cargar_respel(sede_activa)

    with r1:
        with st.form("form_respel"):
            c1, c2 = st.columns(2)
            tip_d = c1.selectbox("Tipo de Documento (*):", ["Acta de Devolución a Proveedor", "Acta de Baja Técnica Interna (Averías / Caducados)", "Manifiesto de Disposición Final RESPEL (Gestor Ambiental)", "Certificado de Destrucción / Tratamiento Fármacos", "Otro"])
            nro_d = c2.text_input("N° Acta / Manifiesto (*):", placeholder="Ej: MAN-2026-0812")
            c3, c4 = st.columns(2)
            ter_d = c3.text_input("Proveedor o Empresa Gestora (*):", placeholder="Ej: ECOENTORNO / INSUMEDICAL")
            fec_d = c4.date_input("Fecha Documento:", datetime.now())
            c5, c6 = st.columns(2)
            mot_d = c5.selectbox("Motivo:", ["Vencimiento / Caducidad", "Avería física / Rotura", "Pérdida cadena de frío", "Alerta INVIMA", "Disposición final programada", "Error despacho", "Otro"])
            res_d = c6.text_input("Responsable (*):", value="Harol Montoya")
            obs_d = st.text_area("Descripción / Observaciones:")
            up_doc = st.file_uploader("Adjuntar archivo escaneado (PDF, JPG, PNG) (*):", type=["pdf","jpg","png"], key="up_resp_f")
            
            if st.form_submit_button("💾 Guardar y Custodiar en Archivo Digital"):
                if not nro_d.strip() or not ter_d.strip() or not res_d.strip() or not up_doc:
                    st.error("Diligencie N° Documento, Tercero, Responsable y adjunte el archivo.")
                else:
                    nom_g = guardar_archivo(DIR_RESPEL_ARCH, up_doc, f"{normalizar(tip_d)}_{normalizar(sede_activa)}_{normalizar(nro_d)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    row_r = {
                        "ID_Archivo": f"DOC-{len(df_resp)+1:04d}", "Fecha_Cargue": date.today().strftime("%Y-%m-%d"), "Fecha_Documento": fec_d.strftime("%Y-%m-%d"),
                        "Sede": sede_activa, "Tipo_Documento": tip_d, "Numero_Acta_Manifiesto": nro_d.strip().upper(), "Entidad_Tercero": ter_d.strip().upper(),
                        "Motivo_Detalle": f"{mot_d} - {obs_d.strip()}" if obs_d.strip() else mot_d, "Responsable": res_d.strip(), "Nombre_Archivo": nom_g
                    }
                    guardar_respel(sede_activa, pd.concat([df_resp, pd.DataFrame([row_r])], ignore_index=True))
                    st.success("Documento radicado y custodiado con éxito.")
                    st.rerun()

    with r2:
        if not df_resp.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Documentos", len(df_resp))
            c2.metric("Devoluciones", len(df_resp[df_resp["Tipo_Documento"].str.contains("Devolución", case=False)]))
            c3.metric("Bajas Técnicas", len(df_resp[df_resp["Tipo_Documento"].str.contains("Baja", case=False)]))
            c4.metric("Manifiestos RESPEL", len(df_resp[df_resp["Tipo_Documento"].str.contains("RESPEL|Destrucción", case=False)]))
            st.dataframe(df_resp[["ID_Archivo", "Fecha_Documento", "Tipo_Documento", "Numero_Acta_Manifiesto", "Entidad_Tercero", "Motivo_Detalle", "Responsable"]], use_container_width=True, hide_index=True)
            st.divider()
            sel_r_idx = st.selectbox("Seleccione documento para descargar soporte:", range(len(df_resp)), format_func=lambda i: f"{df_resp.iloc[i]['ID_Archivo']} | {df_resp.iloc[i]['Numero_Acta_Manifiesto']} ({df_resp.iloc[i]['Entidad_Tercero']})")
            doc_sel = df_resp.iloc[sel_r_idx]
            r_doc = os.path.join(DIR_RESPEL_ARCH, str(doc_sel["Nombre_Archivo"]))
            if os.path.exists(r_doc):
                with open(r_doc, "rb") as fr: 
                    st.download_button(f"📥 Descargar Soporte ({doc_sel['Nombre_Archivo']})", data=fr, file_name=str(doc_sel['Nombre_Archivo']))
            out_r = io.BytesIO()
            with pd.ExcelWriter(out_r, engine="openpyxl") as w: 
                df_resp.to_excel(w, index=False, sheet_name="RESPEL")
            st.download_button("📥 Descargar Planilla de Control RESPEL (Excel)", data=out_r.getvalue(), file_name=f"control_respel_{normalizar(sede_activa)}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else: 
            st.info("No hay documentos archivados.")