# src/pages/8_🤖_Bot_Alertas.py
import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import os

# Importamos tu motor cuantitativo
from utils.datos_mercado import obtener_ohlcv
from utils.indicadores import (bollinger_bands, connors_rsi, calcular_emas, awesome_oscillator, adx, calcular_perfil_volumen)

st.set_page_config(page_title="Bot de Alertas", page_icon="🤖", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        .alert-card { 
            background-color: #ffffff; border: 1px solid #e5e7eb; border-left: 5px solid; 
            border-radius: 8px; padding: 16px; margin-bottom: 0px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
            display: flex; justify-content: space-between; align-items: center; height: 100%;
        }
        .alert-left { display: flex; flex-direction: column; }
        .alert-right { display: flex; flex-direction: column; text-align: right; }
        .alert-title { font-weight: 700; color: #1f2937; font-size: 16px; margin-bottom: 4px;}
        .alert-target { font-size: 14px; color: #6b7280; }
        .alert-live { font-size: 22px; font-weight: 700; color: #111827; }
        .alert-dist { font-size: 13px; font-weight: 700; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-top: 4px;}
        .dist-far { background-color: #f3f4f6; color: #6b7280; }
        .dist-warm { background-color: #fef3c7; color: #d97706; }
        .dist-hot { background-color: #fee2e2; color: #ef4444; }
        .dist-triggered { background-color: #111827; color: #10b981; animation: pulse 2s infinite;}
        
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Centro de Control: Bot de Alertas")

# --- PESTAÑAS PRINCIPALES ---
tab_manual, tab_quant, tab_config = st.tabs(["🎯 Trampas de Precio (Manual)", "🧠 Escáner Algorítmico (Quant)", "⚙️ Configuración API"])

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN
# ==========================================
with tab_config:
    st.markdown("### Configuración de Telegram")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        telegram_token = st.text_input("Token del Bot (BotFather)", type="password")
    with col_t2:
        telegram_chatid = st.text_input("Chat ID (Tu usuario)", type="password")
        
    st.markdown("### Configuración de WhatsApp (CallMeBot)")
    st.info("Actualmente configurado con el número +34623789580 y API Key 3891226.")

def enviar_telegram(mensaje):
    if not telegram_token or not telegram_chatid:
        return False, "Faltan credenciales de Telegram."
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chatid, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload)
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

def enviar_whatsapp(mensaje):
    numero = "+34623789580"
    api_key = "3891226"
    url = f"https://api.callmebot.com/whatsapp.php?phone={numero}&text={mensaje}&apikey={api_key}"
    try:
        res = requests.get(url, timeout=5)
        return res.status_code == 200
    except:
        return False

# ==========================================
# PESTAÑA 1: TRAMPAS MANUALES (TU CÓDIGO ORIGINAL)
# ==========================================
with tab_manual:
    ruta_alertas = os.path.join(os.path.dirname(__file__), "../../data/alertas_trading.csv")

    def cargar_alertas():
        if os.path.exists(ruta_alertas):
            return pd.read_csv(ruta_alertas)
        else:
            return pd.DataFrame(columns=['Ticker', 'Tipo_Alerta', 'Precio_Objetivo', 'Condicion', 'Estado'])

    df_alertas = cargar_alertas()

    @st.cache_data(ttl=60)
    def obtener_precios_radar(tickers):
        if not tickers: return {}
        tickers_yf = [f"{t}.BA" if not t.endswith('.BA') else t for t in tickers]
        precios = {}
        try:
            data = yf.download(tickers_yf, period="1d", progress=False)
            if not data.empty:
                for t, t_ba in zip(tickers, tickers_yf):
                    try:
                        if len(tickers_yf) == 1: precios[t] = float(data['Close'].iloc[-1])
                        else: precios[t] = float(data['Close'][t_ba].iloc[-1])
                    except: pass
        except: pass
        return precios

    st.markdown("### ⚙️ Nueva Regla de Trading")
    with st.form("form_alerta"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ticker_input = st.selectbox("Activo", ['YPFD.BA', 'GGAL.BA', 'PAMP.BA', 'AAPL.BA', 'MELI.BA', 'NVDA.BA', 'AMD.BA', 'GOOGL.BA'])
        with c2:
            tipo_alerta = st.selectbox("Estrategia", ["🟢 COMPRA (cRSI < 10 + Soporte)", "🔴 VENTA (cRSI > 90 + Resistencia)"])
        with c3:
            precio_input = st.number_input("Precio Trampa (ARS)", min_value=0.0, step=100.0, format="%.2f")
        with c4:
            condicion_input = st.selectbox("Disparador", ["Si el precio CAE por debajo de (<=)", "Si el precio SUBE por encima de (>=)"])
            
        submit = st.form_submit_button("Guardar Alerta")
        
        if submit and precio_input > 0:
            nueva_alerta = pd.DataFrame([{
                'Ticker': ticker_input,
                'Tipo_Alerta': 'COMPRA' if 'COMPRA' in tipo_alerta else 'VENTA',
                'Precio_Objetivo': precio_input,
                'Condicion': '<=' if 'CAE' in condicion_input else '>=',
                'Estado': 'ACTIVA'
            }])
            df_alertas = pd.concat([df_alertas, nueva_alerta], ignore_index=True)
            df_alertas.to_csv(ruta_alertas, index=False)
            st.cache_data.clear()
            st.success(f"Alerta guardada para {ticker_input} a $ {precio_input:,.2f} ARS")
            st.rerun()

    st.markdown("---")
    col_tit, col_btn = st.columns([4, 1])
    with col_tit: st.markdown("### 📡 Radar Activo (Termómetro de Precios)")
    with col_btn: 
        if st.button("🔄 Refrescar Precios"): 
            st.cache_data.clear()
            st.rerun()

    precios_vivos = {}
    if not df_alertas.empty:
        activas = df_alertas[df_alertas['Estado'] == 'ACTIVA']
        if not activas.empty:
            tickers_activos = activas['Ticker'].unique().tolist()
            precios_vivos = obtener_precios_radar(tickers_activos)
            
            for index, row in activas.iterrows():
                tk = row['Ticker']
                precio_obj = row['Precio_Objetivo']
                condicion = row['Condicion']
                tipo = row['Tipo_Alerta']
                
                color_borde = "#10b981" if tipo == 'COMPRA' else "#ef4444"
                precio_vivo = precios_vivos.get(tk, 0)
                
                if precio_vivo > 0:
                    disparada = False
                    if condicion == '<=' and precio_vivo <= precio_obj: disparada = True
                    if condicion == '>=' and precio_vivo >= precio_obj: disparada = True
                    
                    if disparada:
                        clase_dist = "dist-triggered"
                        txt_dist = "🚨 ¡TRAMPA CRUZADA! ZONA EJECUCIÓN"
                    else:
                        distancia_pct = (abs(precio_vivo - precio_obj) / precio_obj) * 100
                        if distancia_pct <= 2.0:
                            clase_dist = "dist-hot"
                            txt_dist = f"🔥 A {distancia_pct:.2f}% (¡Zona de disparo!)"
                        elif distancia_pct <= 5.0:
                            clase_dist = "dist-warm"
                            txt_dist = f"⚠️ A {distancia_pct:.2f}% (Acercándose)"
                        else:
                            clase_dist = "dist-far"
                            txt_dist = f"A {distancia_pct:.2f}% de distancia"
                    
                    html_vivo = f"<div class='alert-right'><div class='alert-live'>$ {precio_vivo:,.2f}</div><div class='alert-dist {clase_dist}'>{txt_dist}</div></div>"
                else:
                    html_vivo = f"<div class='alert-right'><div class='alert-live' style='color: #9ca3af;'>Sin datos</div><div class='alert-dist dist-far'>Mercado cerrado o error de red</div></div>"
                    
                col_card, col_acciones = st.columns([5, 1])
                with col_card:
                    st.markdown(f"<div class='alert-card' style='border-left-color: {color_borde};'><div class='alert-left'><div class='alert-title'>{tipo} : {tk}</div><div class='alert-target'>Trampa fijada en: <b>$ {precio_obj:,.2f} ARS</b></div></div>{html_vivo}</div>", unsafe_allow_html=True)
                
                with col_acciones:
                    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                    with st.expander("⚙️"):
                        nuevo_precio = st.number_input("Precio ($)", value=float(precio_obj), key=f"precio_{index}", step=100.0)
                        if st.button("💾 Guardar", key=f"guardar_{index}", use_container_width=True):
                            df_alertas.at[index, 'Precio_Objetivo'] = nuevo_precio
                            df_alertas.to_csv(ruta_alertas, index=False)
                            st.cache_data.clear()
                            st.rerun()
                        if st.button("🗑️ Eliminar", key=f"eliminar_{index}", use_container_width=True):
                            df_alertas = df_alertas.drop(index)
                            df_alertas.to_csv(ruta_alertas, index=False)
                            st.cache_data.clear()
                            st.rerun()
                            
                st.markdown("<br>", unsafe_allow_html=True) 
                
            st.markdown("---")
            if st.button("🗑️ Borrar absolutamente todas las alertas"):
                if os.path.exists(ruta_alertas): os.remove(ruta_alertas)
                st.rerun()
        else:
            st.info("Todas tus alertas ya fueron cumplidas.")
    else:
        st.info("No hay alertas configuradas para esta semana.")

    st.markdown("---")
    if st.button("🛰️ Enviar Alertas Cruzadas por WhatsApp", type="primary"):
        if df_alertas.empty:
            st.warning("Configura alertas primero.")
        else:
            with st.spinner("Procesando envíos..."):
                alertas_disparadas = 0
                for index, row in df_alertas[df_alertas['Estado'] == 'ACTIVA'].iterrows():
                    tk = row['Ticker']
                    precio_obj = row['Precio_Objetivo']
                    precio_vivo = precios_vivos.get(tk, 0)
                    
                    if precio_vivo > 0:
                        disparo = False
                        if row['Condicion'] == '<=' and precio_vivo <= precio_obj: disparo = True
                        elif row['Condicion'] == '>=' and precio_vivo >= precio_obj: disparo = True
                            
                        if disparo:
                            icono = "🟢" if row['Tipo_Alerta'] == 'COMPRA' else "🔴"
                            msj = f"{icono} *ALERTA MANUAL: {tk}*%0AEl precio ha cruzado tu trampa.%0ACotizacion en BYMA: $ {precio_vivo:,.2f} ARS%0AEstrategia: {row['Tipo_Alerta']}."
                            
                            if enviar_whatsapp(msj):
                                st.success(f"Aviso enviado por WhatsApp para {tk}!")
                                df_alertas.at[index, 'Estado'] = 'CUMPLIDA'
                                alertas_disparadas += 1
                            else:
                                st.error(f"Fallo de conexión con WhatsApp para {tk}")
                
                if alertas_disparadas > 0:
                    df_alertas.to_csv(ruta_alertas, index=False)
                    st.cache_data.clear()
                else:
                    st.info("Ninguna acción cruzó tus precios objetivo para enviar alerta.")

# ==========================================
# PESTAÑA 2: ESCÁNER QUANT (NUEVO MOTOR)
# ==========================================
with tab_quant:
    st.markdown("### Escáner Multiactivo y Reporte Institucional")

    tickers_cartera = ["YPFD.BA", "GGAL.BA", "PAMP.BA"] 

    st.info("📌 **Activos en Cartera (Prioridad):** Estos activos se escanean para buscar divergencias o toma de ganancias.")
    tickers_seleccionados = st.multiselect(
        "Selecciona los activos para el escáner (Cartera + Watchlist):", 
        options=list(set(tickers_cartera + ["AAPL.BA", "MELI.BA", "SPY", "QQQ", "AMD.BA", "NVDA.BA", "GOOGL.BA"])),
        default=tickers_cartera
    )

    if st.button("🔍 Ejecutar Escáner Quant y Enviar a Telegram", use_container_width=True):
        if not tickers_seleccionados:
            st.warning("⚠️ Selecciona al menos un activo para escanear.")
        else:
            with st.spinner("Ejecutando algoritmos quant de 5 años..."):
                alertas_generadas = []
                
                for ticker in tickers_seleccionados:
                    df = obtener_ohlcv(ticker, period="5y", interval="1d")
                    if df is None or df.empty: continue
                        
                    df = df.dropna(subset=['Close'])
                    cierre = df['Close']
                    high = df['High']
                    low = df['Low']
                    volume = df['Volume']
                    
                    bb_up, bb_mid, bb_low = bollinger_bands(cierre, 20, 2)
                    crsi = connors_rsi(cierre, 3, 2, 100)
                    emas = calcular_emas(cierre, periodos=[9, 21, 55])
                    
                    df_plot = df.tail(126).copy() # Ventana de 6 meses para el POC
                    _, _, poc_price = calcular_perfil_volumen(df_plot, bins=40)
                    
                    last_close = cierre.iloc[-1]
                    last_crsi = crsi.dropna().iloc[-1]
                    last_ema9 = emas['EMA_9'].iloc[-1]
                    last_ema55 = emas['EMA_55'].iloc[-1]
                    last_vol = volume.iloc[-1]
                    vol_sma20 = volume.rolling(window=20).mean().iloc[-1]
                    
                    alertas_ticker = []
                    
                    # Reglas Quant
                    if last_crsi <= 15: alertas_ticker.append(f"🟢 *CRSI Sobrevendido:* {last_crsi:.2f}")
                    elif last_crsi >= 85: alertas_ticker.append(f"🔴 *CRSI Sobrecomprado:* {last_crsi:.2f}")
                        
                    if last_ema9 > last_ema55 and emas['EMA_9'].iloc[-2] <= emas['EMA_55'].iloc[-2]:
                        alertas_ticker.append("🚀 *Golden Cross:* EMA 9 cruzó al alza EMA 55")
                    elif last_ema9 < last_ema55 and emas['EMA_9'].iloc[-2] >= emas['EMA_55'].iloc[-2]:
                        alertas_ticker.append("💀 *Death Cross:* EMA 9 cruzó a la baja EMA 55")
                        
                    distancia_poc = abs((last_close - poc_price) / poc_price)
                    if distancia_poc < 0.02 and last_vol > (vol_sma20 * 1.2):
                        alertas_ticker.append(f"⚠️ *Testeo POC Institucional ($ {poc_price:,.2f})* con volumen alto.")

                    if alertas_ticker:
                        texto_activo = f"*{ticker}* (Precio: ${last_close:,.2f})\n" + "\n".join([f"  {a}" for a in alertas_ticker])
                        alertas_generadas.append(texto_activo)
                
                if alertas_generadas:
                    reporte_final = "📊 *REPORTE QUANT BALANZ*\n\n" + "\n\n".join(alertas_generadas)
                    st.success("✅ Alertas detectadas. Reporte generado:")
                    st.markdown(reporte_final)
                    
                    exito, msg = enviar_telegram(reporte_final)
                    if exito: st.toast("📲 Reporte institucional enviado a Telegram.", icon="✅")
                    else: st.error(f"Error de Telegram: {msg}")
                else:
                    st.info("😴 No se generaron alertas algorítmicas para tu cartera hoy.")