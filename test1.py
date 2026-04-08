import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Configuración y base de datos
DB_FILE = "gestion_activos.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    return pd.DataFrame(columns=["Equipo", "Tipo", "Fecha", "Horas_Operacion", "Horas_Reparacion", "Falla", "Estado"])

st.set_page_config(page_title="Mantenimiento Industrial PRO", layout="wide")
st.title("🚜 Gestión de Activos y KPIs (MTBF, MTTR, OEE)")

df = cargar_datos()

# --- PANEL LATERAL: REGISTRO ---
st.sidebar.header("Registrar Actividad")
with st.sidebar.form("registro_form"):
    equipo = st.selectbox("Equipo", ["Grúa Horquilla 1", "Grúa Horquilla 2", "Retrocavadora Pulpo", "Maquinaria Industrial"])
    tipo = st.selectbox("Tipo de Actividad", ["Mantenimiento Preventivo", "Reparación Correctiva (Falla)", "Operación Normal"])
    fecha = st.date_input("Fecha")
    h_operacion = st.number_input("Horas de Operación", min_value=0.0, step=0.5)
    h_reparacion = st.number_input("Horas de Reparación (Down-time)", min_value=0.0, step=0.5)
    es_falla = 1 if tipo == "Reparación Correctiva (Falla)" else 0
    
    boton_guardar = st.form_submit_button("Guardar Datos")

if boton_guardar:
    nuevo = pd.DataFrame([[equipo, tipo, fecha, h_operacion, h_reparacion, es_falla, "Finalizado"]], 
                         columns=df.columns)
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    st.sidebar.success("Registrado correctamente")

# --- CÁLCULO DE KPIs ---
st.header("📊 Indicadores de Rendimiento")

if not df.empty:
    resumen = df.groupby("Equipo").agg({
        "Horas_Operacion": "sum",
        "Horas_Reparacion": "sum",
        "Falla": "sum"
    }).reset_index()

    resumen['MTBF'] = resumen.apply(lambda x: x['Horas_Operacion'] / x['Falla'] if x['Falla'] > 0 else x['Horas_Operacion'], axis=1)
    resumen['MTTR'] = resumen.apply(lambda x: x['Horas_Reparacion'] / x['Falla'] if x['Falla'] > 0 else 0, axis=1)
    resumen['Disponibilidad'] = (resumen['MTBF'] / (resumen['MTBF'] + resumen['MTTR'])) * 100
    resumen['OEE'] = (resumen['Disponibilidad'] / 100) * 0.95 * 0.98 * 100

    cols = st.columns(len(resumen))
    for i, row in resumen.iterrows():
        with cols[i]:
            st.metric(f"Disponibilidad {row['Equipo']}", f"{row['Disponibilidad']:.1f}%")
            st.write(f"**MTBF:** {row['MTBF']:.1f} hrs")
            st.write(f"**MTTR:** {row['MTTR']:.1f} hrs")
            st.progress(row['OEE'] / 100, text=f"OEE: {row['OEE']:.1f}%")

    st.divider()
    st.subheader("📋 Base de Datos Completa")
    st.dataframe(df)
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Base de Datos (CSV)", data=csv_data, file_name="mantenimiento_export.csv", mime="text/csv")
else:
    st.warning("No hay datos suficientes para calcular KPIs. Registra la primera actividad en el panel lateral.")
    