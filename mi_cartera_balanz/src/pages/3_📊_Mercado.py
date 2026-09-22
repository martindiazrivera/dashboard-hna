import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Mercado | Balanz", page_icon="📊", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .sector-title {
            color: #3b82f6;
            font-size: 18px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 10px;
            border-bottom: 1px solid #1f2937;
            padding-bottom: 5px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Cotizaciones de Mercado (En Vivo ARS)")
st.markdown("Monitor de mercado argentino y global. Datos históricos del dólar y cotizaciones locales en pesos.")
st.markdown("---")

# --- FUNCIONES DE EXTRACCIÓN DE DATOS ---
@st.cache_data(ttl=3600, show_spinner=False)
def obtener_datos_macro():
    try:
        # API de Argentina Datos para Dólares
        req_dolar = requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares", timeout=5).json()
        df_dolar = pd.DataFrame(req_dolar)
        df_dolar['fecha'] = pd.to_datetime(df_dolar['fecha'])
        
        # API para Inflación (UVA)
        req_uva = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/uva", timeout=5).json()
        df_uva = pd.DataFrame(req_uva)
        df_uva['fecha'] = pd.to_datetime(df_uva['fecha'])
        
        return df_dolar, df_uva
    except:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def obtener_cotizaciones_locales(tickers):
    datos = []
    # Agregamos .BA para obtener el precio en BYMA (ARS)
    tickers_ba = [f"{t}.BA" for t in tickers]
    try:
        data = yf.download(tickers_ba, period="5d", progress=False)
        if not data.empty:
            for t, t_ba in zip(tickers, tickers_ba):
                try:
                    if len(tickers_ba) == 1:
                        cierres = data['Close'].dropna()
                    else:
                        cierres = data['Close'][t_ba].dropna()
                        
                    if len(cierres) >= 2:
                        precio_actual = float(cierres.iloc[-1])
                        precio_ayer = float(cierres.iloc[-2])
                        var_pct = ((precio_actual - precio_ayer) / precio_ayer) * 100
                        datos.append({
                            'Especie': t,
                            'Último': precio_actual,
                            '% Día': var_pct
                        })
                except:
                    continue
    except: pass
    return pd.DataFrame(datos)

# --- FORMATOS ---
def color_pct(val):
    if pd.isna(val): return ''
    color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#6b7280'
    return f'color: {color}; font-weight: bold;'

# --- MAQUETADO EN PESTAÑAS (TABS) ---
tab1, tab2, tab3 = st.tabs(["💵 Dólar Histórico & Inflación", "🇦🇷 Acciones Merval & Bonos", "🌎 CEDEARs Líderes"])

