import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests
import json

# ==============================================================================
# CONFIGURACIÓN DEL SCRIPT DE GOOGLE SHEETS
# ==============================================================================
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbydoj6lb9MWZLRhPfKotXH0QAEwSOv8NhWL_g5gSA2N04_IQAKp0-ks33S6JxAZlBdn/exec"

# ==============================================================================
# CATÁLOGO DE PRODUCTOS
# ==============================================================================
CATALOGO = [
    {"sku": "758486", "descripcion": "PALTA MADURA EMPACADA M X KG", "seccion": "FRUTAS Y VERDURAS"},
    {"sku": "4108", "descripcion": "MANZANA AMERICANA WASHINGTON X KG", "seccion": "FRUTAS Y VERDURAS"},
    {"sku": "110329", "descripcion": "PLATANO SEDA TIPO EXPORTACION", "seccion": "FRUTAS Y VERDURAS"},
    {"sku": "155", "descripcion": "TOMATE ITALIANO - M", "seccion": "FRUTAS Y VERDURAS"},
    {"sku": "71554", "descripcion": "PALTA FUERTE M X KG", "seccion": "FRUTAS Y VERDURAS"},
    {"sku": "67295", "descripcion": "MANZANA FUJI X KG", "seccion": "FRUTAS Y VERDURAS"},
    {"sku": "993444", "descripcion": "PAPA CONG RECTA C&C 4BOLX2.5KG (PR-M)", "seccion": "POLLOS A LA BRASA"}
]

OPCIONES_PRODUCTO = [f"{item['sku']} - {item['descripcion']}" for item in CATALOGO]
MAPA_SECCION = {f"{item['sku']} - {item['descripcion']}": item["seccion"] for item in CATALOGO}
MAPA_SKU = {f"{item['sku']} - {item['descripcion']}": item["sku"] for item in CATALOGO}
MAPA_DESC = {f"{item['sku']} - {item['descripcion']}": item["descripcion"] for item in CATALOGO}

COLUMNAS = [
    "Fecha", "Hora_Registro", "Nombre", "SKU", "Descripcion", "Seccion",
    "Peso_Guia_kg", "Peso_Bascula_k", "Diferencia_kg", "Variacion_Pct", "Estado", "Observaciones"
]

# ==============================================================================
# COMUNICACIÓN CON GOOGLE SHEETS
# ==============================================================================
def cargar_datos():
    try:
        r = requests.get(URL_APPS_SCRIPT, timeout=10)
        if r.status_code == 200:
            filas = r.json()
            if len(filas) > 1:
                df = pd.DataFrame(filas[1:], columns=filas[0])
                for col in COLUMNAS:
                    if col not in df.columns:
                        df[col] = None
                return df[COLUMNAS]
    except Exception:
        pass
    return pd.DataFrame(columns=COLUMNAS)

def guardar_pesaje(fecha_sel, nombre_op, prod_str, peso_guia, peso_bascula, obs):
    sku = MAPA_SKU[prod_str]
    descripcion = MAPA_DESC[prod_str]
    seccion = MAPA_SECCION[prod_str]
    
    dif_kg = round(peso_bascula - peso_guia, 2)
    pct = round((dif_kg / peso_guia) * 100, 2)
    
    if pct < -1.5:
        estado = "Merma / Faltante"
    elif pct > 1.5:
        estado = "Exceso"
    else:
        estado = "Conforme"

    payload = {
        "Fecha": fecha_sel.strftime("%Y-%m-%d"),
        "Hora_Registro": datetime.now().strftime("%H:%M:%S"),
        "Nombre": nombre_op.strip(),
        "SKU": sku,
        "Descripcion": descripcion,
        "Seccion": seccion,
        "Peso_Guia_kg": round(float(peso_guia), 2),
        "Peso_Bascula_k": round(float(peso_bascula), 2),
        "Diferencia_kg": dif_kg,
        "Variacion_Pct": pct,
        "Estado": estado,
        "Observaciones": obs.strip() if obs else ""
    }
    
    response = requests.post(URL_APPS_SCRIPT, data=json.dumps(payload), timeout=10)
    return response.status_code == 200

