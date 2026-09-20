import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Mercado | Balanz", page_icon="📊", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 Cotizaciones de Mercado (En Vivo)")
st.markdown("Monitor de mercado global. Datos obtenidos sin latencia desde Wall Street (Yahoo Finance).")
st.markdown("---")

@st.cache_data(ttl=300) # Caché de 5 minutos para no saturar la red
def obtener_cotizaciones():
    # Usamos ADRs de empresas argentinas e índices principales para estabilidad total
    tickers = ['YPF', 'GGAL', 'PAM', 'MELI', 'NVDA', 'AAPL', 'MSFT', 'SPY', 'QQQ', 'TSLA', 'AMD']
    datos_mercado = []
    
    try:
        data = yf.download(tickers, period="2d", progress=False)
        if not data.empty:
            for t in tickers:
                try:
                    cierres = data['Close'][t].dropna()
                    if len(cierres) >= 2:
                        precio_actual = float(cierres.iloc[-1])
                        precio_ayer = float(cierres.iloc[-2])
                        var_usd = precio_actual - precio_ayer
                        var_pct = (var_usd / precio_ayer) * 100
                        volumen = float(data['Volume'][t].iloc[-1])
                        
                        datos_mercado.append({
                            'Ticker': t,
                            'Precio (USD)': precio_actual,
                            'Var (%)': var_pct,
                            'Var (USD)': var_usd,
                            'Volumen': volumen
                        })
                except:
                    continue
    except Exception as e:
        st.error(f"Error temporal de conexión con el proveedor de mercado.")
        
    return pd.DataFrame(datos_mercado)

# Formateadores nativos
def formato_usd(valor):
    if pd.isna(valor): return ""
    return f"u$s {valor:,.2f}".translate(str.maketrans(',.', '.,'))

def formato_pct(valor):
    if pd.isna(valor): return ""
    return f"{valor:,.2f} %".translate(str.maketrans(',.', '.,'))

def formato_vol(valor):
    if pd.isna(valor): return ""
    return f"{valor:,.0f}".translate(str.maketrans(',.', '.,'))

with st.spinner("Sincronizando con Wall Street..."):
    df_mercado = obtener_cotizaciones()
    
    if not df_mercado.empty:
        c1, c2 = st.columns([1, 3])
        with c1:
            buscador = st.text_input("🔍 Buscar ticker...", placeholder="Ej: YPF, NVDA, SPY")
            
        if buscador:
            df_mercado = df_mercado[df_mercado['Ticker'].str.contains(buscador.upper())]
            
        def color_variacion(val):
            color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#6b7280'
            return f'color: {color}; font-weight: bold;'

        st.dataframe(
            df_mercado.style
            .map(color_variacion, subset=['Var (%)', 'Var (USD)'])
            .format({
                'Precio (USD)': formato_usd,
                'Var (%)': formato_pct,
                'Var (USD)': formato_usd,
                'Volumen': formato_vol
            }),
            use_container_width=True,
            hide_index=True,
            height=600
        )
    else:
        st.warning("El mercado se encuentra cerrado o no hay conexión disponible.")