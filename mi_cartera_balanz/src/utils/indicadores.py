# src/utils/indicadores.py
import pandas as pd
import numpy as np

def bollinger_bands(series, length=20, num_stds=2):
    """
    Calcula Bandas de Bollinger.
    Investing utiliza desviación estándar poblacional (ddof=0).
    """
    ma = series.rolling(window=length).mean()
    # ddof=0 es crítico para coincidir con TradingView/Investing
    std = series.rolling(window=length).std(ddof=0) 
    
    upper = ma + (std * num_stds)
    lower = ma - (std * num_stds)
    
    return upper, ma, lower

def sma(series, period):
    """Media Móvil Simple (SMA)"""
    return series.rolling(window=period).mean()

def ema_tradingview(series, period):
    """
    Calcula la EMA exactamente como lo hace TradingView/Investing.
    La semilla inicial es la SMA.
    """
    sma_seed = series.rolling(window=period).mean()
    
    # ARRAY NUMPY PARA EVITAR ERROR READ-ONLY
    emas_array = np.full(len(series), np.nan)
    
    first_valid_idx = sma_seed.first_valid_index()
    if first_valid_idx is None:
        return pd.Series(emas_array, index=series.index)
        
    idx = series.index.get_loc(first_valid_idx)
    emas_array[idx] = sma_seed.iloc[idx]
    
    alpha = 2 / (period + 1)
    precios = series.values
    
    for i in range(idx + 1, len(series)):
        emas_array[i] = (precios[i] - emas_array[i-1]) * alpha + emas_array[i-1]
        
    return pd.Series(emas_array, index=series.index)

def calcular_emas(series, periodos=[9, 21, 55]):
    """Calcula múltiples EMAs y las devuelve en un diccionario."""
    emas = {}
    for p in periodos:
        emas[f'EMA_{p}'] = ema_tradingview(series, p)
    return emas

def _rsi_wilder_tv(series, period):
    """RSI suavizado (RMA) idéntico a TradingView."""
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    sma_up = up.rolling(window=period).mean()
    sma_down = down.rolling(window=period).mean()
    
    # ARRAYS NUMPY PARA EVITAR ERROR READ-ONLY
    rup_vals = np.full(len(series), np.nan)
    rdown_vals = np.full(len(series), np.nan)
    
    first_valid = sma_up.first_valid_index()
    if first_valid is not None:
        idx = series.index.get_loc(first_valid)
        rup_vals[idx] = sma_up.iloc[idx]
        rdown_vals[idx] = sma_down.iloc[idx]
        
        alpha = 1 / period
        up_vals = up.values
        down_vals = down.values
        
        for i in range(idx + 1, len(series)):
            rup_vals[i] = alpha * up_vals[i] + (1 - alpha) * rup_vals[i-1]
            rdown_vals[i] = alpha * down_vals[i] + (1 - alpha) * rdown_vals[i-1]
            
    rma_up = pd.Series(rup_vals, index=series.index)
    rma_down = pd.Series(rdown_vals, index=series.index)
        
    rs = rma_up / rma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def connors_rsi(close_series, rsi_period=3, streak_rsi_period=2, roc_period=100):
    """
    Calcula el Connors RSI (CRSI) compuesto por 3 elementos.
    """
    rsi_close = _rsi_wilder_tv(close_series, rsi_period)
    
    streak = np.zeros(len(close_series))
    for i in range(1, len(close_series)):
        if close_series.iloc[i] > close_series.iloc[i-1]:
            streak[i] = streak[i-1] + 1 if streak[i-1] > 0 else 1
        elif close_series.iloc[i] < close_series.iloc[i-1]:
            streak[i] = streak[i-1] - 1 if streak[i-1] < 0 else -1
        else:
            streak[i] = 0
            
    streak_series = pd.Series(streak, index=close_series.index)
    rsi_streak = _rsi_wilder_tv(streak_series, streak_rsi_period)
    
    roc = close_series.diff(1)
    percent_rank = np.zeros(len(close_series))
    
    for i in range(roc_period, len(close_series)):
        current_ret = roc.iloc[i]
        window_rets = roc.iloc[i-roc_period+1 : i+1]
        percent_rank[i] = (sum(window_rets < current_ret) / roc_period) * 100
        
    percent_rank_series = pd.Series(percent_rank, index=close_series.index)
    percent_rank_series[:roc_period] = np.nan
    
    crsi = (rsi_close + rsi_streak + percent_rank_series) / 3
    return crsi