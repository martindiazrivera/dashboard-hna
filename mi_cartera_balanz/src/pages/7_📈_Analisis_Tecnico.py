# src/pages/7_📈_Analisis_Tecnico.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from mi_cartera_balanz.src.utils.datos_mercado import obtener_ohlcv
from mi_cartera_balanz.src.utils.indicadores import bollinger_bands, connors_rsi, calcular_emas, awesome_oscillator, adx

st.set_page_config(page_title="Análisis Técnico", page_icon="📈", layout="wide")
st.title("📈 Panel de Análisis Técnico (Quant)")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker_input = st.text_input("Activo (Ej: YPFD.BA, GGAL.BA, SPY)", value="YPFD.BA").upper()
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
            # Limpieza quirúrgica de fines de semana/feriados
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
            
            # --- 3. Panel Visual (Tarjetas de Métricas) ---
            st.markdown("### Valores Actuales (Último Cierre Válido)")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.info(f"**Precio:** $ {cierre.iloc[-1]:,.2f}")
                st.write("**Bollinger (20, 2)**")
                st.metric("Superior", f"$ {bb_up.iloc[-1]:,.2f}")
                st.metric("Media", f"$ {bb_mid.iloc[-1]:,.2f}")
                st.metric("Inferior", f"$ {bb_low.iloc[-1]:,.2f}")
                
            with m_col2:
                st.warning(f"**Osciladores**")
                st.metric("Connors RSI", f"{crsi.dropna().iloc[-1]:,.2f}")
                
            with m_col3:
                st.success(f"**Tendencia (EMAs)**")
                st.metric("EMA 9", f"$ {emas['EMA_9'].iloc[-1]:,.2f}")
                st.metric("EMA 21", f"$ {emas['EMA_21'].iloc[-1]:,.2f}")
                st.metric("EMA 55", f"$ {emas['EMA_55'].iloc[-1]:,.2f}")
                
            with m_col4:
                st.error(f"**Fuerza (Momento)**")
                st.metric("ADX (14)", f"{adx_series.dropna().iloc[-1]:,.2f}")
                st.metric("Awesome Osc (AO)", f"{ao.iloc[-1]:,.2f}")

            st.divider()
            
            # --- 4. Gráfico Interactivo de Alta Fidelidad (Plotly) ---
            st.markdown("### Gráfico Cuantitativo (Estilo TradingView)")
            
            df_plot = df.tail(120).copy() 
            
            # Ahora tenemos 3 filas (Precios, AO+ADX, CRSI)
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

            # Fila 1: Velas, BB y EMAs
            fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name="Precio"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_up.tail(120), line=dict(color='rgba(173, 204, 255, 0.5)', width=1), name='BB Sup'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_low.tail(120), line=dict(color='rgba(173, 204, 255, 0.5)', width=1), fill='tonexty', fillcolor='rgba(173, 204, 255, 0.1)', name='BB Inf'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_mid.tail(120), line=dict(color='orange', width=1.5, dash='dash'), name='BB Media'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=emas['EMA_9'].tail(120), line=dict(color='blue', width=1.5), name='EMA 9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=emas['EMA_55'].tail(120), line=dict(color='red', width=2), name='EMA 55'), row=1, col=1)

            # Fila 2: AO (Barras) y ADX (Línea)
            ao_tail = ao.tail(120)
            colors_ao = ['green' if val > 0 else 'red' for val in ao_tail]
            fig.add_trace(go.Bar(x=df_plot.index, y=ao_tail, marker_color=colors_ao, name='AO'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=adx_series.tail(120), line=dict(color='yellow', width=2), name='ADX'), row=2, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="gray", opacity=0.5, row=2, col=1) # Nivel clave ADX

            # Fila 3: CRSI
            fig.add_trace(go.Scatter(x=df_plot.index, y=crsi.tail(120), line=dict(color='purple', width=2), name='CRSI'), row=3, col=1)
            fig.add_hline(y=80, line_dash="dot", line_color="red", row=3, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="green", row=3, col=1)

            fig.update_layout(xaxis_rangeslider_visible=False, height=850, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)