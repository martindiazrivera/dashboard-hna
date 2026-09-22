import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Analytics | Balanz", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .metric-box {
            background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 100%;
        }
        .metric-title { color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;}
        .metric-value { font-size: 28px; font-weight: 700; color: #111827; }
        .metric-sub { font-size: 14px; font-weight: 500; margin-top: 4px; color: #9ca3af; }
        .green { color: #10b981; }
        .red { color: #ef4444; }
        .orange { color: #f59e0b; }
        
        /* Semáforos / Badges */
        .badge-green { background-color: #d1fae5; color: #047857; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: none;}
        .badge-red { background-color: #fee2e2; color: #b91c1c; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: none;}
        .badge-orange { background-color: #fef3c7; color: #b45309; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: none;}

        .section-title { font-size: 20px; font-weight: 600; color: #ffffff; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #374151; padding-bottom: 8px;}
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Trading Analytics & Inteligencia Operativa")
st.markdown("Métricas algorítmicas, eficiencia de comportamiento y escaneo de costos extraídos de tu historial.")

def formato_arg(valor):
    if pd.isna(valor) or valor == "": return "$ 0,00"
    try:
        return f"$ {float(valor):,.2f}".translate(str.maketrans(',.', '.,'))
    except:
        return "$ 0,00"

def formato_pct(valor):
    if pd.isna(valor) or valor == "": return "0.00 %"
    try:
        return f"{float(valor):,.2f} %".translate(str.maketrans(',.', '.,'))
    except:
        return "0.00 %"

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_reporte = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    ruta_ordenes = os.path.join(dir_actual, "../../data/ordenes.xlsx")
    
    # Cargamos fuentes de datos
    df_av = pd.read_excel(ruta_reporte, sheet_name="Analisis_Avanzado").set_index('Metrica')
    
    try:
        df_fifo = pd.read_excel(ruta_reporte, sheet_name="Operaciones_Cerradas_FIFO")
    except:
        df_fifo = pd.DataFrame()
        
    def get_val(metrica, default=0):
        return df_av.loc[metrica, 'Valor'] if metrica in df_av.index else default

    # --- SECCIÓN 1: EFICIENCIA DEL PORTFOLIO ---
    st.markdown('<div class="section-title">🎯 Eficiencia del Portfolio (Win/Loss)</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    # Cálculo en vivo del Win Rate desde la tabla FIFO
    if not df_fifo.empty and 'P&L Realizado ($)' in df_fifo.columns:
        trades = len(df_fifo)
        ganadoras = df_fifo[df_fifo['P&L Realizado ($)'] > 0]
        perdedoras = df_fifo[df_fifo['P&L Realizado ($)'] < 0]
        
        win_rate = (len(ganadoras) / trades * 100) if trades > 0 else 0
        avg_win = ganadoras['P&L Realizado ($)'].mean() if not ganadoras.empty else 0
        avg_loss = abs(perdedoras['P&L Realizado ($)'].mean()) if not perdedoras.empty else 0
    else:
        trades, win_rate, avg_win, avg_loss = 0, 0, 0, 0
        
    # Semáforo Win Rate
    wr_badge = '<span class="badge-green">✅ Saludable</span>' if win_rate >= 50 else '<span class="badge-red">⚠️ Revisar</span>'
    wr_color = "green" if win_rate >= 50 else "red"
    
    c1.markdown(f'<div class="metric-box"><div class="metric-title"><span>Win Rate (Tasa de Éxito)</span> {wr_badge}</div><div class="metric-value {wr_color}">{formato_pct(win_rate)}</div><div class="metric-sub">Basado en {trades} trades cerrados</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div class="metric-title">Promedio Ganancia (Win)</div><div class="metric-value green">{formato_arg(avg_win)}</div><div class="metric-sub">Ingreso promedio por operación exitosa</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div class="metric-title">Promedio Pérdida (Loss)</div><div class="metric-value red">-{formato_arg(avg_loss)}</div><div class="metric-sub">Pérdida promedio al cortar posiciones</div></div>', unsafe_allow_html=True)
    
    # Semáforo Ratio Riesgo / Recompensa
    rr_ratio = (avg_win / avg_loss) if avg_loss != 0 else 0
    rr_badge = '<span class="badge-green">✅ Positivo</span>' if rr_ratio >= 1 else '<span class="badge-orange">⚠️ Asimétrico</span>'
    rr_color = "green" if rr_ratio >= 1 else "orange"
    
    c4.markdown(f'<div class="metric-box"><div class="metric-title"><span>Ratio Riesgo/Recompensa</span> {rr_badge}</div><div class="metric-value {rr_color}">1 : {rr_ratio:.2f}</div><div class="metric-sub">Lo que ganas por cada $1 que arriesgas</div></div>', unsafe_allow_html=True)

    # --- SECCIÓN 2: COSTOS INVISIBLES ---
    st.markdown('<div class="section-title">💸 La Sangría Invisible (Costos de Intermediación)</div>', unsafe_allow_html=True)
    c5, c6, c7 = st.columns(3)
    
    aranceles = get_val('Comisiones Broker (Arancel)')
    mercado = get_val('Derechos de Mercado (Bolsa)')
    total_costos = get_val('Total Costos Operativos')
    
    c5.markdown(f'<div class="metric-box"><div class="metric-title">Aranceles Balanz</div><div class="metric-value red">-{formato_arg(aranceles)}</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="metric-box"><div class="metric-title">Derechos BYMA/Caja Valores</div><div class="metric-value red">-{formato_arg(mercado)}</div></div>', unsafe_allow_html=True)
    c7.markdown(f'<div class="metric-box" style="border-left: 4px solid #ef4444;"><div class="metric-title">Costo Total Friccional</div><div class="metric-value red" style="font-size: 32px;">-{formato_arg(total_costos)}</div><div class="metric-sub">Dinero retenido en intermediarios</div></div>', unsafe_allow_html=True)

    # --- SECCIÓN 3: COMPORTAMIENTO Y PSICOLOGÍA ---
    st.markdown('<div class="section-title">🧠 Comportamiento y Decisiones (Registro de Órdenes)</div>', unsafe_allow_html=True)
    c8, c9, c10 = st.columns(3)
    
    try:
        if os.path.exists(ruta_ordenes):
            df_ord = pd.read_excel(ruta_ordenes)
            tot_ord = len(df_ord)
            if tot_ord > 0 and 'Estado' in df_ord.columns:
                est = df_ord['Estado'].astype(str).str.upper().str.strip()
                cumplidas = (len(df_ord[est.isin(['EJECUTADA', 'FINALIZADA'])]) / tot_ord) * 100
                canceladas = (len(df_ord[est.isin(['CANCELADA', 'RECHAZADA'])]) / tot_ord) * 100
            else:
                cumplidas, canceladas = 0, 0
        else:
            tot_ord, cumplidas, canceladas = 0, 0, 0
    except:
        tot_ord, cumplidas, canceladas = 0, 0, 0
        
    c8.markdown(f'<div class="metric-box"><div class="metric-title">Órdenes Emitidas Totales</div><div class="metric-value">{tot_ord}</div><div class="metric-sub">Intenciones de mercado</div></div>', unsafe_allow_html=True)
    c9.markdown(f'<div class="metric-box"><div class="metric-title">Ejecución Perfecta</div><div class="metric-value green">{formato_pct(cumplidas)}</div><div class="metric-sub">Llegaron al mercado con éxito</div></div>', unsafe_allow_html=True)
    c10.markdown(f'<div class="metric-box"><div class="metric-title">Índice de Duda / Rechazo</div><div class="metric-value orange">{formato_pct(canceladas)}</div><div class="metric-sub">Órdenes canceladas por ti o el mercado</div></div>', unsafe_allow_html=True)

    # --- SECCIÓN 4: CASHFLOW Y RENTAS ---
    st.markdown('<div class="section-title">🏦 Flujo de Caja Histórico (Homologado por API MEP)</div>', unsafe_allow_html=True)
    
    c11, c12, c13 = st.columns(3)
    
    # Leemos las métricas multimoneda y sus equivalentes históricos reales de la API
    fondeos_ars = get_val('Fondeos ARS')
    fondeos_usd_hist = get_val('Fondeos USD Historico ARS')
    
    retiros_ars = get_val('Retiros ARS')
    retiros_usd_hist = get_val('Retiros USD Historico ARS')
    
    rentas_ars = get_val('Rentas ARS')
    rentas_usd_hist = get_val('Rentas USD Historico ARS')
    
    # Consolidamos usando los ARS reales del día de la transacción
    fondeos_tot = fondeos_ars + fondeos_usd_hist
    retiros_tot = retiros_ars + retiros_usd_hist
    rentas_tot = rentas_ars + rentas_usd_hist
    flujo_neto = fondeos_tot - retiros_tot
    
    c11.markdown(f'<div class="metric-box"><div class="metric-title">Aportes vs Extracciones (Consolidados)</div><div class="metric-value" style="font-size: 20px;">In: {formato_arg(fondeos_tot)}</div><div class="metric-value" style="font-size: 20px; color:#ef4444;">Out: {formato_arg(retiros_tot)}</div></div>', unsafe_allow_html=True)
    c12.markdown(f'<div class="metric-box"><div class="metric-title">Esfuerzo de Ahorro Neto</div><div class="metric-value green">{formato_arg(flujo_neto)}</div><div class="metric-sub">Capital inyectado limpio al valor del MEP del día.</div></div>', unsafe_allow_html=True)
    c13.markdown(f'<div class="metric-box" style="border-left: 4px solid #10b981;"><div class="metric-title">Ingresos Pasivos (Rentas)</div><div class="metric-value green" style="font-size: 32px;">+{formato_arg(rentas_tot)}</div><div class="metric-sub">Dividendos y Cupones ganados durmiendo</div></div>', unsafe_allow_html=True)

except FileNotFoundError:
    st.warning("⚠️ No se encontró la base de datos. Ejecuta el Motor Cuantitativo.")
except Exception as e:
    st.error(f"❌ Error al cargar las analíticas: {e}")