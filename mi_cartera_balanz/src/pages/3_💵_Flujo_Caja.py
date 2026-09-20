import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Flujo de Caja | Balanz", page_icon="💵", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .balanz-card {
            background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            padding: 20px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .balanz-card-destacada {
            background-color: #f0fdf4; border: 2px solid #10b981; border-radius: 12px;
            padding: 20px; height: 100%; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.05);
        }
        .balanz-title { color: #4b5563; font-size: 14px; font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;}
        .balanz-total { font-size: 26px; font-weight: 700; color: #111827; margin-bottom: 2px;}
        .tc-text { color: #9ca3af; font-size: 11px; margin-top: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("💵 Gestión de Liquidez y Balance Patrimonial")
st.markdown("Auditoría integral de capital aportado, valuación de activos y rentabilidad neta global (Sincronizado con Dólar MEP histórico).")

def formato_arg(valor, decimales=2):
    if pd.isna(valor): return "$ 0,00"
    return f"$ {float(valor):,.{decimales}f}".translate(str.maketrans(',.', '.,'))

def formato_usd(valor, decimales=2):
    if pd.isna(valor): return "US$ 0,00"
    return f"US$ {float(valor):,.{decimales}f}".translate(str.maketrans(',.', '.,'))

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    
    # Cargamos fuentes de datos de Cartera y Análisis Avanzado
    df_analisis = pd.read_excel(ruta, sheet_name="Analisis_Avanzado").set_index('Metrica')
    df_tenencia = pd.read_excel(ruta, sheet_name="Tenencia_Actual")
    
    try:
        df_caja = pd.read_excel(ruta, sheet_name="Flujo_Caja")
    except:
        df_caja = pd.DataFrame()

    # Extracción de métricas de Caja / Tesorería (ARS, USD y USD convertidos históricamente)
    fondeos_ars = df_analisis.loc['Fondeos ARS', 'Valor'] if 'Fondeos ARS' in df_analisis.index else 0
    fondeos_usd = df_analisis.loc['Fondeos USD', 'Valor'] if 'Fondeos USD' in df_analisis.index else 0
    fondeos_usd_hist = df_analisis.loc['Fondeos USD Historico ARS', 'Valor'] if 'Fondeos USD Historico ARS' in df_analisis.index else 0
    
    retiros_ars = df_analisis.loc['Retiros ARS', 'Valor'] if 'Retiros ARS' in df_analisis.index else 0
    retiros_usd = df_analisis.loc['Retiros USD', 'Valor'] if 'Retiros USD' in df_analisis.index else 0
    retiros_usd_hist = df_analisis.loc['Retiros USD Historico ARS', 'Valor'] if 'Retiros USD Historico ARS' in df_analisis.index else 0

    # Balances netos de caja REALES (Pesos nativos + Dólares al MEP del día exacto)
    total_fondeos_cons = fondeos_ars + fondeos_usd_hist
    total_retiros_cons = retiros_ars + retiros_usd_hist
    balance_neto_cons = total_fondeos_cons - total_retiros_cons

    # Valuación actual y P&L de Cartera
    valuacion_actual_cartera = df_tenencia['Tenencia Total Valuada'].sum() if not df_tenencia.empty else 0
    
    # P&L Realizado Histórico
    df_macro = pd.read_excel(ruta, sheet_name="Macro_Benchmark").set_index('Metrica')
    pnl_realizado_historico = df_macro.loc['Total P&L Realizado', 'Valor'] if 'Total P&L Realizado' in df_macro.index else 0

    # ECUACIÓN PATRIMONIAL GLOBAL
    ganancia_total_global = valuacion_actual_cartera - balance_neto_cons

    # --- BLOQUE 1: RESUMEN DE LA IDENTIDAD PATRIMONIAL ---
    st.markdown("<h3 style='color:#111827;'>📊 Resumen Ejecutivo Patrimonial</h3>", unsafe_allow_html=True)
    
    r1, r2, r3, r4 = st.columns(4)
    
    with r1:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">💼 Capital Neto Invertido</div>
            <div class="balanz-total">{formato_arg(balance_neto_cons)}</div>
            <div class="tc-text">Plata neta real aportada histórica (ARS + USD MEP del día).</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r2:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">👁️ Valuación Actual Cartera</div>
            <div class="balanz-total">{formato_arg(valuacion_actual_cartera)}</div>
            <div class="tc-text">Valor de mercado hoy de tus activos vivos.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r3:
        st.markdown(f"""
        <div class="balanz-card-destacada">
            <div class="balanz-title" style="color: #065f46;">🚀 Ganancia Neta Global</div>
            <div class="balanz-total" style="color: #059669;">{formato_arg(ganancia_total_global)}</div>
            <div class="tc-text" style="color: #047857;">Crecimiento patrimonial histórico total.</div>
        </div>
        """, unsafe_allow_html=True)

    with r4:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">📈 P&L Ya Realizado (Cash)</div>
            <div class="balanz-total" style="color: #3b82f6;">{formato_arg(pnl_realizado_historico)}</div>
            <div class="tc-text">Ganancias netas aseguradas por ventas pasadas.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- BLOQUE 2: DETALLE DE TESORERÍA (Fondeos y Retiros Nativo) ---
    st.markdown("<h3 style='color:#111827;'>📥 Desglose Nativo de Tesorería</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">📥 Total Fondeado Histórico</div>
            <div class="balanz-total" style="color: #10b981;">{formato_arg(fondeos_ars)}</div>
            <div class="balanz-total" style="color: #3b82f6; font-size: 20px;">{formato_usd(fondeos_usd)}</div>
            <div class="tc-text">Recibos de Tesorería acumulados.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">📤 Total Retirado Histórico</div>
            <div class="balanz-total" style="color: #ef4444;">{formato_arg(retiros_ars)}</div>
            <div class="balanz-total" style="color: #f59e0b; font-size: 20px;">{formato_usd(retiros_usd)}</div>
            <div class="tc-text">Comprobantes de Pago extraídos a banco.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#111827;'>📋 Auditoría Oficial de Movimientos de Caja</h3>", unsafe_allow_html=True)
    
    if not df_caja.empty:
        if 'Concertacion' in df_caja.columns:
            df_caja['Concertacion'] = pd.to_datetime(df_caja['Concertacion'])
            df_caja = df_caja.sort_values(by='Concertacion', ascending=False)
            df_caja['Concertacion'] = df_caja['Concertacion'].dt.strftime('%Y-%m-%d')
            
        st.dataframe(df_caja, use_container_width=True, hide_index=True)
    else:
        st.info("No se encontraron registros de caja en el reporte.")

except FileNotFoundError:
    st.warning("⚠️ No se encontró la base de datos. Ejecuta el Motor Cuantitativo primero.")
except Exception as e:
    st.error(f"❌ Error al cargar la sección de caja: {e}")