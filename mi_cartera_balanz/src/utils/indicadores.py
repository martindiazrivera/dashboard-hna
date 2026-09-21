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

# --- FASE 3: Osciladores de Fuerza (AO y ADX) ---

def awesome_oscillator(high, low):
    """
    Calcula el Awesome Oscillator (AO).
    AO = SMA(Medio, 5) - SMA(Medio, 34)
    donde Medio = (High + Low) / 2
    """
    median_price = (high + low) / 2
    sma_5 = median_price.rolling(window=5).mean()
    sma_34 = median_price.rolling(window=34).mean()
    ao = sma_5 - sma_34
    return ao

def adx(high, low, close, period=14):
    """
    Calcula el Average Directional Index (ADX).
    """
    # 1. True Range (TR)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 2. Directional Movement (DM+ y DM-)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    plus_dm = pd.Series(plus_dm, index=close.index)
    minus_dm = pd.Series(minus_dm, index=close.index)
    
    # 3. Suavizado (RMA) idéntico a TradingView
    # Usamos np.full para evitar el ValueError read-only
    rma_tr = np.full(len(close), np.nan)
    rma_plus_dm = np.full(len(close), np.nan)
    rma_minus_dm = np.full(len(close), np.nan)
    
    # Semilla inicial (SMA de los primeros 'period' días)
    sma_tr = tr.rolling(window=period).mean()
    sma_plus = plus_dm.rolling(window=period).mean()
    sma_minus = minus_dm.rolling(window=period).mean()
    
    first_valid = sma_tr.first_valid_index()
    if first_valid is not None:
        idx = close.index.get_loc(first_valid)
        rma_tr[idx] = sma_tr.iloc[idx]
        rma_plus_dm[idx] = sma_plus.iloc[idx]
        rma_minus_dm[idx] = sma_minus.iloc[idx]
        
        alpha = 1 / period
        tr_vals = tr.values
        plus_vals = plus_dm.values
        minus_vals = minus_dm.values
        
        for i in range(idx + 1, len(close)):
            rma_tr[i] = alpha * tr_vals[i] + (1 - alpha) * rma_tr[i-1]
            rma_plus_dm[i] = alpha * plus_vals[i] + (1 - alpha) * rma_plus_dm[i-1]
            rma_minus_dm[i] = alpha * minus_vals[i] + (1 - alpha) * rma_minus_dm[i-1]
            
    rma_tr = pd.Series(rma_tr, index=close.index)
    rma_plus_dm = pd.Series(rma_plus_dm, index=close.index)
    rma_minus_dm = pd.Series(rma_minus_dm, index=close.index)
    
    # 4. Directional Indicators (+DI y -DI)
    plus_di = 100 * (rma_plus_dm / rma_tr)
    minus_di = 100 * (rma_minus_dm / rma_tr)
    
    # 5. Directional Movement Index (DX) y ADX final
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    
    # El ADX es una RMA del DX
    adx_array = np.full(len(close), np.nan)
    sma_dx = dx.rolling(window=period).mean()
    first_valid_dx = sma_dx.first_valid_index()
    
    if first_valid_dx is not None:
        idx_dx = close.index.get_loc(first_valid_dx)
        adx_array[idx_dx] = sma_dx.iloc[idx_dx]
        dx_vals = dx.values
        for i in range(idx_dx + 1, len(close)):
            adx_array[i] = alpha * dx_vals[i] + (1 - alpha) * adx_array[i-1]
            
    return pd.Series(adx_array, index=close.index)

def calcular_perfil_volumen(df, bins=50):
    """
    Calcula el Perfil de Volumen (Volume Profile) vertical/horizontal 
    agrupando el volumen por niveles de precio.
    """
    highs = df['High']
    lows = df['Low']
    vols = df['Volume']
    
    min_price = lows.min()
    max_price = highs.max()
    
    # Creamos los 'bins' o franjas de precio
    price_bins = np.linspace(min_price, max_price, bins)
    bin_volumes = np.zeros(bins - 1)
    
    # Distribuimos el volumen de cada vela en las franjas que tocó
    for h, l, v in zip(highs, lows, vols):
        if h == l:
            continue
        # En qué franjas cae esta vela
        mask = (price_bins[:-1] >= l) & (price_bins[1:] <= h) | \
               (price_bins[:-1] <= h) & (price_bins[1:] >= l)
        
        if mask.sum() > 0:
            # Distribuimos el volumen equitativamente entre los niveles tocados
            vol_per_bin = v / mask.sum()
            bin_volumes[mask] += vol_per_bin
            
    # Precios medios de cada bin para graficar
    bin_centers = (price_bins[:-1] + price_bins[1:]) / 2
    
    # Identificamos el POC (Point of Control: el precio con más volumen)
    poc_idx = np.argmax(bin_volumes)
    poc_price = bin_centers[poc_idx]
    
    return bin_centers, bin_volumes, poc_price