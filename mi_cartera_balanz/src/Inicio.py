import streamlit as st
import os
import sys

# Agregamos la ruta para poder importar el motor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.motor_cuantitativo import MotorCuantitativo

st.set_page_config(page_title="Centro de Mando | Balanz", page_icon="📊", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        .main-header {background-color: #f8fafc; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #3b82f6;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1 style='margin-top: 0; color: #1e293b;'>📊 Centro de Mando Cuantitativo</h1>
    <p style='color: #64748b; font-size: 16px;'>Plataforma integral de gestión patrimonial, auditoría de tesorería y análisis algorítmico.</p>
</div>
""", unsafe_allow_html=True)

# Crear directorio data si no existe en la nube
dir_actual = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(dir_actual, '../../data'))
os.makedirs(data_dir, exist_ok=True)

st.markdown("### 📥 1. Carga de Archivos (Actualización de Base de Datos)")
st.markdown("Sube tus reportes extraídos de Balanz para recalcular la cartera.")

col1, col2 = st.columns(2)
with col1:
    boletos_file = st.file_uploader("📂 boletos.xlsx", type=['xlsx'])
    movimientos_file = st.file_uploader("📂 movimientos.xlsx", type=['xlsx'])
with col2:
    cuentacorriente_file = st.file_uploader("📂 cuentacorriente.xlsx", type=['xlsx'])
    ordenes_file = st.file_uploader("📂 ordenes.xlsx", type=['xlsx'])

st.markdown("### ⚙️ 2. Ejecutar Algoritmo")
if st.button("🚀 Procesar Datos y Actualizar Motor", type="primary", use_container_width=True):
    archivos_subidos = 0
    
    # Guardamos los archivos subidos en el disco temporal de la nube
    if boletos_file:
        with open(os.path.join(data_dir, "boletos.xlsx"), "wb") as f: f.write(boletos_file.getbuffer())
        archivos_subidos += 1
    if movimientos_file:
        with open(os.path.join(data_dir, "movimientos.xlsx"), "wb") as f: f.write(movimientos_file.getbuffer())
        archivos_subidos += 1
    if cuentacorriente_file:
        with open(os.path.join(data_dir, "cuentacorriente.xlsx"), "wb") as f: f.write(cuentacorriente_file.getbuffer())
        archivos_subidos += 1
    if ordenes_file:
        with open(os.path.join(data_dir, "ordenes.xlsx"), "wb") as f: f.write(ordenes_file.getbuffer())
        archivos_subidos += 1

    if archivos_subidos > 0:
        with st.spinner("🧠 El Motor Cuantitativo está procesando tus datos (Valuando activos, cruzando Dólar MEP, agrupando lotes FIFO)..."):
            try:
                motor = MotorCuantitativo(data_dir=data_dir)
                motor.exportar_base_datos()
                st.success("✅ ¡Base de datos actualizada con éxito! Ya puedes navegar por las pestañas laterales.")
            except Exception as e:
                st.error(f"❌ Error interno en el motor: {e}")
    else:
        st.warning("⚠️ No subiste ningún archivo nuevo. Sube al menos un Excel de Balanz para procesar.")