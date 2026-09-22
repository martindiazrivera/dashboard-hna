import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Cierres Mensuales | Balanz", page_icon="📅", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .cierre-card {
            background-color: #f8fafc !important; 
            border: 1px solid #e2e8f0 !important; 
            border-radius: 8px !important;
            padding: 16px !important; 
            margin-bottom: 16px !important; 
            display: flex !important; 
            justify-content: space-between !important;
            align-items: center !important;
        }
        .cierre-col { display: flex !important; flex-direction: column !important; }
        
        .cierre-label { font-size: 11px !important; font-weight: 700 !important; color: #64748b !important; text-transform: uppercase !important; letter-spacing: 0.5px !important;}
        
        .cierre-val { font-size: 18px !important; font-weight: 700 !important; color: #0f172a !important; margin-top: 4px !important;}
        
        .val-green { color: #059669 !important; }
        .val-red { color: #dc2626 !important; }
        .streamlit-expanderHeader { font-weight: 600 !important; font-size: 15px !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📅 Cierres Mensuales (Monthly Statements)")
st.markdown("Auditoría histórica agrupada mes a mes: Operaciones, P&L Realizado (Swings cerrados) y Flujo de Caja neto.")

def formato_arg(valor, decimales=2):
    if pd.isna(valor) or valor == "": return "$ 0,00"
    try:
        return f"$ {float(valor):,.{decimales}f}".translate(str.maketrans(',.', '.,'))
    except:
        return "$ 0,00"

def color_rendimiento(val):
    if isinstance(val, str): return ''
    try:
        color = '#10b981' if float(val) > 0 else '#ef4444' if float(val) < 0 else '#6b7280'
        return f'color: {color}; font-weight: 600;'
    except:
        return ''

def obtener_columna_fecha(df, posibles_nombres):
    for col in df.columns:
        col_limpia = col.strip().lower()
        for candidato in posibles_nombres:
            if candidato.strip().lower() in col_limpia:
                return col
    return None

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    
    # Cargamos las bases crudas del motor
    df_boletos = pd.read_excel(ruta, sheet_name="Historial_Bruto")
    df_fifo = pd.read_excel(ruta, sheet_name="Operaciones_Cerradas_FIFO")
    
    try:
        df_caja = pd.read_excel(ruta, sheet_name="Flujo_Caja")
    except:
        df_caja = pd.DataFrame()

    # Preparar Fechas de forma DEFENSIVA y PRECISA
    if not df_boletos.empty:
        col_f = obtener_columna_fecha(df_boletos, ['fecha_norm', 'concertacion', 'fecha'])
        if col_f:
            df_boletos[col_f] = pd.to_datetime(df_boletos[col_f], errors='coerce')
            df_boletos['Periodo'] = df_boletos[col_f].dt.strftime('%Y-%m').fillna('Desconocido')
        else:
            df_boletos['Periodo'] = 'Desconocido'
    
    if not df_fifo.empty:
        # BUSQUEDA ESTRICTA: Obligamos a que use la Fecha de VENTA para asignar la ganancia al mes correcto
        col_f_venta = None
        for c in df_fifo.columns:
            if 'venta' in c.lower() and 'fecha' in c.lower():
                col_f_venta = c
                break
        
        if col_f_venta:
            df_fifo[col_f_venta] = pd.to_datetime(df_fifo[col_f_venta], errors='coerce')
            df_fifo['Periodo'] = df_fifo[col_f_venta].dt.strftime('%Y-%m').fillna('Desconocido')
        else:
            df_fifo['Periodo'] = 'Desconocido'
            
    if not df_caja.empty:
        col_f = obtener_columna_fecha(df_caja, ['fecha', 'concertacion'])
        if col_f:
            df_caja[col_f] = pd.to_datetime(df_caja[col_f], errors='coerce')
            df_caja['Periodo'] = df_caja[col_f].dt.strftime('%Y-%m').fillna('Desconocido')
        else:
            df_caja['Periodo'] = 'Desconocido'

    # Obtener todos los meses únicos
    periodos_boletos = df_boletos['Periodo'].unique().tolist() if (not df_boletos.empty and 'Periodo' in df_boletos.columns) else []
    periodos_fifo = df_fifo['Periodo'].unique().tolist() if (not df_fifo.empty and 'Periodo' in df_fifo.columns) else []
    periodos_caja = df_caja['Periodo'].unique().tolist() if (not df_caja.empty and 'Periodo' in df_caja.columns) else []
    
    todos_los_periodos = sorted(list(set(periodos_boletos + periodos_fifo + periodos_caja)), reverse=True)
    
    if 'Desconocido' in todos_los_periodos:
        todos_los_periodos.remove('Desconocido')

    if not todos_los_periodos:
        st.info("No hay datos históricos para generar cierres mensuales.")
    else:
        for index, periodo in enumerate(todos_los_periodos):
            mes_boletos = df_boletos[df_boletos['Periodo'] == periodo].copy() if (not df_boletos.empty and 'Periodo' in df_boletos.columns) else pd.DataFrame()
            mes_fifo = df_fifo[df_fifo['Periodo'] == periodo].copy() if (not df_fifo.empty and 'Periodo' in df_fifo.columns) else pd.DataFrame()
            
            if not mes_boletos.empty and 'Tipo' in mes_boletos.columns and 'Neto' in mes_boletos.columns:
                total_comprado = abs(mes_boletos[mes_boletos['Tipo'].str.upper() == 'COMPRA']['Neto'].sum())
                total_vendido = abs(mes_boletos[mes_boletos['Tipo'].str.upper() == 'VENTA']['Neto'].sum())
            else:
                total_comprado = 0
                total_vendido = 0
                
            pnl_realizado_mes = mes_fifo['P&L Realizado ($)'].sum() if (not mes_fifo.empty and 'P&L Realizado ($)' in mes_fifo.columns) else 0

            titulo_expander = f"📅 CIERRE: {periodo} | P&L del Mes: {formato_arg(pnl_realizado_mes)}"
            
            # El primer mes de la lista se abre por defecto
            with st.expander(titulo_expander, expanded=(index == 0)):
                st.markdown(f"""
                <div class="cierre-header">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <div class="metric-label">Total Invertido (Compras)</div>
                            <div class="metric-value">{formato_arg(total_comprado)}</div>
                        </div>
                        <div>
                            <div class="metric-label">Total Liquidado (Ventas)</div>
                            <div class="metric-value">{formato_arg(total_vendido)}</div>
                        </div>
                        <div>
                            <div class="metric-label">Ganancia Realizada (FIFO)</div>
                            <div class="metric-value {'green' if pnl_realizado_mes >= 0 else 'red'}">{formato_arg(pnl_realizado_mes)}</div>
                        </div>
                        <div>
                            <div class="metric-label">Operaciones (Tickets)</div>
                            <div class="metric-value">{len(mes_boletos)}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                tab1, tab2 = st.tabs(["🧾 Operaciones del Mes", "📈 Swings Cerrados (Ganancia)"])
                
                with tab1:
                    if not mes_boletos.empty:
                        c_f = obtener_columna_fecha(mes_boletos, ['fecha_norm', 'concertacion', 'fecha'])
                        c_t = obtener_columna_fecha(mes_boletos, ['ticker_norm', 'ticker', 'especie'])
                        c_tipo = obtener_columna_fecha(mes_boletos, ['tipo', 'operacion'])
                        c_cant = obtener_columna_fecha(mes_boletos, ['cantidad'])
                        c_pre = obtener_columna_fecha(mes_boletos, ['precio_real', 'precio operado', 'precio'])
                        c_neto = obtener_columna_fecha(mes_boletos, ['neto', 'monto'])
                        
                        cols_disponibles = [c for c in [c_f, c_t, c_tipo, c_cant, c_pre, c_neto] if c is not None]
                        vista_bol = mes_boletos[cols_disponibles].copy()
                        
                        if c_f: vista_bol[c_f] = vista_bol[c_f].dt.strftime('%Y-%m-%d')
                        
                        format_dict = {}
                        if c_cant: format_dict[c_cant] = "{:,.2f}"
                        if c_pre: format_dict[c_pre] = formato_arg
                        if c_neto: format_dict[c_neto] = formato_arg
                            
                        st.dataframe(vista_bol.style.format(format_dict), hide_index=True, use_container_width=True)
                    else:
                        st.write("No hubo compra/venta de activos en este mes.")
                        
                with tab2:
                    if not mes_fifo.empty:
                        cols_fifo = []
                        if 'Fecha Compra Origen' in mes_fifo.columns: cols_fifo.append('Fecha Compra Origen')
                        if 'Fecha Venta' in mes_fifo.columns: cols_fifo.append('Fecha Venta')
                        if 'Ticker' in mes_fifo.columns: cols_fifo.append('Ticker')
                        if 'Cantidad' in mes_fifo.columns: cols_fifo.append('Cantidad')
                        if 'Precio Compra Promedio' in mes_fifo.columns: cols_fifo.append('Precio Compra Promedio')
                        if 'Precio Venta Real' in mes_fifo.columns: cols_fifo.append('Precio Venta Real')
                        if 'P&L Realizado ($)' in mes_fifo.columns: cols_fifo.append('P&L Realizado ($)')
                        
                        vista_fifo = mes_fifo[cols_fifo].copy()
                        if 'Fecha Compra Origen' in vista_fifo.columns:
                            vista_fifo['Fecha Compra Origen'] = pd.to_datetime(vista_fifo['Fecha Compra Origen'], errors='coerce').dt.strftime('%Y-%m-%d')
                        if 'Fecha Venta' in vista_fifo.columns:
                            vista_fifo['Fecha Venta'] = pd.to_datetime(vista_fifo['Fecha Venta'], errors='coerce').dt.strftime('%Y-%m-%d')
                        
                        format_fifo = {}
                        if 'Cantidad' in vista_fifo.columns: format_fifo['Cantidad'] = "{:,.2f}"
                        if 'Precio Compra Promedio' in vista_fifo.columns: format_fifo['Precio Compra Promedio'] = formato_arg
                        if 'Precio Venta Real' in vista_fifo.columns: format_fifo['Precio Venta Real'] = formato_arg
                        if 'P&L Realizado ($)' in vista_fifo.columns: format_fifo['P&L Realizado ($)'] = formato_arg
                        
                        st.dataframe(
                            vista_fifo.style.map(color_rendimiento, subset=['P&L Realizado ($)'] if 'P&L Realizado ($)' in vista_fifo.columns else []).format(format_fifo), 
                            hide_index=True, use_container_width=True
                        )
                    else:
                        st.write("No se cerraron posiciones (sin P&L realizado) en este mes.")

except FileNotFoundError:
    st.warning("⚠️ No se encontró la base de datos. Ejecuta el Motor Cuantitativo primero.")
except Exception as e:
    st.error(f"❌ Error al cargar los cierres mensuales: {e}")