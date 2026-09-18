import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ==============================================================================
# CONFIGURACIÓN Y ARCHIVO LOCAL
# ==============================================================================
DATA_FILE = "registro_pesos.csv"

PRODUCTOS_CATALOGO = [
    "Manzana Golden",
    "Plátano Cavendish",
    "Naranja Valencia",
    "Pera Packham",
    "Uva Red Globe"
]

TOLERANCIA_MERMA_PCT = -1.5   # Merma si la diferencia es menor a -1.5%
TOLERANCIA_EXCESO_PCT = 1.5   # Exceso si la diferencia es mayor a +1.5%

# ==============================================================================
# GESTIÓN DE DATOS
# ==============================================================================
def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "Fecha_Hora", "Lote", "Producto", "Peso_Teorico_kg", "Peso_Real_kg", "Observaciones"
    ])

def guardar_registro(lote, producto, peso_teorico, peso_real, observaciones):
    nuevo = pd.DataFrame([{
        "Fecha_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Lote": lote.strip() if lote.strip() else "S/L",
        "Producto": producto,
        "Peso_Teorico_kg": round(float(peso_teorico), 2),
        "Peso_Real_kg": round(float(peso_real), 2),
        "Observaciones": observaciones.strip() if observaciones else ""
    }])
    nuevo.to_csv(DATA_FILE, mode="a", header=not os.path.exists(DATA_FILE), index=False)

def clasificar_variacion(pct):
    if pct < TOLERANCIA_MERMA_PCT:
        return "Merma / Faltante"
    elif pct > TOLERANCIA_EXCESO_PCT:
        return "Exceso"
    return "Conforme"

# ==============================================================================
# INTERFAZ STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Control de Pesos - Recepción", layout="wide")
st.title("⚖️ Control de Pesos e Ingresos")

col_form, col_tabla = st.columns([1, 2], gap="large")

# --- FORMULARIO PARA EL PERSONAL ---
with col_form:
    st.subheader("📥 Nuevo Ingreso")
    with st.form("form_pesaje", clear_on_submit=True):
        lote_input = st.text_input("N° Lote / Guía:", placeholder="Ej: LT-101")
        prod_input = st.selectbox("Seleccione el Producto:", options=PRODUCTOS_CATALOGO)
        
        c1, c2 = st.columns(2)
        with c1:
            peso_teorico = st.number_input("Peso Guía (kg):", min_value=0.0, step=0.1, format="%.2f")
        with c2:
            peso_real = st.number_input("Peso Báscula (kg):", min_value=0.0, step=0.1, format="%.2f")
            
        notas = st.text_input("Observaciones (opcional):")
        btn_guardar = st.form_submit_button("💾 Guardar Registro", use_container_width=True)

        if btn_guardar:
            if peso_teorico <= 0 or peso_real <= 0:
                st.error("⚠️ Ingrese valores válidos mayores a 0 en ambos pesos.")
            else:
                guardar_registro(lote_input, prod_input, peso_teorico, peso_real, notas)
                dif = peso_real - peso_teorico
                pct = (dif / peso_teorico) * 100
                st.success(f"Registrado: {prod_input} | Dif: {dif:+.2f} kg ({pct:+.2f}%)")

# --- TABLA Y EXPORTACIÓN ---
with col_tabla:
    st.subheader("📊 Registros y Auditoría")
    df = cargar_datos()

    if not df.empty:
        # Añadir columnas de análisis
        df["Diferencia_kg"] = (df["Peso_Real_kg"] - df["Peso_Teorico_kg"]).round(2)
        df["Variacion_Pct"] = ((df["Diferencia_kg"] / df["Peso_Teorico_kg"]) * 100).round(2)
        df["Estado"] = df["Variacion_Pct"].apply(clasificar_variacion)

        # Métricas de resumen arriba
        tot_teorico = df["Peso_Teorico_kg"].sum()
        tot_real = df["Peso_Real_kg"].sum()
        dif_neta = tot_real - tot_teorico
        pct_neta = (dif_neta / tot_teorico) * 100

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Teórico (Guía)", f"{tot_teorico:,.2f} kg")
        m2.metric("Total Báscula", f"{tot_real:,.2f} kg")
        m3.metric("Diferencia Neta", f"{dif_neta:+,.2f} kg", delta=f"{pct_neta:+.2f}%", delta_color="inverse")

        # Vista previa en pantalla (últimos registros primero)
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)

        # Preparación del CSV con codificación para Excel en español
        # index=False evita columnas numéricas innecesarias
        csv_bytes = df.to_csv(index=False, sep=";").encode("utf-8-sig")

        st.download_button(
            label="📥 Descargar Reporte Completo con Análisis (CSV)",
            data=csv_bytes,
            file_name=f"reporte_pesajes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No hay registros todavía. El personal puede empezar a cargar datos a la izquierda.")