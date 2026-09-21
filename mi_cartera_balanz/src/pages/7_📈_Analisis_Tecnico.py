# src/pages/7_📈_Analisis_Tecnico.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.datos_mercado import obtener_ohlcv
from utils.indicadores import bollinger_bands, connors_rsi, calcular_emas, awesome_oscillator, adx

st.set_page_config(page_title="Análisis Técnico", page_icon="📈", layout="wide")
st.title("📈 Panel de Análisis Técnico (Quant)")

# --- Helper para Métricas de Color ---
def metric_color(label, value, color="white", is_currency=False):
    val_str = f"$ {value:,.2f}" if is_currency else f"{value:,.2f}"
    html = f"""
    <div style="line-height: 1.2; margin-bottom: 15px;">
        <span style="font-size: 14px; font-weight: 600; color: #a5a5a5;">{label}</span><br>
        <span style="font-size: 28px; font-weight: 700; color: {color};">{val_str}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker_input = st.text_input("Activo (Ej: YPFD.BA, AAPL.BA, SPY)", value="AAPL.BA").upper()
with col2:
    period_input = st.selectbox("Historial de carga", ["2y", "5y", "max"], index=1)
with col3:
    st.write("") 
    st.write("")
    analizar_btn = st.button("🚀 Analizar Activo", use_container_width=True)

if analizar_btn or ticker_input:
    with st.spinner(f"Descargando datos y calculando métricas para {ticker_input}..."):
        df = obtener_ohlcv(ticker_input, period=period_input, interval="1d")
        
        if df is None or df.empty:
            st.error(f"❌ No se encontraron datos para {ticker_input}.")
        else:
            df = df.dropna(subset=['Close'])
            cierre = df['Close']
            high = df['High']
            low = df['Low']
            
            # --- 2. Cálculos Matemáticos ---
            bb_up, bb_mid, bb_low = bollinger_bands(cierre, 20, 2)
            crsi = connors_rsi(cierre, 3, 2, 100)
            emas = calcular_emas(cierre, periodos=[9, 21, 55])
            ao = awesome_oscillator(high, low)
            adx_series = adx(high, low, cierre, 14)
            
            # Últimos valores
            last_date = df.index[-1].strftime('%d/%m/%Y')
            last_close = cierre.iloc[-1]
            last_bb_up = bb_up.iloc[-1]
            last_bb_mid = bb_mid.iloc[-1]
            last_bb_low = bb_low.iloc[-1]
            last_crsi = crsi.dropna().iloc[-1]
            last_ema9 = emas['EMA_9'].iloc[-1]
            last_ema21 = emas['EMA_21'].iloc[-1]
            last_ema55 = emas['EMA_55'].iloc[-1]
            last_adx = adx_series.dropna().iloc[-1]
            last_ao = ao.iloc[-1]
            prev_ao = ao.iloc[-2]
            
            # --- 3. LÓGICA DE COLORES (SEMÁFORO) ---
            # 3.1 CRSI
            if last_crsi >= 90 or last_crsi <= 10: color_crsi = "#ff4b4b" # Rojo
            elif last_crsi >= 70 or last_crsi < 30: color_crsi = "#faca2b" # Amarillo
            else: color_crsi = "white"

            # 3.2 Bollinger (%B)
            pb = (last_close - last_bb_low) / (last_bb_up - last_bb_low)
            if pb >= 1.0 or pb <= 0.0: color_bb = "#ff4b4b" # Rompió banda (Rojo)
            elif pb >= 0.85 or pb <= 0.15: color_bb = "#faca2b" # Muy cerca (Amarillo)
            else: color_bb = "white"

            # 3.3 EMAs (Alineación)
            if last_ema9 > last_ema21 > last_ema55: color_ema = "white" # Tendencia alcista clara
            elif last_ema9 < last_ema21 < last_ema55: color_ema = "#ff4b4b" # Tendencia bajista clara
            else: color_ema = "#faca2b" # Cruzadas / Transición

            # 3.4 ADX y AO
            if last_adx < 20: color_adx = "#ff4b4b"
            elif last_adx < 25: color_adx = "#faca2b"
            else: color_adx = "white"
            
            if (last_ao > 0 and last_ao > prev_ao) or (last_ao < 0 and last_ao < prev_ao): 
                color_ao = "white" # Acelerando tendencia
            else: 
                color_ao = "#faca2b" # Perdiendo momento
            
            # --- 4. Panel Visual ---
            st.markdown(f"### Valores Actuales (Cierre: {last_date})")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.info(f"**Precio:** $ {last_close:,.2f}")
                st.write(f"**Bollinger (20, 2)**")
                metric_color("Superior", last_bb_up, is_currency=True)
                metric_color("Media", last_bb_mid, is_currency=True)
                metric_color("Inferior", last_bb_low, is_currency=True)
                
            with m_col2:
                st.warning(f"**Osciladores**")
                metric_color("Connors RSI", last_crsi, color=color_crsi)
                st.markdown(f"<div style='margin-top: 20px; font-size: 12px; color: {color_bb};'>• Precio vs Bandas (Alerta: Color)</div>", unsafe_allow_html=True)
                
            with m_col3:
                st.success(f"**Tendencia (EMAs)**")
                metric_color("EMA 9", last_ema9, color=color_ema, is_currency=True)
                metric_color("EMA 21", last_ema21, color=color_ema, is_currency=True)
                metric_color("EMA 55", last_ema55, color=color_ema, is_currency=True)
                
            with m_col4:
                st.error(f"**Fuerza (Momento)**")
                metric_color("ADX (14)", last_adx, color=color_adx)
                metric_color("Awesome Osc (AO)", last_ao, color=color_ao)

            st.divider()
            
            # --- 4. Gráfico Interactivo de Alta Fidelidad (Plotly con 4 Paneles) ---
            st.markdown("### Gráfico Cuantitativo (Estilo TradingView)")
            
            df_plot = df.tail(120).copy() 
            
            # Creamos 4 subplots: 1. Precio/BB/EMAs | 2. Volumen | 3. ADX | 4. CRSI
            fig = make_subplots(
                rows=4, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.03, 
                row_heights=[0.55, 0.15, 0.15, 0.15]
            )

            # --- FILA 1: Precio + Bollinger + EMAs ---
            fig.add_trace(go.Candlestick(
                x=df_plot.index, open=df_plot['Open'], high=df_plot['High'],
                low=df_plot['Low'], close=df_plot['Close'], name="Precio"
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_up.tail(120), line=dict(color='rgba(173, 204, 255, 0.5)', width=1), name='BB Sup'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_low.tail(120), line=dict(color='rgba(173, 204, 255, 0.5)', width=1), fill='tonexty', fillcolor='rgba(173, 204, 255, 0.1)', name='BB Inf'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_mid.tail(120), line=dict(color='orange', width=1.5, dash='dash'), name='BB Media'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=emas['EMA_9'].tail(120), line=dict(color='blue', width=1.5), name='EMA 9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=emas['EMA_55'].tail(120), line=dict(color='red', width=2), name='EMA 55'), row=1, col=1)

            # --- FILA 2: Volumen ---
            vol_tail = df_plot['Volume']
            # Colores dinámicos para el volumen según si la vela fue verde o roja
            vol_colors = ['rgba(38, 166, 154, 0.6)' if row['Close'] >= row['Open'] else 'rgba(239, 83, 80, 0.6)' for index, row in df_plot.iterrows()]
            
            fig.add_trace(go.Bar(
                x=df_plot.index, y=vol_tail, marker_color=vol_colors, name='Volumen'
            ), row=2, col=1)

            # --- FILA 3: ADX (Fuerza de Tendencia) ---
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=adx_series.tail(120), line=dict(color='yellow', width=2), name='ADX (14)'
            ), row=3, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="gray", opacity=0.5, row=3, col=1)
            fig.add_hline(y=25, line_dash="dash", line_color="orange", opacity=0.5, row=3, col=1)

            # --- FILA 4: Connors RSI (CRSI) ---
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=crsi.tail(120), line=dict(color='purple', width=2), name='CRSI'
            ), row=4, col=1)
            fig.add_hline(y=80, line_dash="dot", line_color="red", row=4, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="green", row=4, col=1)
            fig.add_hline(y=50, line_dash="solid", line_color="gray", opacity=0.3, row=4, col=1)

            # --- Configuración Global del Gráfico ---
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=950, # Aumentamos altura para que respiren los 4 paneles
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_dark",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)