import streamlit as st
import pandas as pd
import numpy as np
import os
import requests

st.set_page_config(page_title="Benchmark | Balanz", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        .bench-card {
            background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            padding: 20px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        }
        .bench-winner {
            background-color: #f0fdf4; border: 2px solid #10b981; border-radius: 12px;
            padding: 20px; height: 100%; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15); text-align: center;
            transform: scale(1.02);
        }
        .bench-title { color: #6b7280; font-size: 14px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;}
        .bench-val { font-size: 32px; font-weight: 800; color: #111827; margin-bottom: 8px;}
        .bench-vs { font-size: 14px; font-weight: 600; padding: 4px 8px; border-radius: 4px; display: inline-block;}
        .green-badge { background-color: #d1fae5; color: #047857; }
        .red-badge { background-color: #fee2e2; color: #b91c1c; }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Benchmark de Mercado (Costo de Oportunidad)")
st.markdown("¿Qué hubiera pasado si en vez de operar en Balanz, ponías cada peso en Dólares o Plazos Fijos UVA el mismo día que lo fondeaste?")

def formato_arg(valor):
    if pd.isna(valor): return "$ 0,00"
    return f"$ {float(valor):,.2f}".translate(str.maketrans(',.', '.,'))

# 1. Función con Caché para traer todas las APIs Históricas rápido
@st.cache_data(ttl=3600, show_spinner="Descargando bases históricas del BCRA y BYMA...")
def descargar_datos_historicos():
    try:
        # Dólar MEP
        mep = requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa", timeout=10).json()
        df_mep = pd.DataFrame(mep)
        df_mep['fecha'] = pd.to_datetime(df_mep['fecha'])
        df_mep = df_mep.set_index('fecha').resample('D').ffill()['venta']
        
        # Inflación / Plazo Fijo UVA (Usamos el índice UVA que refleja inflación diaria exacta)
        uva = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/uva", timeout=10).json()
        df_uva = pd.DataFrame(uva)
        df_uva['fecha'] = pd.to_datetime(df_uva['fecha'])
        df_uva = df_uva.set_index('fecha').resample('D').ffill()['valor']
        
        return df_mep, df_uva
    except Exception as e:
        st.error("Error de conexión a las APIs públicas.")
        return None, None

try:
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(dir_actual, "../../data/Reporte_Avanzado_Cartera.xlsx")
    
    df_tenencia = pd.read_excel(ruta, sheet_name="Tenencia_Actual")
    df_caja = pd.read_excel(ruta, sheet_name="Flujo_Caja")
    
    valuacion_actual_cartera = df_tenencia['Tenencia Total Valuada'].sum() if not df_tenencia.empty else 0
    
    df_mep, df_uva = descargar_datos_historicos()
    
    if df_mep is not None and df_uva is not None and not df_caja.empty:
        
        mep_hoy = df_mep.iloc[-1]
        uva_hoy = df_uva.iloc[-1]
        
        # Simulación Histórica Vectorizada
        usd_acumulados = 0.0
        uvas_acumulados = 0.0
        capital_neto_nominal = 0.0
        
        df_caja['Fecha_Sim'] = pd.to_datetime(df_caja['Concertacion'] if 'Concertacion' in df_caja.columns else df_caja.columns[0]).dt.normalize()
        
        for index, row in df_caja.iterrows():
            fecha = row['Fecha_Sim']
            monto = float(row.get('Importe', row.get('Monto', 0)))
            moneda = str(row.get('Moneda', 'PESOS')).upper()
            
            # Buscar cotización del día (o la última disponible)
            precio_mep_dia = df_mep.get(fecha, df_mep.asof(fecha))
            precio_uva_dia = df_uva.get(fecha, df_uva.asof(fecha))
            
            if pd.isna(precio_mep_dia): precio_mep_dia = mep_hoy
            if pd.isna(precio_uva_dia): precio_uva_dia = uva_hoy
            
            # Unificar todo a pesos del día para la simulación
            monto_ars_dia = monto if 'PESOS' in moneda else (monto * precio_mep_dia)
            
            capital_neto_nominal += monto_ars_dia
            
            # SIMULACIÓN 1: Comprar/Vender Dólar MEP
            usd_acumulados += (monto_ars_dia / precio_mep_dia)
            
            # SIMULACIÓN 2: Comprar/Vender Plazo Fijo UVA (Inflación)
            uvas_acumulados += (monto_ars_dia / precio_uva_dia)
            
        # VALUACIONES FINALES HOY
        valuacion_mep = usd_acumulados * mep_hoy
        valuacion_uva = uvas_acumulados * uva_hoy
        
        # Determinar al ganador
        escenarios = {
            "Tu Cartera Balanz": valuacion_actual_cartera,
            "Colchón Dólar MEP": valuacion_mep,
            "Plazo Fijo UVA (Inflación)": valuacion_uva
        }
        ganador = max(escenarios, key=escenarios.get)

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        
        # TARJETA 1: DÓLAR MEP
        dif_mep = valuacion_actual_cartera - valuacion_mep
        pct_mep = (dif_mep / valuacion_mep) * 100 if valuacion_mep > 0 else 0
        clase_mep_bdg = "green-badge" if dif_mep >= 0 else "red-badge"
        txt_mep = f"{'+' if dif_mep>=0 else ''}{formato_arg(dif_mep)} ({pct_mep:,.2f}%) vs Tu Cartera"
        
        with c1:
            st.markdown(f"""
            <div class="{'bench-winner' if ganador == 'Colchón Dólar MEP' else 'bench-card'}">
                <div class="bench-title">💵 Si comprabas Dólar MEP</div>
                <div class="bench-val">{formato_arg(valuacion_mep)}</div>
                <div class="bench-vs {clase_mep_bdg}">{txt_mep}</div>
                <p style="font-size: 12px; color: #9ca3af; margin-top: 10px;">Comprando y reteniendo USD con cada fondeo al tipo de cambio de ese día.</p>
            </div>
            """, unsafe_allow_html=True)

        # TARJETA 2: TU CARTERA (EL TRADER)
        with c2:
            st.markdown(f"""
            <div class="{'bench-winner' if ganador == 'Tu Cartera Balanz' else 'bench-card'}" style="border-color: #3b82f6;">
                <div class="bench-title" style="color: #2563eb;">🧠 Tu Cartera Actual</div>
                <div class="bench-val" style="color: #1e3a8a;">{formato_arg(valuacion_actual_cartera)}</div>
                <div class="bench-vs" style="background-color: #dbeafe; color: #1e40af;">Capital Real Protegido</div>
                <p style="font-size: 12px; color: #9ca3af; margin-top: 10px;">Tu patrimonio actual operando acciones y cedears.</p>
            </div>
            """, unsafe_allow_html=True)

        # TARJETA 3: INFLACIÓN / UVA
        dif_uva = valuacion_actual_cartera - valuacion_uva
        pct_uva = (dif_uva / valuacion_uva) * 100 if valuacion_uva > 0 else 0
        clase_uva_bdg = "green-badge" if dif_uva >= 0 else "red-badge"
        txt_uva = f"{'+' if dif_uva>=0 else ''}{formato_arg(dif_uva)} ({pct_uva:,.2f}%) vs Tu Cartera"
        
        with c3:
            st.markdown(f"""
            <div class="{'bench-winner' if ganador == 'Plazo Fijo UVA (Inflación)' else 'bench-card'}">
                <div class="bench-title">📈 Si hacías Plazo Fijo UVA</div>
                <div class="bench-val">{formato_arg(valuacion_uva)}</div>
                <div class="bench-vs {clase_uva_bdg}">{txt_uva}</div>
                <p style="font-size: 12px; color: #9ca3af; margin-top: 10px;">Atando cada peso fondeado a la inflación exacta del país (Índice CER/UVA).</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # GRÁFICO COMPARATIVO
        st.markdown("### 📊 Gráfico de Rendimiento Comparativo")
        df_chart = pd.DataFrame({
            "Estrategia": ["Colchón Dólar MEP", "Plazo Fijo UVA (Inflación)", "Tu Cartera (Gestión Activa)"],
            "Valuación Final (ARS)": [valuacion_mep, valuacion_uva, valuacion_actual_cartera]
        }).set_index("Estrategia")
        
        st.bar_chart(df_chart, height=400)
        
        st.info(f"💡 **Veredicto del Motor:** El ganador histórico de tu capital es **{ganador}**. Tu capital inicial puro aportado fue de {formato_arg(capital_neto_nominal)}.")

    else:
        st.warning("Faltan datos en la base de Caja. Ejecuta el Motor Cuantitativo.")

except Exception as e:
    st.error(f"❌ Error al procesar el benchmark: {e}")