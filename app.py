import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# ==============================================================================
# CONFIGURACIÓN Y CATÁLOGO DE PRODUCTOS
# ==============================================================================
DATA_FILE = "registro_pesos_historico.csv"

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
    "Fecha", "Hora_Registro", "SKU", "Descripcion", "Seccion",
    "Lote_Guia", "Peso_Teorico_kg", "Peso_Real_kg", 
    "Diferencia_kg", "Variacion_Pct", "Estado", "Observaciones"
]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, sep=";")
    return pd.DataFrame(columns=COLUMNAS)

def guardar_pesaje(fecha_seleccionada, prod_str, lote, peso_teorico, peso_real, obs):
    sku = MAPA_SKU[prod_str]
    descripcion = MAPA_DESC[prod_str]
    seccion = MAPA_SECCION[prod_str]
    
    dif_kg = round(peso_real - peso_teorico, 2)
    pct = round((dif_kg / peso_teorico) * 100, 2)
    
    if pct < -1.5:
        estado = "Merma / Faltante"
    elif pct > 1.5:
        estado = "Exceso"
    else:
        estado = "Conforme"

    nuevo_registro = pd.DataFrame([{
        "Fecha": fecha_seleccionada.strftime("%Y-%m-%d"),
        "Hora_Registro": datetime.now().strftime("%H:%M:%S"),
        "SKU": sku,
        "Descripcion": descripcion,
        "Seccion": seccion,
        "Lote_Guia": lote.strip() if lote.strip() else "S/L",
        "Peso_Teorico_kg": round(float(peso_teorico), 2),
        "Peso_Real_kg": round(float(peso_real), 2),
        "Diferencia_kg": dif_kg,
        "Variacion_Pct": pct,
        "Estado": estado,
        "Observaciones": obs.strip() if obs else ""
    }])
    
    nuevo_registro.to_csv(
        DATA_FILE, 
        mode="a", 
        header=not os.path.exists(DATA_FILE), 
        index=False, 
        sep=";", 
        encoding="utf-8-sig"
    )

# ==============================================================================
# INTERFAZ STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Control de Pesos - Recepción", layout="wide")

col_titulo, col_export = st.columns([3, 1])

with col_titulo:
    st.title("⚖️ Control de Pesos en Recepción")

df_historico = cargar_datos()

# Botón de exportación en la esquina superior derecha
with col_export:
    st.write("")
    if not df_historico.empty:
        csv_bytes = df_historico.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Exportar Histórico (CSV)",
            data=csv_bytes,
            file_name=f"historico_pesajes_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

st.markdown("---")

col_form, col_tabla = st.columns([1, 2], gap="large")

with col_form:
    st.subheader("📝 Registrar Pesaje")
    
    with st.form("form_registro", clear_on_submit=False):
        # Fecha por defecto: hoy, pero editable haciendo clic en el calendario
        fecha_ingreso = st.date_input(
            "Fecha de Ingreso:",
            value=date.today(),
            format="YYYY-MM-DD"
        )
        
        producto_sel = st.selectbox(
            "Seleccione Producto (SKU - Descripción):", 
            options=OPCIONES_PRODUCTO
        )
        
        st.caption(f"📂 **Sección:** {MAPA_SECCION[producto_sel]}")
        
        lote_guia = st.text_input("N° Lote / Guía de Remisión:", placeholder="Ej: GR-40892")
        
        c1, c2 = st.columns(2)
        with c1:
            peso_guia = st.number_input("Peso Guía (kg):", min_value=0.0, step=0.1, format="%.2f")
        with c2:
            peso_real = st.number_input("Peso Báscula (kg):", min_value=0.0, step=0.1, format="%.2f")
            
        notas = st.text_input("Observaciones:", placeholder="Opcional")
        
        btn_guardar = st.form_submit_button("💾 Guardar Ingreso", use_container_width=True)
        
        if btn_guardar:
            if peso_guia <= 0 or peso_real <= 0:
                st.error("⚠️ Ingrese pesos mayores a 0.")
            else:
                guardar_pesaje(fecha_ingreso, producto_sel, lote_guia, peso_guia, peso_real, notas)
                dif = peso_real - peso_guia
                pct = (dif / peso_guia) * 100
                st.success(f"Guardado exitosamente: {producto_sel} | Dif: {dif:+.2f} kg ({pct:+.2f}%)")
                st.rerun()

with col_tabla:
    st.subheader("📋 Histórico Acumulado")
    
    if not df_historico.empty:
        total_teo = df_historico["Peso_Teorico_kg"].sum()
        total_real = df_historico["Peso_Real_kg"].sum()
        dif_neta = total_real - total_teo
        pct_neta = (dif_neta / total_teo) * 100

        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresos Registrados", f"{len(df_historico)}")
        m2.metric("Total Báscula", f"{total_real:,.2f} kg")
        m3.metric("Diferencia Neta Total", f"{dif_neta:+,.2f} kg", delta=f"{pct_neta:+.2f}%", delta_color="inverse")

        st.dataframe(
            df_historico.iloc[::-1][[
                "Fecha", "SKU", "Descripcion", "Seccion", "Lote_Guia", 
                "Peso_Teorico_kg", "Peso_Real_kg", "Diferencia_kg", "Variacion_Pct", "Estado"
            ]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay pesajes registrados todavía.")
