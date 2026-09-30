import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import os, json, re, io, base64
from datetime import datetime, date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# -------------------------------------------------------------
# 1. CONFIGURACIÓN GENERAL Y LOGOTIPO CORPORATIVO ASAD IPS
# -------------------------------------------------------------
st.set_page_config(
    page_title="ASAD IPS - Servicio Farmacéutico",
    page_icon="💊",
    layout="wide"
)

# LOGO OFICIAL EXTRAÍDO DEL MANUAL DE MARCA ASAD IPS (BASE64 INTEGRADO)
LOGO_B64 = (
    "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"
)

# Generación automática del archivo logo_asad.png en disco para Streamlit y ReportLab (PDFs)
if not os.path.exists("logo_asad.png"):
    try:
        with open("logo_asad.png", "wb") as _f_l:
            _f_l.write(base64.b64decode(LOGO_B64))
    except Exception:
        pass

# ESTILOS CORPORATIVOS SEGÚN MANUAL DE MARCA ASAD IPS (VERDANA + PALETA)
st.markdown("""
<style>
    /* Tipografía Corporativa Oficial: Verdana (solo a textos seguros para no romper iconos) */
    html, body, [class*="st-emotion-cache"], .stApp {
        font-family: 'Verdana', sans-serif;
    }
    p, label, input, textarea, select {
        font-family: 'Verdana', sans-serif !important;
    }
    
    /* Protección estricta de fuentes de iconos nativos de Streamlit */
    [data-testid="stIconMaterial"], 
    .material-symbols-rounded, 
    .material-symbols-outlined,
    [class*="icon"],
    span[data-testid="stExpanderToggleIcon"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }

    /* Encabezados Institucionales */
    h1, h2, h3 {
        color: #3855a0 !important;
        font-family: 'Verdana', sans-serif !important;
        font-weight: 700 !important;
    }
    h4, h5, h6 {
        color: #211915 !important;
        font-family: 'Verdana', sans-serif !important;
    }

    /* Botones con Azul Corporativo ASAD (#3855a0) y hover Celeste (#009eda) */
    .stButton > button {
        background-color: #3855a0 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-family: 'Verdana', sans-serif !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        background-color: #009eda !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0, 158, 218, 0.4) !important;
    }

    /* Pestañas (Tabs) con subrayado en Azul Corporativo */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #3855a0 !important;
        border-bottom-color: #3855a0 !important;
        font-weight: bold !important;
    }

    /* Métricas destacadas */
    div[data-testid="stMetricValue"] {
        color: #3855a0 !important;
        font-weight: 700 !important;
    }
    
    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

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
    st_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=9.5, alignment=1, textColor=colors.HexColor('#3855a0'))
    st_h2 = ParagraphStyle('H2', fontName='Helvetica', fontSize=7.5, alignment=1, textColor=colors.HexColor('#333333'))
    
    logo_flow = RLImage("logo_asad.png", width=130, height=49) if os.path.exists("logo_asad.png") else Paragraph("<b>ASAD IPS</b>", st_h1)
    elems = [
        Table([[logo_flow,
                Paragraph("<b>ASAD ASISTENCIA EN SALUD DOMICILIARIA SAS</b><br/><font size=6.5 color='#211915'>HABILITACIÓN SERVICIO FARMACÉUTICO - RESOLUCIÓN 3100 DE 2019</font><br/><b>ACTA INSTITUCIONAL DE RECEPCIÓN TÉCNICA DE INSUMOS</b><br/><font size=6.5 color='#211915'>Proceso: Gestión de Recursos Físicos / Calidad Asistencial</font>", st_h1),
                Paragraph(f"<b>CÓDIGO:</b> GCA-DC-FT-04<br/><b>VERSIÓN:</b> 002<br/><b>FECHA:</b> {datos['fecha']}", st_h2)]], colWidths=[150, 410, 180],
              style=[('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3855a0')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#3855a0')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,0), 'CENTER'), ('PADDING', (0,0), (-1,-1), 3)]),
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
                       style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#3855a0')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3855a0')),
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

def procesar_archivo_cargue_masivo(archivo, categoria, factura, prov, resp, cargo):
    xls = pd.ExcelFile(archivo)
    sheet_a_leer = xls.sheet_names[0]
    for s in xls.sheet_names:
        s_norm = s.upper()
        if ("MEDICAMENTOS" in s_norm and categoria == "Medicamentos") or \
           ("DISPOSITIVOS" in s_norm and categoria == "Dispositivos Médicos") or \
           ("INSUMOS" in s_norm and categoria == "Insumos") or \
           ("REACTIVOS" in s_norm and categoria == "Reactivos"):
            sheet_a_leer = s
            break

    df_raw = pd.read_excel(archivo, sheet_name=sheet_a_leer, header=None)
    h_idx = 0
    for idx, row in df_raw.head(25).iterrows():
        row_txt = " ".join([str(v).upper() for v in row.values if pd.notna(v)])
        if "LOTE" in row_txt and ("NOMBRE" in row_txt or "PROVEEDOR" in row_txt or "ITEM" in row_txt or "N°" in row_txt):
            h_idx = idx
            break

    df_in = pd.read_excel(archivo, sheet_name=sheet_a_leer, header=h_idx)
    df_in = df_in.dropna(how="all", axis=0).dropna(how="all", axis=1)

    col_map = {re.sub(r'\s+', ' ', str(c).upper().strip()): c for c in df_in.columns}

    def find_col(*keywords):
        for k in keywords:
            for norm, orig in col_map.items():
                if k in norm:
                    return orig
        return None

    df_out = pd.DataFrame()
    c_lab = find_col("LABORATORIO")
    c_lote = find_col("LOTE")
    c_invima = find_col("REGISTRO SANITARIO", "REGISTRO INVIMA", "INVIMA")
    c_est_invima = find_col("ESTADO DE REGISTRO", "ESTADO REGISTRO", "ESTADO INVIMA")
    c_calidad = find_col("ANALISIS DE CALIDAD", "CALIDAD")
    c_defecto = find_col("DEFECTO CRITICO", "DEFECTO")
    c_cant = find_col("CANTIDAD")
    c_f_venc = find_col("CADUCIDAD", "FECHA DE CADUCIDAD", "FECHA VENCIMIENTO", "VENCIMIENTO")
    c_temp_t = find_col("TEMP", "TRANSPORTE")

    df_out["Factura_Remision"] = factura.strip()
    df_out["Proveedor"] = prov.strip() or "PROVEEDOR GENERAL"
    df_out["Fecha Ingreso"] = date.today().strftime("%Y-%m-%d")
    df_out["Laboratorio"] = df_in[c_lab].astype(str) if c_lab else "N/A"
    df_out["Lote"] = df_in[c_lote].astype(str) if c_lote else "N/A"
    df_out["Registro INVIMA"] = df_in[c_invima].astype(str) if c_invima else "N/A"
    df_out["Estado INVIMA"] = df_in[c_est_invima].astype(str) if c_est_invima else "VIGENTE"
    df_out["Analisis Calidad"] = df_in[c_calidad].astype(str) if c_calidad else "OK (Conforme)"
    df_out["Defecto Critico"] = df_in[c_defecto].astype(str) if c_defecto else "NO APLICA"
    df_out["Cantidad"] = pd.to_numeric(df_in[c_cant], errors="coerce").fillna(0).astype(int) if c_cant else 0
    df_out["Responsable Tecnico"] = resp.strip()
    df_out["Cargo Responsable"] = cargo

    if categoria == "Medicamentos":
        c_nom = find_col("NOMBRE COMERCIAL", "NOMBRE")
        c_forma = find_col("FORMA FARMACEUTICA", "FORMA")
        c_conc = find_col("CONCENTRACION")
        c_pres = find_col("PRESENTACION")
        c_via = find_col("ADMINISTRACION", "VIA")
        c_und = find_col("UNIDAD DE MEDIDA", "UNIDAD")
        c_princ = find_col("PRINCIPIO ACTIVO", "PRINCIPIO")

        df_out["Nombre Comercial"] = df_in[c_nom].astype(str) if c_nom else "N/A"
        df_out["Principio Activo"] = df_in[c_princ].astype(str) if c_princ else "N/A"
        df_out["Forma Farmaceutica"] = df_in[c_forma].astype(str) if c_forma else "N/A"
        df_out["Concentracion"] = df_in[c_conc].astype(str) if c_conc else "N/A"
        df_out["Presentacion"] = df_in[c_pres].astype(str) if c_pres else "N/A"
        df_out["Via Administracion"] = df_in[c_via].astype(str) if c_via else "N/A"
        df_out["Unidad Medida"] = df_in[c_und].astype(str) if c_und else "N/A"
        df_out["Temp Transporte"] = df_in[c_temp_t].astype(str) if c_temp_t else "Ambiente (15-25°C)"
        df_out["Fecha Caducidad"] = df_in[c_f_venc].astype(str).str[:10] if c_f_venc else "N/A"
        df_out["Semaforizacion"] = df_out["Fecha Caducidad"].apply(lambda f: semaforo(f)[0])

    elif categoria in ["Dispositivos Médicos", "Insumos"]:
        col_nom_dest = "Nombre Dispositivo" if categoria == "Dispositivos Médicos" else "Nombre Insumo"
        col_pres_dest = "Presentacion Comercial" if categoria == "Dispositivos Médicos" else "Presentacion"
        c_nom = find_col("NOMBRE DEL DISPOSITIVO", "DESCRIPCION", "NOMBRE")
        c_marca = find_col("MARCA DEL DISPOSITIVO", "MARCA")
        c_serie = find_col("SERIE")
        c_pres = find_col("PRESENTACION COMERCIAL", "PRESENTACION")
        c_riesgo = find_col("CLASIFICACION DE RIESGO", "RIESGO")

        df_out[col_nom_dest] = df_in[c_nom].astype(str) if c_nom else "N/A"
        df_out["Marca"] = df_in[c_marca].astype(str) if c_marca else "N/A"
        df_out["Serie"] = df_in[c_serie].astype(str) if c_serie else "NA"
        df_out[col_pres_dest] = df_in[c_pres].astype(str) if c_pres else "N/A"
        df_out["Clasificacion Riesgo"] = df_in[c_riesgo].astype(str) if c_riesgo else "NA"
        df_out["Fecha Caducidad"] = df_in[c_f_venc].astype(str).str[:10] if c_f_venc else "N/A"
        df_out["Semaforizacion"] = df_out["Fecha Caducidad"].apply(lambda f: semaforo(f)[0])

    else:
        c_nom = find_col("NOMBRE DEL REACTIVO", "NOMBRE")
        c_marca = find_col("MARCA DEL REACTIVO", "MARCA")
        c_pres = find_col("PRESENTACION")
        c_riesgo = find_col("CLASIFICACION DE RIESGO", "RIESGO")

        df_out["Nombre Reactivo"] = df_in[c_nom].astype(str) if c_nom else "N/A"
        df_out["Marca"] = df_in[c_marca].astype(str) if c_marca else "N/A"
        df_out["Presentacion"] = df_in[c_pres].astype(str) if c_pres else "N/A"
        df_out["Clasificacion Riesgo"] = df_in[c_riesgo].astype(str) if c_riesgo else "NA"
        df_out["Temp Transporte"] = df_in[c_temp_t].astype(str) if c_temp_t else "2°C - 8°C"
        df_out["Fecha Vencimiento"] = df_in[c_f_venc].astype(str).str[:10] if c_f_venc else "N/A"
        df_out["Semaforizacion"] = df_out["Fecha Vencimiento"].apply(lambda f: semaforo(f)[0])

    col_verif = "Nombre Comercial" if categoria == "Medicamentos" else ("Nombre Dispositivo" if categoria == "Dispositivos Médicos" else ("Nombre Insumo" if categoria == "Insumos" else "Nombre Reactivo"))
    df_out = df_out[df_out[col_verif].notna() & (df_out[col_verif] != "N/A") & (df_out[col_verif] != "") & (df_out[col_verif] != "nan")]
    df_out["Item"] = range(1, len(df_out) + 1)
    
    _, cols_maestras, _ = COLS_K[categoria]
    for cm in cols_maestras:
        if cm not in df_out.columns:
            df_out[cm] = "N/A"
            
    return df_out[cols_maestras]

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
    st_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=9, alignment=1, textColor=colors.HexColor('#3855a0'), leading=12)
    st_h2 = ParagraphStyle('H2', fontName='Helvetica', fontSize=7.5, alignment=1, textColor=colors.HexColor('#211915'), leading=10)
    
    logo_flow = RLImage("logo_asad.png", width=130, height=49) if os.path.exists("logo_asad.png") else Paragraph("<b>ASAD IPS</b>", st_h1)
    
    elems = [
        Table([[logo_flow,
                Paragraph("<b>ASAD ASISTENCIA EN SALUD DOMICILIARIA SAS</b><br/><font size=6.5 color='#211915'>HABILITACIÓN SERVICIO FARMACÉUTICO - RESOLUCIÓN 3100 DE 2019</font><br/><b>ACTA INSTITUCIONAL DE AUDITORÍA Y CONTEO CÍCLICO FÍSICO</b><br/><font size=6.5 color='#211915'>Proceso: Gestión de Recursos Físicos / Control y Custodia de Farmacia</font>", st_h1),
                Paragraph(f"<b>CÓDIGO:</b> GCA-DC-FT-08<br/><b>VERSIÓN:</b> 001<br/><b>CONSECUTIVO:</b> {datos['consecutivo']}", st_h2)]], colWidths=[150, 410, 180],
              style=[('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3855a0')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#3855a0')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,0), 'CENTER'), ('PADDING', (0,0), (-1,-1), 3)]),
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
                       style=[('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#3855a0')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3855a0')),
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
    if os.path.exists("logo_asad.png"):
        st.image("logo_asad.png", use_container_width=True)
    else:
        st.markdown("### 🏥 **ASAD IPS**")
    st.markdown("### **Servicio Farmacéutico**")
    st.caption("Macroproceso: Recursos Físicos")
    st.caption("*Su salud, nuestra salud*")
    st.markdown("---")

    modulo = option_menu(
        menu_title=None,
        options=["Factores Ambientales", "Recepción y Kardex", "Semaforización (FEFO)", "Dispensación", "Conteo Cíclico", "Devoluciones / RESPEL"],
        icons=["thermometer-half", "box-seam", "traffic-light", "bag-check", "clipboard-check", "trash"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"font-size": "15px", "color": "#009eda"},
            "nav-link": {
                "font-size": "13.5px", "text-align": "left", "margin": "2px 0px",
                "padding": "10px 14px", "border-bottom": "1px solid #edf2f7",
                "border-radius": "6px", "color": "#211915", "--hover-color": "#e0f2fe",
                "font-family": "Verdana, sans-serif"
            },
            "nav-link-selected": {"background-color": "#3855a0", "color": "#ffffff", "font-weight": "600"}
        }
    )
    st.markdown("---")
    st.caption("Sistema de Aseguramiento de Calidad\nResolución 3100 de 2019")

cfg = cargar_cfg()

# =============================================================
# SUBMÓDULO 1: FACTORES AMBIENTALES
# =============================================================
if modulo == "Factores Ambientales":
    st.markdown("## 🌡️ Control de Temperatura y Humedad")
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
                        st.warning("⚠️️ Humedad fuera de rango normativo (50%-70%).")
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
    st.markdown("## 📦 Recepción Técnica y Kardex Institucional")
    c_s, c_k = st.columns([1.5, 2.0])
    sede_activa = c_s.selectbox("🏢 Sede Operativa:", ["Sede Ibagué", "Sede Fusagasugá"], key="rec_sede_activa")
    cat_k = c_k.selectbox("📦 Categoría:", list(COLS_K.keys()), key="rk_cat")
    k1, k2, k3 = st.tabs(["📥 Registro Individual", "📂 Cargue Masivo con Acta PDF", "📋 Kardex Activo e Historial de Actas"])

    with k1:
        df_k = cargar_k(sede_activa, cat_k)
        prox_item = len(df_k) + 1

        with st.form("form_recep_ind"):
            st.write(f"##### Recepción Técnica: **{cat_k}** (Ítem #{prox_item})")
            
            st.markdown("###### **1. Trazabilidad de Compra y Proveedor**")
            f1_c1, f1_c2, f1_c3 = st.columns(3)
            factura_rem = f1_c1.text_input("N° de Factura o Remisión Comercial (*):")
            proveedor = f1_c2.text_input("Nombre del Proveedor:")
            fecha_ingreso = f1_c3.date_input("Fecha de Ingreso / Recepción:", datetime.now())

            st.markdown("###### **2. Especificaciones Técnicas del Producto**")
            if cat_k == "Medicamentos":
                f2_c1, f2_c2, f2_c3 = st.columns(3)
                nombre_prod = f2_c1.text_input("Nombre Comercial (*):")
                principio_activo = f2_c2.text_input("Principio Activo (DCI):")
                forma_farm = f2_c3.text_input("Forma Farmacéutica (ej: Solución inyectable, Ungüento):")

                f3_c1, f3_c2, f3_c3 = st.columns(3)
                concentracion = f3_c1.text_input("Concentración (ej: 0.9%, 2%, 500 mg):")
                presentacion = f3_c2.text_input("Presentación (ej: Bolsa, Ampolla, Tubo):")
                via_adm = f3_c3.selectbox("Vía de Administración:", ["Tópica", "Inyectable", "Parenteral", "Oral", "Oftálmica", "Otra"])

                f4_c1, f4_c2, f4_c3 = st.columns(3)
                unidad_medida = f4_c1.text_input("Unidad de Medida (ML, MG, UND):")
                laboratorio = f4_c2.text_input("Laboratorio Fabricante:")
                lote = f4_c3.text_input("Lote de Fabricación (*):")

                temp_transporte = st.text_input("Temperatura de Transporte/Recepción (°C):", value="Ambiente (15-25°C)")

            elif cat_k in ["Dispositivos Médicos", "Insumos"]:
                col_nom_label = "Nombre Dispositivo (*):" if cat_k == "Dispositivos Médicos" else "Nombre Insumo (*):"
                f2_c1, f2_c2 = st.columns([2, 1])
                nombre_prod = f2_c1.text_input(col_nom_label, placeholder="ej: Guantes nitrilo Talla S")
                marca_prod = f2_c2.text_input("Marca Comercial:")

                f3_c1, f3_c2, f3_c3 = st.columns(3)
                laboratorio = f3_c1.text_input("Fabricante:")
                serie = f3_c2.text_input("Serie (si aplica, o NA):", value="NA")
                lote = f3_c3.text_input("Lote de Fabricación (*):")

                f4_c1, f4_c2 = st.columns(2)
                presentacion = f4_c1.text_input("Presentación Comercial (ej: Caja x 100, Paquete x 20, Unidad):")
                clasif_riesgo = f4_c2.selectbox("Clasificación de Riesgo:", ["NA", "I", "IIa", "IIb", "III"])

            else:
                f2_c1, f2_c2, f2_c3 = st.columns(3)
                nombre_prod = f2_c1.text_input("Nombre del Reactivo (*):")
                marca_prod = f2_c2.text_input("Marca:")
                laboratorio = f2_c3.text_input("Laboratorio Fabricante:")

                f3_c1, f3_c2, f3_c3 = st.columns(3)
                lote = f3_c1.text_input("Lote (*):")
                presentacion = f3_c2.text_input("Presentación:")
                clasif_riesgo = f3_c3.selectbox("Clasificación de Riesgo:", ["NA", "I", "IIa", "IIb", "III"])

                temp_transporte = st.text_input("Temperatura de Recepción (°C):", value="2°C - 8°C")

            st.markdown("###### **3. Inspección Organoléptica y Sanitaria**")
            f5_c1, f5_c2, f5_c3 = st.columns(3)
            reg_invima = f5_c1.text_input("Registro Sanitario INVIMA:")
            estado_invima = f5_c2.selectbox("Estado Registro INVIMA:", ["VIGENTE", "EN TRÁMITE", "NO APLICA"])
            fecha_vencimiento = f5_c3.date_input("Fecha de Caducidad / Vencimiento:", datetime.now())

            f6_c1, f6_c2, f6_c3 = st.columns(3)
            analisis_calidad = f6_c1.selectbox("Concepto Técnico Organoléptico:", ["OK (Conforme / Aprobado)", "RECHAZADO"])
            defecto_critico = f6_c2.selectbox("Defecto Crítico Detectado:", ["NO APLICA", "Empaque roto / perforado", "Rotulado borroso o ilegible", "Sin fecha o lote", "Partículas extrañas / turbidez"])
            cantidad = f6_c3.number_input("Cantidad Recibida (*):", min_value=1, step=1, value=10)

            st.markdown("###### **4. Trazabilidad del Responsable Técnico**")
            f7_c1, f7_c2 = st.columns(2)
            resp_recep = f7_c1.text_input("Nombre Completo de quien realiza la Recepción (*):", value="Harol Montoya")
            cargo_recep = f7_c2.selectbox("Cargo Asistencial / Administrativo:", [
                "Auxiliar del Servicio Farmacéutico",
                "Regente de Farmacia",
                "Químico Farmacéutico",
                "Coordinador de Recursos Físicos"
            ])

            color_sem, _ = semaforo(fecha_vencimiento)
            st.info(f"🚦 **Semaforización Automática (FEFO):** {color_sem}")

            guardar_rec = st.form_submit_button("Guardar Recepción Técnica en Kardex y Emitir Acta PDF")
            if guardar_rec:
                if not factura_rem.strip():
                    st.error("El N° de Factura o Remisión es obligatorio.")
                elif not nombre_prod.strip() or not lote.strip():
                    st.error("El Nombre del Producto y el Lote son obligatorios.")
                elif not resp_recep.strip():
                    st.error("Debe ingresar el nombre del responsable técnico que inspecciona.")
                else:
                    nuevo_fila = {
                        "Item": prox_item,
                        "Factura_Remision": factura_rem.strip(),
                        "Proveedor": proveedor.strip() if proveedor.strip() else "PROVEEDOR GENERAL",
                        "Fecha Ingreso": fecha_ingreso.strftime("%Y-%m-%d"),
                        "Registro INVIMA": reg_invima.strip() if reg_invima.strip() else "N/A",
                        "Estado INVIMA": estado_invima,
                        "Analisis Calidad": analisis_calidad,
                        "Defecto Critico": defecto_critico,
                        "Cantidad": int(cantidad),
                        "Responsable Tecnico": resp_recep.strip(),
                        "Cargo Responsable": cargo_recep,
                        "Semaforizacion": color_sem
                    }

                    if cat_k == "Medicamentos":
                        nuevo_fila.update({
                            "Nombre Comercial": nombre_prod.strip(),
                            "Principio Activo": principio_activo.strip() if principio_activo.strip() else "N/A",
                            "Forma Farmaceutica": forma_farm.strip() if forma_farm.strip() else "N/A",
                            "Concentracion": concentracion.strip() if concentracion.strip() else "N/A",
                            "Presentacion": presentacion.strip() if presentacion.strip() else "N/A",
                            "Via Administracion": via_adm,
                            "Unidad Medida": unidad_medida.strip() if unidad_medida.strip() else "N/A",
                            "Laboratorio": laboratorio.strip() if laboratorio.strip() else "N/A",
                            "Lote": lote.strip(),
                            "Temp Transporte": temp_transporte.strip() if temp_transporte.strip() else "Ambiente (15-25°C)",
                            "Fecha Caducidad": fecha_vencimiento.strftime("%Y-%m-%d")
                        })
                    elif cat_k in ["Dispositivos Médicos", "Insumos"]:
                        col_nombre = "Nombre Dispositivo" if cat_k == "Dispositivos Médicos" else "Nombre Insumo"
                        col_pres = "Presentacion Comercial" if cat_k == "Dispositivos Médicos" else "Presentacion"
                        nuevo_fila.update({
                            col_nombre: nombre_prod.strip(),
                            "Marca": marca_prod.strip() if marca_prod.strip() else "N/A",
                            "Laboratorio": laboratorio.strip() if laboratorio.strip() else "N/A",
                            "Serie": serie.strip() if serie.strip() else "NA",
                            "Lote": lote.strip(),
                            col_pres: presentacion.strip() if presentacion.strip() else "N/A",
                            "Clasificacion Riesgo": clasif_riesgo,
                            "Fecha Caducidad": fecha_vencimiento.strftime("%Y-%m-%d")
                        })
                    else:
                        nuevo_fila.update({
                            "Nombre Reactivo": nombre_prod.strip(),
                            "Marca": marca_prod.strip() if marca_prod.strip() else "N/A",
                            "Laboratorio": laboratorio.strip() if laboratorio.strip() else "N/A",
                            "Lote": lote.strip(),
                            "Presentacion": presentacion.strip() if presentacion.strip() else "N/A",
                            "Clasificacion Riesgo": clasif_riesgo,
                            "Temp Transporte": temp_transporte.strip() if temp_transporte.strip() else "2°C - 8°C",
                            "Fecha Vencimiento": fecha_vencimiento.strftime("%Y-%m-%d")
                        })

                    df_nuevo = pd.DataFrame([nuevo_fila])
                    df_k = pd.concat([df_k, df_nuevo], ignore_index=True)
                    guardar_k(sede_activa, cat_k, df_k)
                    
                    datos_acta_indiv = {
                        'sede': sede_activa,
                        'proveedor': proveedor.strip() if proveedor.strip() else "PROVEEDOR GENERAL",
                        'factura': factura_rem.strip(),
                        'categoria': cat_k,
                        'fecha': fecha_ingreso.strftime("%Y-%m-%d"),
                        'responsable': resp_recep.strip(),
                        'cargo': cargo_recep
                    }
                    pdf_bytes_ind, nom_pdf_ind = generar_pdf_recepcion(datos_acta_indiv, df_nuevo)
                    st.session_state["pdf_ind"] = (pdf_bytes_ind, nom_pdf_ind)
                    st.toast("✅ ¡Producto registrado exitosamente!", icon="🏥")
                    st.success(f"Producto '{nombre_prod}' registrado con éxito en {sede_activa} y su Acta Oficial en PDF fue generada.")
                    st.rerun()

        if "pdf_ind" in st.session_state:
            st.info("📄 **Acta Oficial recién generada para descargar:**")
            st.download_button(
                f"📥 Descargar Acta de este Registro en PDF ({st.session_state['pdf_ind'][1]})", 
                data=st.session_state["pdf_ind"][0], 
                file_name=st.session_state["pdf_ind"][1], 
                mime="application/pdf"
            )

    with k2:
        st.write(f"##### 📂 Cargue Masivo y Generación de Acta Oficial (PDF) - **{cat_k}**")
        st.caption("Descarga la plantilla base correspondiente a esta categoría, diligénciala y súbela para ingresar el lote y emitir el acta técnica legal.")

        plantilla_bytes = plantilla_kardex(cat_k)
        st.download_button(
            label=f"📥 Descargar Plantilla Oficial en Excel ({cat_k})",
            data=plantilla_bytes,
            file_name=f"plantilla_cargue_{normalizar(cat_k)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_down_plantilla_masiva"
        )

        st.divider()

        st.markdown("###### **1. Datos Generales del Acta y Facturación**")
        c_f1, c_f2 = st.columns(2)
        m_fac = c_f1.text_input("N° Factura / Remisión Comercial (*):", placeholder="Ej: FAC-2026-9812", key="fac_masivo")
        m_prov = c_f2.text_input("Nombre del Proveedor:", placeholder="Ej: INSUMEDICAL S.A.S.", key="prov_masivo")

        c_f3, c_f4 = st.columns(2)
        m_resp = c_f3.text_input("Nombre del Responsable Técnico que Inspecciona (*):", placeholder="Ej: Harol Montoya", value="Harol Montoya", key="resp_masivo")
        m_cargo = c_f4.selectbox("Cargo del Responsable:", [
            "Auxiliar del Servicio Farmacéutico",
            "Regente de Farmacia",
            "Químico Farmacéutico",
            "Coordinador de Recursos Físicos"
        ], key="cargo_masivo")

        st.divider()

        st.markdown("###### **2. Subir Archivo Diligenciado**")
        up_k = st.file_uploader(
            f"Selecciona el archivo Excel con los productos de {cat_k}:",
            type=["xlsx", "xls"],
            key="uploader_kardex"
        )

        if up_k is not None:
            if not m_fac.strip() or not m_resp.strip():
                st.warning("⚠️ Debe diligenciar el N° de Factura y el Nombre del Responsable para habilitar la importación y el Acta en PDF.")
            else:
                try:
                    df_procesado = procesar_archivo_cargue_masivo(
                        up_k, 
                        cat_k, 
                        m_fac, 
                        m_prov, 
                        m_resp, 
                        m_cargo
                    )
                    
                    st.write(f"Se estructuraron **{len(df_procesado)}** productos para ingresar al Kardex:")
                    st.dataframe(df_procesado.head(8), use_container_width=True, hide_index=True)
                    if len(df_procesado) > 8:
                        st.caption(f"... mostrando 8 de {len(df_procesado)} registros detectados.")

                    modo_import = st.radio("Modo de Importación:", ["Añadir a la base existente", "Reemplazar base actual de esta categoría"], horizontal=True)

                    clave_bloqueo = f"cargue_hecho_{normalizar(sede_activa)}_{normalizar(cat_k)}_{normalizar(m_fac)}_{up_k.name}"

                    if st.session_state.get(clave_bloqueo, False):
                        st.warning("🔒 **Este lote ya fue importado con éxito.** Si necesitas subirlo de nuevo o actualizarlo, cambia el N° de Factura o recarga el archivo.")
                    else:
                        if st.button("🚀 Confirmar e Importar al Kardex y Generar Acta PDF", key="btn_confirm_pdf"):
                            with st.spinner("Procesando cargue e imprimiendo Acta oficial en PDF..."):
                                df_existente = cargar_k(sede_activa, cat_k)
                                
                                if modo_import == "Añadir a la base existente":
                                    df_final = pd.concat([df_existente, df_procesado], ignore_index=True)
                                else:
                                    df_final = df_procesado
                                    
                                df_final["Item"] = range(1, len(df_final) + 1)
                                guardar_k(sede_activa, cat_k, df_final)

                                datos_acta = {
                                    'sede': sede_activa,
                                    'proveedor': m_prov.strip() if m_prov.strip() else "PROVEEDOR GENERAL",
                                    'factura': m_fac.strip(),
                                    'categoria': cat_k,
                                    'fecha': date.today().strftime("%Y-%m-%d"),
                                    'responsable': m_resp.strip(),
                                    'cargo': m_cargo
                                }
                                
                                pdf_bytes, nom_pdf = generar_pdf_recepcion(datos_acta, df_procesado)
                                st.session_state["pdf_mas"] = (pdf_bytes, nom_pdf)
                                st.session_state[clave_bloqueo] = True

                                st.balloons()
                                st.toast("🎉 ¡Cargue Masivo Exitoso!", icon="✅")
                                st.success(f"✅ **¡CARGUE EXITOSO!** Se ingresaron **{len(df_procesado)} productos** a {sede_activa} y el Acta legal en PDF fue generada.")

                except Exception as e:
                    st.error(f"Error al procesar el archivo Excel: {str(e)}")

        if "pdf_mas" in st.session_state:
            st.markdown("---")
            st.success("📄 **El Acta de Recepción Técnica está lista para ser descargada:**")
            st.download_button(
                label=f"📥 Descargar Acta Oficial en PDF ({st.session_state['pdf_mas'][1]})",
                data=st.session_state["pdf_mas"][0],
                file_name=st.session_state["pdf_mas"][1],
                mime="application/pdf",
                key="btn_descarga_acta_pdf"
            )

    with k3:
        df_k = cargar_k(sede_activa, cat_k)
        
        c_busq, _ = st.columns([2.5, 1.5])
        termino_busqueda = c_busq.text_input("🔍 Buscar por Factura, Lote, INVIMA o Nombre:", "", key="txt_busq_kardex")

        if not df_k.empty:
            col_fecha_v = COLS_K[cat_k][2]
            if col_fecha_v in df_k.columns:
                df_k["Semaforizacion"] = df_k[col_fecha_v].apply(lambda f: semaforo(f)[0])

            if termino_busqueda.strip():
                df_filtrado = df_k[
                    df_k.astype(str).apply(lambda row: row.str.contains(termino_busqueda, case=False).any(), axis=1)
                ]
            else:
                df_filtrado = df_k

            st.write(f"Mostrando **{len(df_filtrado)}** productos en **{cat_k}** ({sede_activa}):")
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

            st.markdown("##### 📥 Opciones de Exportación a Excel")
            col_exp1, col_exp2 = st.columns(2)

            with col_exp1:
                bytes_kardex_activo = exportar_kardex_activo(sede_activa)
                st.download_button(
                    label="🟢 Descargar Kardex Activo (Solo Stock > 0) [Excel]",
                    data=bytes_kardex_activo,
                    file_name=f"kardex_activo_{normalizar(sede_activa)}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="btn_down_kardex_activo",
                    help="Exporta las 4 categorías omitiendo todos los ítems en cero o agotados."
                )

            with col_exp2:
                ruta_kardex_excel = ruta_kardex(sede_activa)
                if os.path.exists(ruta_kardex_excel):
                    with open(ruta_kardex_excel, "rb") as f_k:
                        st.download_button(
                            label="📁 Descargar Kardex Completo (Con Historial y Ceros) [Excel]",
                            data=f_k,
                            file_name=f"kardex_completo_{normalizar(sede_activa)}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="btn_down_kardex_completo"
                        )

            st.divider()

            st.markdown("### 📑 Custodia y Gestión de Actas")
            st.caption("Genera actas en PDF bajo demanda y asocia los soportes escaneados firmados para auditorías de Habilitación.")

            facturas_disponibles = [f for f in df_k["Factura_Remision"].dropna().unique() if str(f).strip() not in ["N/A", "nan", ""]]
            
            if facturas_disponibles:
                anios_encontrados = set()
                if "Fecha Ingreso" in df_k.columns:
                    for f_val in df_k["Fecha Ingreso"].dropna().astype(str):
                        m = re.search(r'(20\d\d)', f_val)
                        if m:
                            anios_encontrados.add(m.group(1))

                anio_actual_str = str(date.today().year)
                anios_encontrados.add(anio_actual_str)
                lista_anios = sorted(list(anios_encontrados), reverse=True)
                opciones_anios = ["Todos"] + lista_anios

                c_f_anio, c_f_est, c_f_txt = st.columns([1.0, 1.3, 1.7])
                idx_def_anio = opciones_anios.index(anio_actual_str) if anio_actual_str in opciones_anios else 0
                filtro_anio = c_f_anio.selectbox("📅 Año:", opciones_anios, index=idx_def_anio, key="sel_filter_anio")
                filtro_estado = c_f_est.selectbox("Estado de Firma:", ["Todas", "🟡 Pendientes de Firma", "🟢 Firmadas y Custodiadas"], key="sel_filter_estado")
                busqueda_fac = c_f_txt.text_input("🔍 Buscar factura o proveedor:", placeholder="Ej: FAC o PROVEEDOR", key="txt_filter_fac")

                facturas_del_anio = []
                for f in facturas_disponibles:
                    df_sub = df_k[df_k["Factura_Remision"] == f]
                    fecha_ing = str(df_sub.iloc[0].get("Fecha Ingreso") or "")
                    m = re.search(r'(20\d\d)', fecha_ing)
                    anio_f = m.group(1) if m else ""
                    if filtro_anio == "Todos" or anio_f == str(filtro_anio):
                        facturas_del_anio.append(f)

                total_facturas = len(facturas_del_anio)
                firmadas_count = sum(1 for f in facturas_del_anio if buscar_soporte(DIR_ACTAS_FIR, f"Acta_Firmada_{normalizar(sede_activa)}_{normalizar(f)}")[0] is not None)
                pendientes_count = total_facturas - firmadas_count

                m_act1, m_act2, m_act3 = st.columns(3)
                m_act1.metric(f"Facturas ({filtro_anio})", total_facturas)
                m_act2.metric("🟢 Firmadas y Custodiadas", firmadas_count)
                m_act3.metric("🟡 Pendientes de Firma", pendientes_count)

                st.write("---")

                facturas_filtradas = []
                for f in facturas_del_anio:
                    df_sub = df_k[df_k["Factura_Remision"] == f]
                    prov_f = str(df_sub.iloc[0].get("Proveedor") or "")
                    tiene_firma = (buscar_soporte(DIR_ACTAS_FIR, f"Acta_Firmada_{normalizar(sede_activa)}_{normalizar(f)}")[0] is not None)

                    cumple_txt = (busqueda_fac.lower() in str(f).lower()) or (busqueda_fac.lower() in prov_f.lower())
                    if filtro_estado == "🟡 Pendientes de Firma":
                        cumple_est = not tiene_firma
                    elif filtro_estado == "🟢 Firmadas y Custodiadas":
                        cumple_est = tiene_firma
                    else:
                        cumple_est = True

                    if cumple_txt and cumple_est:
                        facturas_filtradas.append(f)

                if facturas_filtradas:
                    fac_seleccionada = st.selectbox(
                        f"Seleccione la Factura / Remisión ({len(facturas_filtradas)} encontradas):", 
                        facturas_filtradas, 
                        key="sel_fac_custodia"
                    )
                    
                    df_fac = df_k[df_k["Factura_Remision"] == fac_seleccionada]
                    primer_item = df_fac.iloc[0]

                    col_acta_gen, col_acta_fir = st.columns(2)

                    with col_acta_gen:
                        st.markdown("#### **1. Acta Oficial Emitida**")
                        nom_gen_esperado = f"Acta_Recepcion_{normalizar(sede_activa)}_{normalizar(fac_seleccionada)}.pdf"
                        ruta_generada = os.path.join(DIR_ACTAS_GEN, nom_gen_esperado)

                        datos_acta_seleccionada = {
                            'sede': sede_activa,
                            'proveedor': str(primer_item.get("Proveedor") or "PROVEEDOR GENERAL"),
                            'factura': str(fac_seleccionada),
                            'categoria': cat_k,
                            'fecha': str(primer_item.get("Fecha Ingreso") or date.today().strftime("%Y-%m-%d")),
                            'responsable': str(primer_item.get("Responsable Tecnico") or "Auxiliar de Farmacia"),
                            'cargo': str(primer_item.get("Cargo Responsable") or "Auxiliar del Servicio Farmacéutico")
                        }

                        if os.path.exists(ruta_generada):
                            st.success("📄 **El Acta PDF está disponible en el servidor:**")
                            with open(ruta_generada, "rb") as f_gen:
                                st.download_button(
                                    label=f"📥 Descargar Acta Oficial en PDF ({nom_gen_esperado})",
                                    data=f_gen,
                                    file_name=nom_gen_esperado,
                                    mime="application/pdf",
                                    key="btn_down_gen_existente"
                                )
                            if st.button("🔄 Regenerar / Actualizar Acta PDF", key="btn_regen_pdf"):
                                pdf_b, _ = generar_pdf_recepcion(datos_acta_seleccionada, df_fac)
                                st.success("Acta PDF actualizada correctamente con los datos del Kardex.")
                                st.rerun()
                        else:
                            st.warning("⚠️ Esta factura aún no tiene el archivo PDF compilado en disco.")
                            if st.button(f"📄 Generar Acta Oficial en PDF Ahora ({fac_seleccionada})", key="btn_generar_ondemand"):
                                with st.spinner("Compilando Acta legal en PDF..."):
                                    pdf_b, nom_pdf_nuevo = generar_pdf_recepcion(datos_acta_seleccionada, df_fac)
                                    st.success(f"¡Acta generada con éxito como '{nom_pdf_nuevo}'!")
                                    st.rerun()

                    with col_acta_fir:
                        st.markdown("#### **2. Soporte Físico Firmado**")
                        ruta_firmada, nom_firmada = buscar_soporte(DIR_ACTAS_FIR, f"Acta_Firmada_{normalizar(sede_activa)}_{normalizar(fac_seleccionada)}")

                        if ruta_firmada:
                            st.success(f"🟢 **ESTADO:** ACTA CUSTODIADA Y FIRMADA (`{nom_firmada}`)")
                            with open(ruta_firmada, "rb") as f_firmada:
                                st.download_button(
                                    label="📥 Descargar Acta Firmada (Soporte Legal)",
                                    data=f_firmada,
                                    file_name=nom_firmada,
                                    key="btn_down_firmada_cust"
                                )
                        else:
                            st.warning("🟡 **ESTADO:** PENDIENTE DE FIRMA (Falta adjuntar el escaneado)")

                        st.write("---")
                        archivo_firmado_up = st.file_uploader(
                            f"Subir o Reemplazar Acta Firmada para {fac_seleccionada}:",
                            type=["pdf", "png", "jpg", "jpeg"],
                            key="up_acta_firmada_file"
                        )
                        if st.button("💾 Guardar Acta Firmada en el Sistema", key="btn_save_acta_firmada"):
                            if archivo_firmado_up is not None:
                                nom_guardado = guardar_archivo(DIR_ACTAS_FIR, archivo_firmado_up, f"Acta_Firmada_{normalizar(sede_activa)}_{normalizar(fac_seleccionada)}")
                                st.toast("✅ Acta firmada custodiada correctamente", icon="📑")
                                st.success(f"El acta firmada se guardó exitosamente como `{nom_guardado}`.")
                                st.rerun()
                            else:
                                st.error("Debe seleccionar un archivo escaneado para subir.")

                else:
                    st.info(f"No se encontraron facturas para el año {filtro_anio} con los filtros seleccionados.")

                st.write("---")
                with st.expander("🧹 Depurar Registros Duplicados"):
                    st.caption("Si por error se importó un archivo varias veces, este botón dejará solo una copia única de cada producto y lote:")
                    if st.button("Eliminar Filas Duplicadas Ahora", key="btn_clean_dupes"):
                        col_nombre_k = "Nombre Comercial" if cat_k == "Medicamentos" else ("Nombre Dispositivo" if cat_k == "Dispositivos Médicos" else ("Nombre Insumo" if cat_k == "Insumos" else "Nombre Reactivo"))
                        filas_antes = len(df_k)
                        cols_para_comparar = [c for c in ["Factura_Remision", col_nombre_k, "Lote"] if c in df_k.columns]
                        if cols_para_comparar:
                            df_limpio = df_k.drop_duplicates(subset=cols_para_comparar, keep="first")
                        else:
                            df_limpio = df_k.drop_duplicates(keep="first")
                            
                        df_limpio["Item"] = range(1, len(df_limpio) + 1)
                        guardar_k(sede_activa, cat_k, df_limpio)
                        
                        filas_eliminadas = filas_antes - len(df_limpio)
                        st.toast("🧹 Base de datos depurada", icon="✅")
                        st.success(f"Se eliminaron {filas_eliminadas} registros duplicados. El inventario quedó depurado.")
                        st.rerun()
            else:
                st.info(f"No hay facturas registradas aún en {cat_k} para {sede_activa}.")
        else:
            st.info(f"No hay registros ingresados en {cat_k} para {sede_activa}.")

# =============================================================
# SUBMÓDULO 3: SEMAFORIZACIÓN (FEFO)
# =============================================================
elif modulo == "Semaforización (FEFO)":
    st.markdown("## 🚦 Semaforización y Rotación FEFO (FEFO)")
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
    st.markdown("## 📋 Dispensación de Insumos / Medicamentos a Pacientes")
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
                cmap = {re.sub(r'\s+', ' ', str(c).upper().strip()): c for c in df_raw.columns}
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
    st.markdown("## 🔍 Auditoría de Farmacia y Conteo Cíclico Físico")
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
                cmap = {re.sub(r'\s+', ' ', str(c).upper().strip()): c for c in df_raw.columns}
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
    st.markdown("## ♻️ Archivo Digital de Devoluciones, Bajas y Manifiestos RESPEL")
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