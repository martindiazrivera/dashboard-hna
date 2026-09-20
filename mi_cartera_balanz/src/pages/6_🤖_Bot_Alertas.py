import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import os

st.set_page_config(page_title="Bot de Alertas | Balanz", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
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

st.title("🤖 Escáner Algorítmico y Bot de WhatsApp")
st.markdown("Configura tus **Trampas de Precio** dominicales. El radar mostrará la temperatura del mercado en vivo.")

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
    tickers_yf = [f"{t}.BA" for t in tickers]
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
        ticker_input = st.selectbox("Activo", ['GOOGL', 'AMD', 'TSM', 'MSFT', 'AAPL', 'MELI', 'NVDA', 'YPFD', 'PAMP'])
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
                
            
            # --- ESTRUCTURA DE COLUMNAS (TARJETA + BOTONES EDICIÓN) ---
            col_card, col_acciones = st.columns([5, 1])
            
            with col_card:
                st.markdown(f"<div class='alert-card' style='border-left-color: {color_borde};'><div class='alert-left'><div class='alert-title'>{tipo} : {tk}</div><div class='alert-target'>Trampa fijada en: <b>$ {precio_obj:,.2f} ARS</b></div></div>{html_vivo}</div>", unsafe_allow_html=True)
            
            with col_acciones:
                st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                with st.expander("⚙️ Opciones"):
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
                        
            st.markdown("<br>", unsafe_allow_html=True) # Espacio entre tarjetas
            
        st.markdown("---")
        if st.button("🗑️ Borrar absolutamente todas las alertas"):
            if os.path.exists(ruta_alertas): os.remove(ruta_alertas)
            st.rerun()
    else:
        st.info("Todas tus alertas ya fueron cumplidas.")
else:
    st.info("No hay alertas configuradas para esta semana.")

st.markdown("---")
st.markdown("### 📲 Bot de Envío (WhatsApp)")
st.markdown("Presiona este botón solo cuando quieras que el servidor escanee de forma pasiva y te dispare el mensaje al celular.")

def enviar_whatsapp(mensaje):
    numero = "+34623789580"
    api_key = "3891226"
    url = f"https://api.callmebot.com/whatsapp.php?phone={numero}&text={mensaje}&apikey={api_key}"
    try:
        res = requests.get(url, timeout=5)
        return res.status_code == 200
    except:
        return False

if st.button("🛰️ Enviar Alertas por WhatsApp", type="primary"):
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
                        msj = f"{icono} *ALERTA ALGORITMICA: {tk}*%0AEl precio ha cruzado tu trampa.%0ACotizacion en BYMA: $ {precio_vivo:,.2f} ARS%0AEstrategia: {row['Tipo_Alerta']}."
                        
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