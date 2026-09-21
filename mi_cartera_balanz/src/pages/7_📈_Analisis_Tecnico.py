# src/pages/7_📈_Analisis_Tecnico.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.datos_mercado import obtener_ohlcv
from utils.indicadores import bollinger_bands, connors_rsi, calcular_emas

st.set_page_config(page_title="Análisis Técnico", page_icon="📈", layout="wide")
st.title("📈 Panel de Análisis Técnico (Quant)")

# --- 1. Controles Superiores ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker_input = st.text_input("Activo (Ej: YPFD.BA, GGAL.BA, SPY)", value="YPFD.BA").upper()
with col2:
    period_input = st.selectbox("Historial de carga", ["2y", "5y", "max"], index=1)
with col3:
    st.write("") # Espacio para alinear el botón
    st.write("")
    analizar_btn = st.button("🚀 Analizar Activo", use_container_width=True)

if analizar_btn or ticker_input:
    with st.spinner(f"Descargando datos y calculando métricas para {ticker_input}..."):
        df = obtener_ohlcv(ticker_input, period=period_input, interval="1d")
        
        if df is None or df.empty:
            st.error(f"❌ No se encontraron datos para el ticker {ticker_input}. Verificá el símbolo.")
        else:
            # Limpiamos filas vacías fantasmas que manda Yahoo Finance los fines de semana
            df = df.dropna(subset=['Close'])
            cierre = df['Close']
            
            # --- 2. Cálculos Matemáticos ---
            bb_up, bb_mid, bb_low = bollinger_bands(cierre, 20, 2)
            crsi = connors_rsi(cierre, 3, 2, 100)
            emas = calcular_emas(cierre, periodos=[9, 21, 55])
            
            # Extraemos el último valor válido para la tabla resumen
            last_close = cierre.iloc[-1]
            last_bb_up = bb_up.iloc[-1]
            last_bb_mid = bb_mid.iloc[-1]
            last_bb_low = bb_low.iloc[-1]
            last_crsi = crsi.dropna().iloc[-1] # Dropna extra por seguridad en el CRSI
            last_ema9 = emas['EMA_9'].iloc[-1]
            last_ema21 = emas['EMA_21'].iloc[-1]
            last_ema55 = emas['EMA_55'].iloc[-1]
            
            # --- 3. Panel Visual (Tarjetas de Métricas) ---
            st.markdown("### Valores Actuales (Último Cierre)")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.info(f"**Precio Actual:** $ {last_close:,.2f}")
                st.write("**Bandas de Bollinger (20, 2)**")
                st.metric("Superior", f"$ {last_bb_up:,.2f}")
                st.metric("Media", f"$ {last_bb_mid:,.2f}")
                st.metric("Inferior", f"$ {last_bb_low:,.2f}")
                
            with m_col2:
                st.warning(f"**Osciladores**")
                st.metric("Connors RSI (3,2,100)", f"{last_crsi:,.2f}")
                # st.metric("RSI Clásico (14)", "Próximamente...")
                
            with m_col3:
                st.success(f"**Tendencia (EMAs)**")
                st.metric("EMA 9", f"$ {last_ema9:,.2f}")
                st.metric("EMA 21", f"$ {last_ema21:,.2f}")
                st.metric("EMA 55", f"$ {last_ema55:,.2f}")

            st.divider()
            
            # --- 4. Gráfico Interactivo de Alta Fidelidad (Plotly) ---
            st.markdown("### Gráfico Cuantitativo (Estilo TradingView)")
            
            # Recortamos el gráfico a los últimos 6 meses para que se vea claro y no comprimido
            df_plot = df.tail(120).copy() 
            cierre_plot = df_plot['Close']
            
            # Subplots: Fila 1 (Precio + BB + EMAs), Fila 2 (CRSI)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Velas japonesas (Candlestick)
            fig.add_trace(go.Candlestick(
                x=df_plot.index, open=df_plot['Open'], high=df_plot['High'],
                low=df_plot['Low'], close=df_plot['Close'], name="Precio"
            ), row=1, col=1)

            # Bandas de Bollinger
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_up.tail(120), line=dict(color='rgba(173, 204, 255, 0.5)', width=1), name='BB Sup'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_low.tail(120), line=dict(color='rgba(173, 204, 255, 0.5)', width=1), fill='tonexty', fillcolor='rgba(173, 204, 255, 0.1)', name='BB Inf'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=bb_mid.tail(120), line=dict(color='orange', width=1.5, dash='dash'), name='BB Media'), row=1, col=1)

            # EMAs
            fig.add_trace(go.Scatter(x=df_plot.index, y=emas['EMA_9'].tail(120), line=dict(color='blue', width=1.5), name='EMA 9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=emas['EMA_55'].tail(120), line=dict(color='red', width=2), name='EMA 55'), row=1, col=1)

            # CRSI (Panel inferior)
            fig.add_trace(go.Scatter(x=df_plot.index, y=crsi.tail(120), line=dict(color='purple', width=2), name='CRSI'), row=2, col=1)
            # Líneas de sobrecompra/sobreventa para CRSI
            fig.add_hline(y=80, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="green", row=2, col=1)
            fig.add_hline(y=50, line_dash="solid", line_color="gray", opacity=0.5, row=2, col=1)

            # Configuración estética
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=700,
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_dark", # Cambiá a "plotly_white" si preferís fondo claro
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)