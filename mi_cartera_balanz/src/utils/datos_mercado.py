# src/utils/datos_mercado.py
import yfinance as yf
import pandas as pd

def obtener_ohlcv(ticker, period="2y", interval="1d"):
    """
    Descarga el historial de precios OHLCV desde Yahoo Finance.
    Para acciones argentinas, asegúrate de pasar el ticker con el sufijo .BA (ej: YPFD.BA)
    """
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty:
            return None
        
        # yfinance reciente puede devolver MultiIndex, aplanamos si es necesario
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        return data
    except Exception as e:
        print(f"Error descargando {ticker}: {e}")
        return None