# ==============================================================================
# INTERFAZ STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Control de Pesos - Recepción", layout="wide")

col_titulo, col_export = st.columns([3, 1])

with col_titulo:
    st.title("⚖️ Control de Pesos en Recepción")

df_historico = cargar_datos()

with col_export:
    st.write("")
    if not df_historico.empty:
        csv_bytes = df_historico.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Exportar Histórico (CSV)",
            data=csv_bytes,
            file_name=f"pesajes_acumulados_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

st.markdown("---")

col_form, col_tabla = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("📝 Registrar Pesaje")
    
    with st.form("form_registro", clear_on_submit=True):
        fecha_ingreso = st.date_input("Fecha de Ingreso:", value=date.today())
        nombre_personal = st.text_input("Nombre del Operador / Personal:", placeholder="Ej: Juan Pérez")
        
        producto_sel = st.selectbox("Seleccione Producto (SKU - Descripción):", options=OPCIONES_PRODUCTO)
        st.caption(f"📂 **Sección:** {MAPA_SECCION[producto_sel]}")
        
        c1, c2 = st.columns(2)
        with c1:
            peso_guia = st.number_input("Peso Guía (kg):", min_value=0.0, step=0.1, format="%.2f")
        with c2:
            peso_bascula = st.number_input("Peso Báscula (kg):", min_value=0.0, step=0.1, format="%.2f")
            
        observaciones = st.text_input("Observaciones:", placeholder="Opcional")
        btn_guardar = st.form_submit_button("💾 Guardar Ingreso", use_container_width=True)
        
        if btn_guardar:
            if not nombre_personal.strip():
                st.error("⚠️ Por favor ingrese el nombre del operador.")
            elif peso_guia <= 0 or peso_bascula <= 0:
                st.error("⚠️ Ingrese pesos válidos mayores a 0.")
            else:
                with st.spinner("Guardando en Google Sheets..."):
                    ok = guardar_pesaje(fecha_ingreso, nombre_personal, producto_sel, peso_guia, peso_bascula, observaciones)
                if ok:
                    dif = peso_bascula - peso_guia
                    pct = (dif / peso_guia) * 100
                    st.success(f"Guardado exitosamente: {producto_sel} | Dif: {dif:+.2f} kg ({pct:+.2f}%)")
                    st.rerun()
                else:
                    st.error("No se pudo conectar con la hoja. Verifica la implementación de Apps Script.")

with col_tabla:
    st.subheader("📋 Histórico Acumulado")
    
    if not df_historico.empty:
        df_historico["Peso_Guia_kg"] = pd.to_numeric(df_historico["Peso_Guia_kg"], errors="coerce").fillna(0)
        df_historico["Peso_Bascula_k"] = pd.to_numeric(df_historico["Peso_Bascula_k"], errors="coerce").fillna(0)
        df_historico["Diferencia_kg"] = pd.to_numeric(df_historico["Diferencia_kg"], errors="coerce").fillna(0)

        total_guia = df_historico["Peso_Guia_kg"].sum()
        total_bascula = df_historico["Peso_Bascula_k"].sum()
        dif_neta = total_bascula - total_guia
        pct_neta = (dif_neta / total_guia) * 100 if total_guia > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresos Registrados", f"{len(df_historico)}")
        m2.metric("Total Báscula", f"{total_bascula:,.2f} kg")
        m3.metric("Diferencia Neta Acumulada", f"{dif_neta:+,.2f} kg", delta=f"{pct_neta:+.2f}%", delta_color="inverse")

        st.dataframe(
            df_historico.iloc[::-1],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay pesajes registrados todavía.")
