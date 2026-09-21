import pandas as pd
from mi_cartera_balanz.src.utils.datos_mercado import obtener_ohlcv
from mi_cartera_balanz.src.utils.indicadores import bollinger_bands, connors_rsi, calcular_emas

# 1. Obtenemos datos (Mantenemos 5 años para asegurar el arrastre del suavizado)
ticker = "YPFD.BA"
df = obtener_ohlcv(ticker, period="5y", interval="1d")

if df is not None and not df.empty:
    cierre = df['Close']
    
    # 2. Calculamos TODO
    bb_up, bb_mid, bb_low = bollinger_bands(cierre, 20, 2)
    crsi = connors_rsi(cierre, 3, 2, 100)
    emas = calcular_emas(cierre, periodos=[9, 21, 55])
    
    # 3. Armamos el DataFrame de resultados
    resultados = pd.DataFrame({
        'Cierre': cierre,
        'BB_Sup': bb_up,
        'BB_Med': bb_mid,
        'BB_Inf': bb_low,
        'CRSI': crsi,
        'EMA_9': emas['EMA_9'],
        'EMA_21': emas['EMA_21'],
        'EMA_55': emas['EMA_55']
    }).round(4)
    
    print("\n" + "="*80)
    print(" 🔬 LABORATORIO TÉCNICO - YPFD (Últimos 3 días) ".center(80))
    print("="*80)
    print(resultados.tail(3).to_string())
    print("="*80)
    print("Misión FASE 2: Abrir Investing.com, cargar EMA 9, 21 y 55")
    print("y verificar que los valores del último día cuadren perfectamente.")
else:
    print("No se pudieron cargar los datos.")