import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Mi Cartera | Balanz", page_icon="💼", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .balanz-card {
            background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            padding: 24px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .balanz-title { color: #4b5563; font-size: 16px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;}
        .balanz-total { font-size: 32px; font-weight: 700; color: #111827; margin-bottom: 4px;}
        .balanz-sub { font-size: 14px; color: #10b981; font-weight: 600; background-color: #d1fae5; padding: 4px 8px; border-radius: 4px; display: inline-block;}
        .balanz-sub-rojo { font-size: 14px; color: #ef4444; font-weight: 600; background-color: #fee2e2; padding: 4px 8px; border-radius: 4px; display: inline-block;}
        .tc-text { color: #9ca3af; font-size: 12px; margin-top: 15px; }
        
        .streamlit-expanderHeader { font-weight: 600 !important; font-size: 16px !important; color: #111827 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("💼 Estado de Cartera (Gestión Avanzada)")

def formato_arg(valor, decimales=2):
    if pd.isna(valor): return "$ 0,00"
    return f"$ {float(valor):,.{decimales}f}".translate(str.maketrans(',.', '.,'))

def color_rendimiento(val):
    if isinstance(val, str): return ''
    color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#6b7280'
    return f'color: {color}; font-weight: 600;'

def color_estado(val):
    if '✅' in str(val): return 'color: #10b981; font-weight: 600;'
    if '❌' in str(val): return 'color: #ef4444; font-weight: 600;'
    return ''

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    
    # Cargamos los datos limpios
    df = pd.read_excel(ruta, sheet_name="Tenencia_Actual")
    df_lotes = pd.read_excel(ruta, sheet_name="Lotes_Abiertos")
    df_ventas = pd.read_excel(ruta, sheet_name="Operaciones_Cerradas_FIFO")
    df_macro = pd.read_excel(ruta, sheet_name="Macro_Benchmark").set_index('Metrica')
    
    # Separación de liquidez e inversiones
    df_liquidez = df[df['Ticker'] == 'PESOS LÍQUIDOS']
    df_inversiones = df[df['Ticker'] != 'PESOS LÍQUIDOS']
    
    liquidez_total = df_liquidez['Cantidad en Tenencia'].sum() if not df_liquidez.empty else 0
    capital_invertido = df_inversiones['Tenencia Total Valuada'].sum() if not df_inversiones.empty else 0
    total_cartera = capital_invertido + liquidez_total
    
    ganancia_total = df_inversiones['Ganancia/Perdida NO Realizada ($)'].sum() if not df_inversiones.empty else 0
    inversion_original = df_inversiones['Total Invertido ARS'].sum() if not df_inversiones.empty else 0
    porc_ganancia = (ganancia_total / inversion_original) * 100 if inversion_original > 0 else 0
    
    clase_badge = "balanz-sub" if ganancia_total >= 0 else "balanz-sub-rojo"
    signo = "+" if ganancia_total > 0 else ""

    # Usamos 3 columnas para el nuevo diseño del panel principal
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">👁️ Total Cartera (Valuación ARS)</div>
            <div class="balanz-total">{formato_arg(total_cartera)}</div>
            <div class="{clase_badge}">{signo}{formato_arg(ganancia_total)} ({signo}{porc_ganancia:.2f}%)</div>
            <div class="tc-text">Suma del capital de riesgo y la liquidez libre en vivo.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        pnl_realizado = df_macro.loc['Total P&L Realizado', 'Valor'] if 'Total P&L Realizado' in df_macro.index else 0
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">📈 Rendimiento Histórico Cerrado</div>
            <div class="balanz-total">{formato_arg(pnl_realizado)}</div>
            <div class="tc-text">Ganancia neta (cash) asegurada en cuenta por ventas anteriores.</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="balanz-card">
            <div class="balanz-title">💵 Poder de Fuego (Liquidez)</div>
            <div class="balanz-total">{formato_arg(liquidez_total)}</div>
            <div class="tc-text">Pesos libres listos para ser operados o retirados.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#111827;'>📈 Mis instrumentos (Análisis por Lotes FIFO)</h3>", unsafe_allow_html=True)
    st.markdown("Despliega cada instrumento para analizar posiciones abiertas e historial de ventas.")
    
    if df_inversiones.empty:
        st.info("No tienes posiciones de riesgo (Acciones/Cedears) abiertas en este momento.")
    else:
        for index, row in df_inversiones.iterrows():
            ticker = row['Ticker']
            cant = row['Cantidad en Tenencia']
            precio_act = row['Valor Mercado Actual']
            pnl_total = row['Ganancia/Perdida NO Realizada ($)']
            
            icono = "🟢" if pnl_total >= 0 else "🔴"
            
            with st.expander(f"{icono} {ticker} | {cant:,.2f} Nominales | P&L Consolidado: {formato_arg(pnl_total)}"):
                
                # --- TABLA 1: LOTES ACTIVOS (CON SEMÁFORO DE VENTA) ---
                st.markdown("##### 📌 Posición Viva (Lotes Actuales)")
                lotes_tk = df_lotes[df_lotes['Ticker'] == ticker].copy()
                
                if not lotes_tk.empty:
                    lotes_tk['Cotización Actual'] = precio_act
                    lotes_tk['Valuación Actual'] = lotes_tk['Cantidad Viva'] * precio_act
                    lotes_tk['P&L del Lote'] = lotes_tk['Valuación Actual'] - lotes_tk['Capital Asignado']
                    lotes_tk['Rendimiento (%)'] = (lotes_tk['P&L del Lote'] / lotes_tk['Capital Asignado']) * 100
                    
                    # Semáforo de Venta: Verifica si el precio actual superó el breakeven de salida
                    lotes_tk['Estado Venta'] = np.where(
                        lotes_tk['Cotización Actual'] > lotes_tk['Breakeven Salida'], 
                        '✅ Habilitada', 
                        '❌ No conveniente'
                    )
                    
                    lotes_vista = lotes_tk[[
                        'Fecha de Compra', 'Cantidad Viva', 'Precio Operado', 
                        'Comisión Unitaria', 'Costo Real (Entrada)', 'Breakeven Salida', 
                        'Cotización Actual', 'Estado Venta', 'P&L del Lote', 'Rendimiento (%)'
                    ]].copy()
                    
                    lotes_vista['Fecha de Compra'] = pd.to_datetime(lotes_vista['Fecha de Compra']).dt.strftime('%Y-%m-%d')
                    
                    st.dataframe(
                        lotes_vista.style.map(color_rendimiento, subset=['P&L del Lote', 'Rendimiento (%)'])
                                         .map(color_estado, subset=['Estado Venta'])
                                         .format({
                                             'Cantidad Viva': lambda x: f"{x:,.2f}",
                                             'Precio Operado': formato_arg,
                                             'Comisión Unitaria': formato_arg,
                                             'Costo Real (Entrada)': formato_arg,
                                             'Breakeven Salida': formato_arg,
                                             'Cotización Actual': formato_arg,
                                             'P&L del Lote': formato_arg,
                                             'Rendimiento (%)': lambda x: f"{x:,.2f} %"
                                         }),
                        hide_index=True, use_container_width=True
                    )
                else:
                    st.write("No hay detalle de lotes para este activo (Fondo o Fondeo directo).")

                # --- TABLA 2: VENTAS (TRAZABILIDAD Y SEMÁFORO DE RECOMPRA) ---
                if not df_ventas.empty and ticker in df_ventas['Ticker'].values:
                    st.markdown("##### 💸 Historial de Ventas (Trazabilidad y Recompra)")
                    ventas_tk = df_ventas[df_ventas['Ticker'] == ticker].copy()
                    
                    ventas_tk.rename(columns={
                        'Cantidad': 'Cantidad Vendida',
                        'Precio Compra Promedio': 'Costo Real (Entrada)'
                    }, inplace=True)
                    
                    tasa_friccion = 0.01 
                    
                    ventas_tk['Precio Operado (Compra)'] = ventas_tk['Costo Real (Entrada)'] / (1 + tasa_friccion)
                    ventas_tk['Breakeven Salida Histórico'] = ventas_tk['Costo Real (Entrada)'] / (1 - tasa_friccion)
                    ventas_tk['Precio Máximo Recompra'] = ventas_tk['Precio Venta Real'] * (1 - (tasa_friccion * 2))

                    ventas_tk['Estado Recompra'] = np.where(
                        precio_act < ventas_tk['Precio Máximo Recompra'], 
                        '✅ Habilitada', 
                        '❌ No conveniente'
                    )

                    ventas_tk['Fecha Venta'] = pd.to_datetime(ventas_tk['Fecha Venta'])
                    ventas_tk = ventas_tk.sort_values(by='Fecha Venta', ascending=False)
                    
                    ventas_tk['Fecha Venta'] = ventas_tk['Fecha Venta'].dt.strftime('%Y-%m-%d')
                    
                    if 'Fecha Compra Origen' in ventas_tk.columns:
                        ventas_tk['Fecha Compra Origen'] = pd.to_datetime(ventas_tk['Fecha Compra Origen']).dt.strftime('%Y-%m-%d')

                    cols_vista = []
                    if 'Fecha Compra Origen' in ventas_tk.columns: cols_vista.append('Fecha Compra Origen')
                    
                    cols_vista.extend([
                        'Fecha Venta', 'Cantidad Vendida', 
                        'Precio Operado (Compra)', 'Costo Real (Entrada)', 
                        'Breakeven Salida Histórico', 'Precio Venta Real', 
                        'Precio Máximo Recompra', 'Estado Recompra', 'P&L Realizado ($)'
                    ])
                    
                    ventas_vista = ventas_tk[cols_vista].copy()
                    
                    st.dataframe(
                        ventas_vista.style.map(color_rendimiento, subset=['P&L Realizado ($)'])
                                          .map(color_estado, subset=['Estado Recompra'])
                                          .format({
                                              'Cantidad Vendida': lambda x: f"{x:,.2f}",
                                              'Precio Operado (Compra)': formato_arg,
                                              'Costo Real (Entrada)': formato_arg,
                                              'Breakeven Salida Histórico': formato_arg,
                                              'Precio Venta Real': formato_arg,
                                              'Precio Máximo Recompra': formato_arg,
                                              'P&L Realizado ($)': formato_arg
                                          }),
                        hide_index=True, use_container_width=True
                    )
                    
                    st.info(f"💡 **Estado Recompra:** Compara la cotización actual (**{formato_arg(precio_act)}**) con el Precio Máximo de Recompra permitido para asegurar un swing positivo.")

except FileNotFoundError:
    st.warning("⚠️ No se encontró la base de datos. Ejecuta el Motor Cuantitativo primero.")
except Exception as e:
    st.error(f"❌ Error al cargar la interfaz: {e}")