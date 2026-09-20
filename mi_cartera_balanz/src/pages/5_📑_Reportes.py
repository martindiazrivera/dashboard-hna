import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Reportes | Centro de Mando", page_icon="📑", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .investing-metric-card {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .metric-label { color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
        .metric-value { font-size: 24px; font-weight: 700; color: #111827; }
    </style>
""", unsafe_allow_html=True)

st.title("📑 Reportes de Posiciones y Rendimiento Neto")

def formato_arg(valor):
    if pd.isna(valor): return "$ 0,00"
    return f"$ {valor:,.2f}".translate(str.maketrans(',.', '.,'))

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    
    df_tenencia = pd.read_excel(ruta, sheet_name="Tenencia_Actual")
    df_fifo = pd.read_excel(ruta, sheet_name="Operaciones_Cerradas_FIFO")

    # MÉTRICAS LIMPIAS
    val_mercado_total = df_tenencia['Tenencia Total Valuada'].sum() if not df_tenencia.empty else 0
    bp_abiertas = df_tenencia['Ganancia/Perdida NO Realizada ($)'].sum() if not df_tenencia.empty else 0
    bp_cerradas_bruto = df_fifo['P&L Realizado ($)'].sum() if not df_fifo.empty else 0
    
    # Cálculo Estimado de Comisiones por Lote (Asumimos ~1% friccional total por el trade redondo)
    tasa_friccion = 0.01 
    if not df_fifo.empty:
        df_fifo['Costo Trade Estimado ($)'] = (df_fifo['Precio Compra Promedio'] * df_fifo['Cantidad'] * tasa_friccion) + (df_fifo['Precio Venta Real'] * df_fifo['Cantidad'] * tasa_friccion)
        df_fifo['P&L NETO de Bolsillo ($)'] = df_fifo['P&L Realizado ($)'] - df_fifo['Costo Trade Estimado ($)']
        bp_cerradas_neto = df_fifo['P&L NETO de Bolsillo ($)'].sum()
    else:
        bp_cerradas_neto = 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="investing-metric-card">
            <div class="metric-label">Val. Mercado (Abierto)</div>
            <div class="metric-value">{formato_arg(val_mercado_total)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="investing-metric-card">
            <div class="metric-label">P&L Flotante (Abierto)</div>
            <div class="metric-value" style="color:{'#10b981' if bp_abiertas >= 0 else '#ef4444'};">{formato_arg(bp_abiertas)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="investing-metric-card">
            <div class="metric-label">P&L Histórico BRUTO</div>
            <div class="metric-value" style="color:#6b7280; font-size:20px;">{formato_arg(bp_cerradas_bruto)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="investing-metric-card" style="border-left: 4px solid #10b981;">
            <div class="metric-label">P&L Histórico NETO</div>
            <div class="metric-value" style="color:{'#10b981' if bp_cerradas_neto >= 0 else '#ef4444'};">{formato_arg(bp_cerradas_neto)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:#111827; font-size: 18px;'>Registro Histórico de Ventas - Rendimiento Post-Comisiones ({len(df_fifo)} operaciones)</h3>", unsafe_allow_html=True)

    if not df_fifo.empty:
        df_fifo = df_fifo.sort_values(by='Fecha Venta', ascending=False)
        df_fifo['Fecha Venta'] = pd.to_datetime(df_fifo['Fecha Venta']).dt.strftime('%d-%m-%Y')
        
        def color_bp(val):
            color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#6b7280'
            return f'color: {color}; font-weight: 600;'
            
        formatos = {
            'Precio Compra Promedio': lambda x: formato_arg(x),
            'Precio Venta Real': lambda x: formato_arg(x),
            'P&L Realizado ($)': lambda x: formato_arg(x),
            'Costo Trade Estimado ($)': lambda x: formato_arg(x),
            'P&L NETO de Bolsillo ($)': lambda x: formato_arg(x)
        }
        
        # Filtramos columnas para mostrar
        cols_vista = ['Fecha Compra Origen', 'Fecha Venta', 'Ticker', 'Moneda', 'Cantidad', 
                      'Precio Compra Promedio', 'Precio Venta Real', 'P&L Realizado ($)', 
                      'Costo Trade Estimado ($)', 'P&L NETO de Bolsillo ($)']
        
        df_vista = df_fifo[[c for c in cols_vista if c in df_fifo.columns]]
        
        st.dataframe(
            df_vista.style.map(color_bp, subset=['P&L Realizado ($)', 'P&L NETO de Bolsillo ($)'])
                          .format(formatos),
            width='stretch', hide_index=True, use_container_width=True
        )
    else:
        st.info("No hay registro de ventas cerradas procesadas por el motor.")

except FileNotFoundError:
    st.warning("⚠️ No se encontró la base de datos. Ejecuta el Motor Cuantitativo.")
except Exception as e:
    st.error(f"❌ Error al procesar los reportes de posiciones: {e}")