# ==========================================
# TAB 1: DÓLAR E INFLACIÓN
# ==========================================
with tab1:
    with st.spinner("Cargando datos históricos del BCRA..."):
        df_dolar, df_uva = obtener_datos_macro()
        
    if not df_dolar.empty:
        c1, c2 = st.columns([1, 3])
        
        with c1:
            st.markdown("### ⚙️ Configuración")
            tipo_dolar = st.selectbox("Tipo de Cambio", ["mep", "oficial", "blue", "ccl", "tarjeta"])
            periodo = st.radio("Período a visualizar", ["Último Mes", "Últimos 6 Meses", "Último Año", "Histórico Máximo"], index=2)
            
            # Filtro por tipo
            df_plot = df_dolar[df_dolar['casa'] == tipo_dolar].sort_values('fecha').copy()
            
            # Filtro de tiempo
            fecha_max = df_plot['fecha'].max()
            if periodo == "Último Mes": df_plot = df_plot[df_plot['fecha'] >= fecha_max - pd.DateOffset(months=1)]
            elif periodo == "Últimos 6 Meses": df_plot = df_plot[df_plot['fecha'] >= fecha_max - pd.DateOffset(months=6)]
            elif periodo == "Último Año": df_plot = df_plot[df_plot['fecha'] >= fecha_max - pd.DateOffset(years=1)]
            
            if not df_plot.empty:
                precio_hoy = df_plot['venta'].iloc[-1]
                precio_inicio = df_plot['venta'].iloc[0]
                rendimiento = ((precio_hoy - precio_inicio) / precio_inicio) * 100
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.metric(
                    label=f"Dólar {tipo_dolar.upper()} (Hoy)", 
                    value=f"$ {precio_hoy:,.2f}", 
                    delta=f"{rendimiento:,.2f}% en el período"
                )
                st.write(f"**Mínimo del período:** $ {df_plot['venta'].min():,.2f}")
                st.write(f"**Máximo del período:** $ {df_plot['venta'].max():,.2f}")
                
        with c2:
            if not df_plot.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_plot['fecha'], y=df_plot['venta'], 
                    mode='lines', name=tipo_dolar.upper(),
                    line=dict(color='#10b981', width=3),
                    fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
                ))
                fig.update_layout(
                    title=f'Evolución del Dólar {tipo_dolar.upper()}',
                    template='plotly_dark',
                    xaxis_title="Fecha", yaxis_title="Cotización (ARS)",
                    margin=dict(l=0, r=0, t=40, b=0),
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No se pudieron cargar los datos macroeconómicos en este momento.")

# ==========================================
# TAB 2: MERVAL Y BONOS
# ==========================================
with tab2:
    with st.spinner("Obteniendo cotizaciones de BYMA..."):
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown('<div class="sector-title">📊 Panel Líder (Merval)</div>', unsafe_allow_html=True)
            tickers_merval = ['ALUA', 'BBAR', 'BMA', 'BYMA', 'CEPU', 'COME', 'CRES', 'EDN', 'GGAL', 'IRSA', 'LOMA', 'METR', 'PAMP', 'SUPV', 'TECO2', 'TGNO4', 'TGSU2', 'TRAN', 'TXAR', 'VALO', 'YPFD']
            df_merval = obtener_cotizaciones_locales(tickers_merval)
            
            if not df_merval.empty:
                st.dataframe(
                    df_merval.style.map(color_pct, subset=['% Día'])
                    .format({'Último': '$ {:,.2f}', '% Día': '{:,.2f} %'}),
                    use_container_width=True, hide_index=True, height=500
                )
                
        with c2:
            st.markdown('<div class="sector-title">🏛️ Análisis de Bonos (Soberanos)</div>', unsafe_allow_html=True)
            tickers_bonos = ['AL29', 'AL30', 'AL35', 'AE38', 'AL41', 'GD30', 'GD35', 'GD46']
            df_bonos = obtener_cotizaciones_locales(tickers_bonos)
            
            if not df_bonos.empty:
                st.dataframe(
                    df_bonos.style.map(color_pct, subset=['% Día'])
                    .format({'Último': '$ {:,.2f}', '% Día': '{:,.2f} %'}),
                    use_container_width=True, hide_index=True, height=500
                )

# ==========================================
# TAB 3: CEDEARS LÍDERES
# ==========================================
with tab3:
    st.markdown("Cotización de los principales certificados extranjeros en pesos (ARS) ajustados por Dólar CCL.")
    
    sectores = {
        "⚡ Tecnología e Inteligencia Artificial": ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMD', 'MU'],
        "🛒 Comercio Electrónico y Consumo": ['MELI', 'AMZN', 'KO', 'WMT', 'MCD'],
        "🏦 Servicios Financieros y Fintech": ['NU', 'V', 'BABA'],
        "🛢️ Energía y Materiales": ['VIST', 'XOM', 'VALE', 'XLE'],
        "📊 Índices Diversificados (ETFs)": ['SPY', 'QQQ']
    }
    
    with st.spinner("Sincronizando CEDEARs con Wall Street..."):
        cols = st.columns(2)
        idx = 0
        for sector, tickers in sectores.items():
            with cols[idx % 2]:
                st.markdown(f'<div class="sector-title">{sector}</div>', unsafe_allow_html=True)
                df_sector = obtener_cotizaciones_locales(tickers)
                
                if not df_sector.empty:
                    st.dataframe(
                        df_sector.style.map(color_pct, subset=['% Día'])
                        .format({'Último': '$ {:,.2f}', '% Día': '{:,.2f} %'}),
                        use_container_width=True, hide_index=True
                    )
            idx += 1