import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Actividad | Balanz", page_icon="🧾", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

st.title("🧾 Historial de Actividad")

# Formateador robusto
def formato_arg(valor):
    if pd.isna(valor) or valor == '': return "$ 0,00"
    return f"$ {float(valor):,.2f}".translate(str.maketrans(',.', '.,'))

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    df = pd.read_excel(ruta, sheet_name="Historial_Bruto")
    
    # Categorización dinámica extendida
    def categorizar_instrumento(ticker):
        t = str(ticker).upper().strip()
        if t in ['AL30', 'GD30', 'AL30D', 'GD30D', 'AL30C']: return '🏛️ BONO'
        if t == 'BCMMA': return '📈 FONDO'
        
        cedears = ['MELI', 'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMD', 'SPY', 'QQQ', 'KO', 'AMZN']
        acciones = ['YPFD', 'PAMP', 'EDN', 'GGAL', 'BMA', 'TRAN', 'ALUA', 'CEPU', 'TGSU2', 'LOMA']
        
        if t in cedears: return '🌎 CEDEAR'
        if t in acciones: return '🇦🇷 ACCIÓN'
        return '🔄 OTRO'

    col_ticker = 'Ticker_Norm' if 'Ticker_Norm' in df.columns else 'Ticker'
    if col_ticker in df.columns:
        df['Instrumento'] = df[col_ticker].apply(categorizar_instrumento)
        df['Ticker'] = df[col_ticker] # Unificamos la vista

    # Renombrado seguro
    renombres = {
        'Concertacion': '📅 Fecha',
        'Bruto': '💰 Monto Bruto',
        'Costos Mercado': '🏛️ Impuestos',
        'Arancel': '🤝 Comisión',
        'Neto': '✅ Monto Final'
    }
    df_renombrado = df.rename(columns={k: v for k, v in renombres.items() if k in df.columns})

    # Aseguramos formato fecha
    if '📅 Fecha' in df_renombrado.columns:
        df_renombrado['📅 Fecha'] = pd.to_datetime(df_renombrado['📅 Fecha'])

    # Filtramos columnas que realmente existen
    cols_base = ['📅 Fecha', 'Instrumento', 'Ticker', 'Tipo', 'Cantidad', 'Precio', '💰 Monto Bruto', '🏛️ Impuestos', '🤝 Comisión', '✅ Monto Final']
    columnas_visibles = [c for c in cols_base if c in df_renombrado.columns]
    df_final = df_renombrado[columnas_visibles].copy()

    # --- PANEL DE FILTROS AVANZADOS ---
    st.sidebar.header("🔍 Filtros Avanzados")
    
    if '📅 Fecha' in df_final.columns:
        min_date = df_final['📅 Fecha'].min().date()
        max_date = df_final['📅 Fecha'].max().date()
        fechas = st.sidebar.date_input("📅 Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        if len(fechas) == 2:
            df_final = df_final[(df_final['📅 Fecha'].dt.date >= fechas[0]) & (df_final['📅 Fecha'].dt.date <= fechas[1])]

    st.sidebar.markdown("---")
    if 'Tipo' in df_final.columns:
        filtro_tipo = st.sidebar.multiselect("Operación", options=df_final['Tipo'].unique())
        if filtro_tipo: df_final = df_final[df_final['Tipo'].isin(filtro_tipo)]
        
    filtro_inst = st.sidebar.multiselect("Categoría", options=df_final['Instrumento'].unique())
    filtro_ticker = st.sidebar.text_input("Buscar Ticker", placeholder="Ej: NVDA, YPFD")

    if filtro_inst: df_final = df_final[df_final['Instrumento'].isin(filtro_inst)]
    if filtro_ticker: df_final = df_final[df_final['Ticker'].str.contains(filtro_ticker.upper(), na=False)]

    st.sidebar.markdown("---")
    orden = st.sidebar.selectbox("🔃 Ordenar Tabla", ["Fecha (Más reciente)", "Fecha (Más antigua)", "Monto Final (Mayor a menor)"])
    
    if orden == "Fecha (Más reciente)" and '📅 Fecha' in df_final.columns: 
        df_final = df_final.sort_values(by='📅 Fecha', ascending=False)
    elif orden == "Fecha (Más antigua)" and '📅 Fecha' in df_final.columns: 
        df_final = df_final.sort_values(by='📅 Fecha', ascending=True)
    elif orden == "Monto Final (Mayor a menor)" and '✅ Monto Final' in df_final.columns: 
        df_final = df_final.sort_values(by='✅ Monto Final', ascending=False, key=abs)

    # Renderizado final
    if '📅 Fecha' in df_final.columns:
        # CORRECCIÓN: Formato YYYY-MM-DD para mantener el ordenamiento nativo en la tabla
        df_final['📅 Fecha'] = df_final['📅 Fecha'].dt.strftime('%Y-%m-%d')

    cols_moneda = [c for c in ['Precio', '💰 Monto Bruto', '🏛️ Impuestos', '🤝 Comisión', '✅ Monto Final'] if c in df_final.columns]
    format_dict = {col: formato_arg for col in cols_moneda}
    
    st.dataframe(
        df_final.style.format(format_dict),
        use_container_width=True,
        hide_index=True,
        height=600
    )

except FileNotFoundError:
    st.warning("⚠️ Ejecuta el Motor Cuantitativo para generar la base de datos de actividades.")
except Exception as e:
    st.error(f"❌ Error al cargar la actividad: {e}")