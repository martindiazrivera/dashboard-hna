import pandas as pd
import numpy as np
import os
import warnings
import requests

warnings.filterwarnings('ignore')

class MotorCuantitativo:
    def __init__(self):
        # Ubicación absoluta basada en este archivo (src/utils/motor_cuantitativo.py)
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        
        # Apuntamos directamente a mi_cartera_balanz/data/ subiendo dos niveles desde utils/
        ruta_base_proyecto = os.path.abspath(os.path.join(dir_actual, "../../data"))
        
        # Si por estructura de despliegue la carpeta data está en la raíz de ejecución:
        if os.path.exists(os.path.join(ruta_base_proyecto, "boletos.xlsx")):
            self.data_dir = ruta_base_proyecto
        else:
            # Rutas de respaldo por si Streamlit corre desde la raíz del repo
            posibles = ["data", "mi_cartera_balanz/data", "../data", "../../data"]
            self.data_dir = "data"
            for p in posibles:
                if os.path.exists(os.path.join(p, "boletos.xlsx")):
                    self.data_dir = p
                    break

        self.ruta_boletos = os.path.join(self.data_dir, "boletos.xlsx")
        self.ruta_movimientos = os.path.join(self.data_dir, "movimientos.xlsx")
        self.ruta_cta_cte = os.path.join(self.data_dir, "cuentacorriente.xlsx")
        self.ruta_ordenes = os.path.join(self.data_dir, "ordenes.xlsx")
        self.ruta_salida = os.path.join(self.data_dir, "Reporte_Avanzado_Cartera.xlsx")
        
        self.df_boletos = pd.DataFrame()
        self.df_movimientos = pd.DataFrame()
        self.df_cta_cte = pd.DataFrame()
        self.df_ordenes = pd.DataFrame()

    def obtener_columna_flexible(self, df, posibles_nombres):
        for col in df.columns:
            col_limpia = col.strip().lower()
            for candidato in posibles_nombres:
                if candidato.strip().lower() in col_limpia:
                    return col
        return None

    def obtener_dolar_mep_historico(self):
        # Usamos una API pública argentina para traer la serie histórica del MEP
        url = "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            df_dolar = pd.DataFrame(data)
            # Convertimos a datetime y rellenamos fines de semana (ffill)
            df_dolar['fecha'] = pd.to_datetime(df_dolar['fecha'])
            df_dolar.set_index('fecha', inplace=True)
            df_dolar = df_dolar.resample('D').ffill()
            return df_dolar['venta']
        except:
            print("⚠️ No se pudo conectar a la API del dólar histórico. Se usará un valor por defecto.")
            return None

    def cargar_datos_crudos(self):
        try:
            if os.path.exists(self.ruta_boletos):
                self.df_boletos = pd.read_excel(self.ruta_boletos)
                self.df_boletos.columns = self.df_boletos.columns.str.strip()
            
            if os.path.exists(self.ruta_movimientos):
                self.df_movimientos = pd.read_excel(self.ruta_movimientos)
                self.df_movimientos.columns = self.df_movimientos.columns.str.strip()
                
            if os.path.exists(self.ruta_cta_cte):
                self.df_cta_cte = pd.read_excel(self.ruta_cta_cte)
                self.df_cta_cte.columns = self.df_cta_cte.columns.str.strip()
            
            if os.path.exists(self.ruta_ordenes):
                self.df_ordenes = pd.read_excel(self.ruta_ordenes)
                self.df_ordenes.columns = self.df_ordenes.columns.str.strip()
                
            return True
        except Exception as e:
            print(f"❌ Error al cargar Excel: {e}")
            return False

    def procesar_cashflow(self):
        try:
            if not self.df_cta_cte.empty:
                col_saldo = self.obtener_columna_flexible(self.df_cta_cte, ['Saldo'])
                if col_saldo:
                    return float(self.df_cta_cte.iloc[-1][col_saldo])
        except: pass
        return 0.0

    def limpiar_y_ajustar_boletos(self):
        df = self.df_boletos.copy()
        if df.empty: return
        
        col_fecha = self.obtener_columna_flexible(df, ['Concertación', 'Concertacion', 'Fecha'])
        if col_fecha:
            df['Fecha_Norm'] = pd.to_datetime(df[col_fecha], errors='coerce')
            
        def normalizar_ticker(t):
            t = str(t).strip().upper()
            if t in ['AL30D', 'AL30C']: return 'AL30'
            if t in ['GD30D', 'GD30C']: return 'GD30'
            if 'YPF' in t: return 'YPFD'
            if 'MELI' in t or 'MERCADOLIBRE' in t: return 'MELI'
            if 'NVDA' in t or 'NVIDIA' in t: return 'NVDA'
            if 'AAPL' in t or 'APPLE' in t: return 'AAPL'
            if 'MSFT' in t or 'MICROSOFT' in t: return 'MSFT'
            if 'SPY' in t or 'S&P' in t: return 'SPY'
            if 'BONO' in t and 'AL30' in t: return 'AL30'
            return t
            
        col_ticker = self.obtener_columna_flexible(df, ['Ticker', 'Simbolo', 'Especie'])
        if col_ticker:
            df['Ticker_Norm'] = df[col_ticker].apply(normalizar_ticker)
        else:
            df['Ticker_Norm'] = 'DESC'
            
        col_tipo = self.obtener_columna_flexible(df, ['Tipo'])
        if col_tipo:
            df = df[df[col_tipo].str.upper().isin(['COMPRA', 'VENTA'])].copy()
            
        for col in ['Cantidad', 'Precio', 'Bruto', 'Costos Mercado', 'Arancel', 'Neto']:
            col_enc = self.obtener_columna_flexible(df, [col])
            if col_enc:
                df[col] = pd.to_numeric(df[col_enc], errors='coerce').fillna(0)
            else:
                df[col] = 0

        df['Precio_Real'] = np.where(df['Precio'] <= 0, abs(df['Neto']) / df['Cantidad'], df['Precio'])
        df['Precio_Real'] = df['Precio_Real'].replace([np.inf, -np.inf], 0)

        orden_col = 'Fecha_Norm' if 'Fecha_Norm' in df.columns else df.columns[0]
        df['Peso_Orden'] = np.where(df['Tipo'].str.upper() == 'COMPRA', 0, 1)
        self.df_boletos = df.sort_values(by=[orden_col, 'Peso_Orden'], ascending=[True, True]).drop(columns=['Peso_Orden']).reset_index(drop=True)

    def calcular_inventario(self):
        inventario = {}  
        registro_ventas = [] 
        
        for index, row in self.df_boletos.iterrows():
            ticker = row.get('Ticker_Norm', 'OTRO')
            if pd.isna(ticker) or ticker in ['NAN', 'OTRO', 'DESC']: continue
            
            tipo = str(row.get('Tipo', '')).upper().strip()
            cantidad = float(row.get('Cantidad', 0))
            if cantidad <= 0: continue
            
            precio_puro = float(row.get('Precio_Real', 0))
            neto = float(row.get('Neto', 0))
            fecha = row.get('Fecha_Norm')
            moneda = row.get('Moneda', 'Pesos')
            
            factor_multiplicador = 1.0
            if ticker in ['AL30', 'GD30', 'AL30D', 'GD30D']:
                factor_multiplicador = 100.0  
                precio_puro = precio_puro / factor_multiplicador

            if ticker == 'YPFD' and precio_puro > 15000:
                factor_multiplicador = 10.0
                cantidad = cantidad * factor_multiplicador
                precio_puro = precio_puro / factor_multiplicador
            
            if ticker not in inventario:
                inventario[ticker] = []
                
            if tipo == 'COMPRA':
                costo_unitario = (abs(neto) / cantidad) if abs(neto) > 0 else precio_puro
                inventario[ticker].append({
                    'fecha_compra': fecha, 'cantidad_restante': cantidad,
                    'precio_puro': precio_puro, 'costo_unitario': costo_unitario, 'moneda': moneda
                })
            elif tipo == 'VENTA':
                cant_a_vender = cantidad
                ingreso_unitario = (abs(neto) / cantidad) if abs(neto) > 0 else precio_puro
                stock_disp = sum([l['cantidad_restante'] for l in inventario[ticker]])
                if stock_disp < cant_a_vender:
                    faltante = cant_a_vender - stock_disp
                    inventario[ticker].insert(0, {
                        'fecha_compra': fecha, 'cantidad_restante': faltante,
                        'precio_puro': ingreso_unitario, 'costo_unitario': ingreso_unitario, 'moneda': moneda
                    })
                while cant_a_vender > 0 and len(inventario[ticker]) > 0:
                    lote = inventario[ticker][0]
                    cant_disponible = lote['cantidad_restante']
                    if cant_disponible <= cant_a_vender:
                        cant_vendida = cant_disponible
                        cant_a_vender -= cant_disponible
                        inventario[ticker].pop(0) 
                    else:
                        cant_vendida = cant_a_vender
                        inventario[ticker][0]['cantidad_restante'] -= cant_a_vender
                        cant_a_vender = 0
                        
                    registro_ventas.append({
                        'Fecha Compra Origen': lote['fecha_compra'], 
                        'Fecha Venta': fecha, 'Ticker': ticker, 'Moneda': moneda,
                        'Cantidad': cant_vendida, 'Precio Compra Promedio': lote['costo_unitario'],
                        'Precio Venta Real': ingreso_unitario,
                        'P&L Realizado ($)': (ingreso_unitario - lote['costo_unitario']) * cant_vendida
                    })

        df_mov = self.df_movimientos.copy()
        if not df_mov.empty:
            col_desc = self.obtener_columna_flexible(df_mov, ['Descripcion', 'Detalle'])
            if col_desc:
                subs = df_mov[df_mov[col_desc].astype(str).str.contains('Suscripción', case=False, na=False)]
                if not subs.empty:
                    inventario['BCMMA'] = [{
                        'fecha_compra': pd.to_datetime('today'),
                        'cantidad_restante': 160170.68,
                        'precio_puro': 2000000.0 / 160170.68,
                        'costo_unitario': 2000000.0 / 160170.68, 
                        'moneda': 'Pesos'
                    }]

        tenencia = []
        lotes_abiertos = []
        for ticker, lotes in inventario.items():
            cant_total = sum([l['cantidad_restante'] for l in lotes])
            if cant_total > 0:
                costo_total = sum([l['cantidad_restante'] * l['costo_unitario'] for l in lotes])
                tenencia.append({
                    'Ticker': ticker, 'Cantidad en Tenencia': cant_total,
                    'Valor de Compra Promedio': costo_total / cant_total,
                    'Total Invertido ARS': costo_total, 'Moneda Origen': lotes[0]['moneda']
                })
                for lote in lotes:
                    if lote['cantidad_restante'] > 0:
                        p_puro = lote['precio_puro']
                        c_unit = lote['costo_unitario']
                        tasa_comision = (c_unit / p_puro) - 1 if p_puro > 0 else 0
                        breakeven = c_unit / (1 - tasa_comision) if tasa_comision < 1 else c_unit
                        lotes_abiertos.append({
                            'Ticker': ticker, 'Fecha de Compra': lote['fecha_compra'],
                            'Cantidad Viva': lote['cantidad_restante'], 'Precio Operado': p_puro,
                            'Comisión Unitaria': c_unit - p_puro, 'Costo Real (Entrada)': c_unit,
                            'Breakeven Salida': breakeven, 'Capital Asignado': lote['cantidad_restante'] * c_unit
                        })
        return pd.DataFrame(tenencia), pd.DataFrame(registro_ventas), pd.DataFrame(lotes_abiertos)

    def obtener_precio_historico(self, ticker):
        try:
            sub = self.df_boletos[self.df_boletos['Ticker_Norm'] == ticker]
            if not sub.empty: return float(sub.iloc[-1]['Precio_Real'])
        except: pass
        return 0.0

    def valuar_activos_yfinance(self, df_tenencia):
        if df_tenencia.empty: return df_tenencia
        tickers_cartera = df_tenencia['Ticker'].tolist()
        precios_vivos = {}

        print("🌐 Buscando precios locales (BYMA/BCBA)...")
        try:
            from tvDatafeed import TvDatafeed, Interval
            tv = TvDatafeed()
            for t in tickers_cartera:
                if t == 'BCMMA': 
                    precios_vivos[t] = 12.505889 
                    continue
                for exchange in ['BCBA', 'BYMA']:
                    try:
                        data = tv.get_hist(symbol=t, exchange=exchange, interval=Interval.in_daily, n_bars=1)
                        if data is not None and not data.empty:
                            p = float(data['close'].iloc[-1])
                            if t in ['AL30', 'GD30'] and p > 1000: p = p / 100.0
                            precios_vivos[t] = p
                            print(f"✅ Local OK: {t} -> $ {precios_vivos[t]}")
                            break 
                    except: pass
        except: pass

        tickers_cedears_faltantes = [t for t in tickers_cartera if t not in precios_vivos]
        if tickers_cedears_faltantes:
            print("🌐 Buscando precios de CEDEARs (Yahoo Finance)...")
            tickers_yf = [f"{t}.BA" for t in tickers_cedears_faltantes]
            try:
                import yfinance as yf
                data = yf.download(tickers_yf, period="1d", progress=False)
                if not data.empty:
                    for t, tk_yf in zip(tickers_cedears_faltantes, tickers_yf):
                        try:
                            if len(tickers_yf) == 1: p = float(data['Close'].iloc[-1])
                            else: p = float(data['Close'][tk_yf].iloc[-1])
                            if pd.notna(p) and p > 0:
                                precios_vivos[t] = p
                                print(f"✅ Cedear OK: {t} -> $ {precios_vivos[t]}")
                        except: pass
            except: pass

        precios_finales = []
        for index, row in df_tenencia.iterrows():
            t = row['Ticker']
            p = precios_vivos.get(t)
            if p is None or pd.isna(p) or p <= 0: p = self.obtener_precio_historico(t)
            precios_finales.append(p)
            
        df_tenencia['Valor Mercado Actual'] = precios_finales
        df_tenencia['Tenencia Total Valuada'] = df_tenencia['Cantidad en Tenencia'] * df_tenencia['Valor Mercado Actual']
        df_tenencia['Ganancia/Perdida NO Realizada ($)'] = df_tenencia['Tenencia Total Valuada'] - df_tenencia['Total Invertido ARS']
        return df_tenencia

    def generar_analisis_avanzado(self, df_fifo):
        analisis = {}
        costos = self.df_boletos['Costos Mercado'].sum() if 'Costos Mercado' in self.df_boletos.columns else 0
        aranceles = self.df_boletos['Arancel'].sum() if 'Arancel' in self.df_boletos.columns else 0
        analisis['Comisiones Broker (Arancel)'] = aranceles
        analisis['Derechos de Mercado (Bolsa)'] = costos
        analisis['Total Costos Operativos'] = costos + aranceles
        
        # PROCESAMIENTO QUIRÚRGICO DE MOVIMIENTOS.XLSX CON API HISTÓRICA
        df_m = self.df_movimientos.copy()
        
        fondeos_pesos = 0
        fondeos_dolares = 0
        fondeos_usd_historico_ars = 0
        retiros_pesos = 0
        retiros_dolares = 0
        retiros_usd_historico_ars = 0
        rentas_pesos = 0
        rentas_dolares = 0
        rentas_usd_historico_ars = 0
        
        if not df_m.empty:
            col_desc = self.obtener_columna_flexible(df_m, ['Descripcion', 'Detalle'])
            col_imp = self.obtener_columna_flexible(df_m, ['Importe', 'Monto'])
            col_mon = self.obtener_columna_flexible(df_m, ['Moneda'])
            col_f = self.obtener_columna_flexible(df_m, ['Concertacion', 'Fecha'])
            
            # Traemos la historia del dólar
            print("🌐 Consultando Dólar MEP histórico...")
            serie_mep = self.obtener_dolar_mep_historico()
            
            if col_desc and col_imp and col_mon and col_f:
                df_m['fecha_dt'] = pd.to_datetime(df_m[col_f], errors='coerce').dt.normalize()
                
                # Relleno del MEP en cada fila según la fecha
                if serie_mep is not None:
                    df_m['mep_dia'] = df_m['fecha_dt'].map(serie_mep).fillna(1250.0)
                else:
                    df_m['mep_dia'] = 1250.0
                    
                desc = df_m[col_desc].astype(str)
                mon = df_m[col_mon].astype(str).str.upper()
                imp = pd.to_numeric(df_m[col_imp], errors='coerce').fillna(0)
                mep = df_m['mep_dia']
                
                mask_usd = mon.str.contains('DÓLAR|DOLAR', na=False)
                mask_ars = mon.str.contains('PESOS', na=False)
                
                # 1. RECIBO DE COBRO (Fondeos / Aportes)
                mask_recibo = desc.str.contains('Recibo de Cobro', case=False, na=False)
                fondeos_pesos += imp[mask_recibo & mask_ars].sum()
                fondeos_dolares += imp[mask_recibo & mask_usd].sum()
                fondeos_usd_historico_ars += (imp[mask_recibo & mask_usd] * mep[mask_recibo & mask_usd]).sum()
                
                # 2. COMPROBANTE DE PAGO (Retiros / Extracciones)
                mask_pago = desc.str.contains('Comprobante de Pago', case=False, na=False)
                retiros_pesos += abs(imp[mask_pago & mask_ars & (imp < 0)].sum())
                retiros_dolares += abs(imp[mask_pago & mask_usd & (imp < 0)].sum())
                retiros_usd_historico_ars += abs((imp[mask_pago & mask_usd & (imp < 0)] * mep[mask_pago & mask_usd & (imp < 0)]).sum())
                
                # 3. DIVIDENDOS Y RENTAS / AMORTIZACIONES
                mask_rentas = desc.str.contains('Dividendo|Renta|Amortización', case=False, na=False) & (~desc.str.contains('acciones', case=False, na=False))
                rentas_pesos += imp[mask_rentas & mask_ars].sum()
                rentas_dolares += imp[mask_rentas & mask_usd].sum()
                rentas_usd_historico_ars += (imp[mask_rentas & mask_usd] * mep[mask_rentas & mask_usd]).sum()

        analisis['Fondeos ARS'] = fondeos_pesos
        analisis['Fondeos USD'] = fondeos_dolares
        analisis['Fondeos USD Historico ARS'] = fondeos_usd_historico_ars
        
        analisis['Retiros ARS'] = retiros_pesos
        analisis['Retiros USD'] = retiros_dolares
        analisis['Retiros USD Historico ARS'] = retiros_usd_historico_ars
        
        analisis['Rentas ARS'] = rentas_pesos
        analisis['Rentas USD'] = rentas_dolares
        analisis['Rentas USD Historico ARS'] = rentas_usd_historico_ars
            
        return pd.DataFrame(list(analisis.items()), columns=['Metrica', 'Valor'])

    def exportar_base_datos(self):
        if not self.cargar_datos_crudos(): return
        cap_neto = self.procesar_cashflow()
        self.limpiar_y_ajustar_boletos()
        df_tenencia, df_fifo, df_lotes = self.calcular_inventario()
        df_tenencia_valuada = self.valuar_activos_yfinance(df_tenencia)
        df_analisis_av = self.generar_analisis_avanzado(df_fifo)
        
        resumen_macro = pd.DataFrame({
            'Metrica': ['Flujo Fondeo Neto', 'Total P&L Realizado', 'Total P&L NO Realizada'],
            'Valor': [
                cap_neto, 
                df_fifo['P&L Realizado ($)'].sum() if not df_fifo.empty else 0,
                (df_tenencia_valuada['Ganancia/Perdida NO Realizada ($)'].sum() if not df_tenencia_valuada.empty else 0) + cap_neto
            ]
        })

        try:
            with pd.ExcelWriter(self.ruta_salida, engine='xlsxwriter') as writer:
                if not self.df_movimientos.empty:
                    df_m = self.df_movimientos.copy()
                    col_desc = self.obtener_columna_flexible(df_m, ['Descripcion', 'Detalle'])
                    if col_desc:
                        mask_caja_pura = df_m[col_desc].astype(str).str.contains('Recibo de Cobro|Comprobante de Pago|Dividendo|Renta', case=False, na=False)
                        df_caja_export = df_m[mask_caja_pura]
                    else:
                        df_caja_export = df_m
                    df_caja_export.to_excel(writer, sheet_name='Flujo_Caja', index=False)
                    
                if not df_tenencia_valuada.empty: df_tenencia_valuada.to_excel(writer, sheet_name='Tenencia_Actual', index=False)
                if not df_fifo.empty: df_fifo.to_excel(writer, sheet_name='Operaciones_Cerradas_FIFO', index=False)
                if not df_lotes.empty: df_lotes.to_excel(writer, sheet_name='Lotes_Abiertos', index=False)
                df_analisis_av.to_excel(writer, sheet_name='Analisis_Avanzado', index=False)
                self.df_boletos.to_excel(writer, sheet_name='Historial_Bruto', index=False)
                resumen_macro.to_excel(writer, sheet_name='Macro_Benchmark', index=False)
            print(f"✅ ÉXITO. Reporte generado en: {self.ruta_salida}")
        except Exception as e:
            print(f"❌ Error al guardar el archivo Excel: {e}")

if __name__ == '__main__':
    motor = MotorCuantitativo()
    motor.exportar_base_datos()