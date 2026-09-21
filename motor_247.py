# motor_247.py
import os
import pandas as pd
import yfinance as yf
import requests
import datetime

# --- CONFIGURACIÓN ---
TG_TOKEN = os.environ.get("TG_TOKEN", "8830821591:AAFCA5BTdzZYcckBM8TnTdvWjouoqh4IhyM")
TG_CHATID = os.environ.get("TG_CHATID", "1051645650")

# Rutas de los archivos de configuración y alertas
RUTA_ALERTAS = "data/alertas_trading.csv"
RUTA_WATCHLIST = "data/watchlist.csv"

def obtener_tickers_a_escanear():
    if os.path.exists(RUTA_WATCHLIST):
        df_w = pd.read_csv(RUTA_WATCHLIST)
        return df_w['Ticker'].tolist()
    return ["YPFD.BA", "GGAL.BA", "PAMP.BA"]

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHATID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def ejecutar_escaner():
    print(f"[{datetime.datetime.now()}] Iniciando escaneo de GitHub Actions...")
    
    # 1. Escaneo de Trampas Manuales
    if not os.path.exists(RUTA_ALERTAS):
        print("No se encontró el archivo de alertas manuales.")
        return

    df = pd.read_csv(RUTA_ALERTAS)
    activas = df[df['Estado'] == 'ACTIVA']
    
    if activas.empty:
        print("No hay alertas activas para escanear.")
        return

    tickers = activas['Ticker'].unique().tolist()
    tickers_yf = [f"{t}.BA" if not t.endswith('.BA') else t for t in tickers]
    
    try:
        data = yf.download(tickers_yf, period="1d", progress=False)
        precios_vivos = {}
        for t, t_ba in zip(tickers, tickers_yf):
            if len(tickers_yf) == 1:
                precios_vivos[t] = float(data['Close'].iloc[-1])
            else:
                precios_vivos[t] = float(data['Close'][t_ba].iloc[-1])
    except Exception as e:
        print(f"Error descargando precios: {e}")
        return

    hubo_cambios = False
    
    for index, row in activas.iterrows():
        tk = row['Ticker']
        precio_obj = row['Precio_Objetivo']
        condicion = row['Condicion']
        precio_vivo = precios_vivos.get(tk, 0)
        
        if precio_vivo > 0:
            disparo = False
            if condicion == '<=' and precio_vivo <= precio_obj: disparo = True
            elif condicion == '>=' and precio_vivo >= precio_obj: disparo = True
                
            if disparo:
                icono = "🟢" if row['Tipo_Alerta'] == 'COMPRA' else "🔴"
                msj = f"{icono} *ALERTA EN LA NUBE: {tk}*\nTu trampa algorítmica fue cruzada.\nCotizacion: $ {precio_vivo:,.2f} ARS\nEstrategia: {row['Tipo_Alerta']}."
                
                print(f"¡Disparo detectado para {tk}! Enviando Telegram...")
                enviar_telegram(msj)
                
                df.at[index, 'Estado'] = 'CUMPLIDA'
                hubo_cambios = True

    if hubo_cambios:
        df.to_csv(RUTA_ALERTAS, index=False)
        print("Estados actualizados en el CSV.")

if __name__ == "__main__":
    ejecutar_escaner()