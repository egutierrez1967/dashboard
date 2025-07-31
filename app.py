import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import numpy as np
from scipy.stats import zscore
import warnings
warnings.filterwarnings('ignore')

# --- Configuración de página ---
st.set_page_config(layout="wide", page_title="🧠 Dashboard Macro Inteligente Pro", page_icon="🌍")
st.title("🧠 Dashboard Macro Inteligente Pro: Análisis Avanzado")

# --- Funciones auxiliares mejoradas ---
@st.cache_data(ttl=3600)
def cargar_datos_avanzado(tickers_tuple, start, end):
    """Carga datos con mejor manejo de errores y validación"""
    if not tickers_tuple:
        return pd.DataFrame(), {}
    
    tickers = list(tickers_tuple)
    datos_exitosos = {}
    datos_fallidos = {}
    
    for ticker in tickers:
        try:
            # Descargar datos con diferentes parámetros
            data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True, 
                             threads=False, group_by='ticker')
            
            if data.empty:
                datos_fallidos[ticker] = "No hay datos disponibles para el período"
                continue
            
            # Debug: mostrar estructura de columnas
            # st.write(f"DEBUG {ticker}: Columnas = {data.columns.tolist()}")
            
            precio_serie = None
            
            # Estrategia 1: Buscar 'Close' directamente
            if 'Close' in data.columns:
                precio_serie = data['Close']
            
            # Estrategia 2: Si hay MultiIndex, buscar Close en el segundo nivel
            elif isinstance(data.columns, pd.MultiIndex):
                if 'Close' in data.columns.get_level_values(1):
                    close_data = data.xs('Close', level=1, axis=1)
                    if isinstance(close_data, pd.DataFrame) and close_data.shape[1] == 1:
                        precio_serie = close_data.iloc[:, 0]
                    elif isinstance(close_data, pd.Series):
                        precio_serie = close_data
                    else:
                        precio_serie = close_data
            
            # Estrategia 3: Buscar columnas que contengan 'close' (case insensitive)
            elif any('close' in col.lower() for col in data.columns):
                close_cols = [col for col in data.columns if 'close' in col.lower()]
                precio_serie = data[close_cols[0]]
            
            # Estrategia 4: Si solo hay una columna, usar esa
            elif len(data.columns) == 1:
                precio_serie = data.iloc[:, 0]
            
            # Estrategia 5: Buscar columnas típicas de precio
            else:
                columnas_precio = ['Adj Close', 'Price', 'Last', 'Value']
                for col_name in columnas_precio:
                    if col_name in data.columns:
                        precio_serie = data[col_name]
                        break
            
            # Verificar si encontramos datos válidos
            if precio_serie is not None and len(precio_serie) > 0:
                # Asegurar que sea una Serie
                if isinstance(precio_serie, pd.DataFrame):
                    if precio_serie.shape[1] == 1:
                        precio_serie = precio_serie.iloc[:, 0]
                    else:
                        precio_serie = precio_serie.iloc[:, -1]  # Tomar la última columna
                
                # Convertir a numérico y limpiar
                precio_serie = pd.to_numeric(precio_serie, errors='coerce')
                precio_serie = precio_serie.dropna()
                
                if len(precio_serie) > 0:
                    datos_exitosos[ticker] = precio_serie
                else:
                    datos_fallidos[ticker] = "Datos de precio vacíos después de limpieza"
            else:
                datos_fallidos[ticker] = f"No se encontró columna de precio. Columnas disponibles: {data.columns.tolist()}"
            
        except Exception as e:
            datos_fallidos[ticker] = f"Error descargando: {str(e)}"
    
    # Crear DataFrame con datos exitosos
    if datos_exitosos:
        try:
            # Alinear todas las series por fecha
            df_final = pd.DataFrame(datos_exitosos)
            df_final = df_final.dropna(how='all')
            
            if not df_final.empty:
                return df_final, datos_fallidos
            else:
                return pd.DataFrame(), {**datos_fallidos, "DataFrame_Final": "DataFrame vacío después de limpieza"}
                
        except Exception as e:
            return pd.DataFrame(), {**datos_fallidos, "DataFrame_Error": f"Error creando DataFrame: {str(e)}"}
    else:
        return pd.DataFrame(), datos_fallidos

def calcular_metricas_avanzadas(data):
    """Calcula métricas avanzadas de riesgo y rendimiento"""
    metricas = []
    
    for col in data.columns:
        serie = data[col].dropna()
        if len(serie) < 30:  # Mínimo 30 observaciones
            continue
            
        returns = serie.pct_change().dropna()
        
        # Métricas básicas
        retorno_total = (serie.iloc[-1] / serie.iloc[0] - 1) * 100
        retorno_anual = ((serie.iloc[-1] / serie.iloc[0]) ** (252 / len(serie)) - 1) * 100
        volatilidad = returns.std() * (252**0.5) * 100
        
        # Métricas avanzadas
        sharpe = (retorno_anual - 2) / volatilidad if volatilidad != 0 else 0
        max_drawdown = calcular_max_drawdown(serie)
        var_95 = np.percentile(returns, 5) * 100  # Value at Risk 95%
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # Calmar ratio (retorno anual / max drawdown)
        calmar = retorno_anual / abs(max_drawdown) if max_drawdown != 0 else 0
        
        metricas.append({
            "Activo": col,
            "Retorno Total (%)": round(retorno_total, 2),
            "Retorno Anual (%)": round(retorno_anual, 2),
            "Volatilidad (%)": round(volatilidad, 2),
            "Sharpe": round(sharpe, 2),
            "Max Drawdown (%)": round(max_drawdown, 2),
            "VaR 95% (%)": round(var_95, 2),
            "Calmar": round(calmar, 2),
            "Skewness": round(skewness, 2),
            "Kurtosis": round(kurtosis, 2)
        })
    
    return pd.DataFrame(metricas)

def calcular_max_drawdown(serie):
    """Calcula el máximo drawdown de una serie de precios"""
    peak = serie.expanding().max()
    drawdown = (serie - peak) / peak * 100
    return drawdown.min()

def detectar_anomalias(data, ventana=30, threshold=2.5):
    """Detecta anomalías usando Z-score móvil"""
    anomalias = {}
    
    for col in data.columns:
        serie = data[col].dropna()
        returns = serie.pct_change().dropna()
        
        # Z-score móvil
        rolling_mean = returns.rolling(window=ventana).mean()
        rolling_std = returns.rolling(window=ventana).std()
        z_scores = (returns - rolling_mean) / rolling_std
        
        # Detectar anomalías
        anomalias_idx = np.where(np.abs(z_scores) > threshold)[0]
        if len(anomalias_idx) > 0:
            anomalias[col] = {
                'fechas': returns.iloc[anomalias_idx].index.tolist(),
                'valores': returns.iloc[anomalias_idx].values.tolist(),
                'z_scores': z_scores.iloc[anomalias_idx].values.tolist()
            }
    
    return anomalias

def analisis_regimenes(data, ventana=60):
    """Análisis de regímenes de volatilidad"""
    regimenes = {}
    
    for col in data.columns:
        serie = data[col].dropna()
        returns = serie.pct_change().dropna()
        
        # Volatilidad móvil
        vol_movil = returns.rolling(window=ventana).std() * (252**0.5) * 100
        
        # Definir regímenes basados en percentiles
        low_vol = vol_movil.quantile(0.33)
        high_vol = vol_movil.quantile(0.67)
        
        regimen = pd.Series(index=vol_movil.index, dtype='object')
        regimen[vol_movil <= low_vol] = 'Baja Volatilidad'
        regimen[(vol_movil > low_vol) & (vol_movil <= high_vol)] = 'Volatilidad Media'
        regimen[vol_movil > high_vol] = 'Alta Volatilidad'
        
        regimenes[col] = {
            'volatilidad': vol_movil,
            'regimen': regimen,
            'actual': regimen.iloc[-1] if not regimen.empty else 'N/A'
        }
    
    return regimenes

# --- Debug: Función para diagnosticar estructura de datos ---
def diagnosticar_ticker(ticker, start, end):
    """Función para diagnosticar la estructura de datos de un ticker"""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        st.write(f"**{ticker}:**")
        st.write(f"- Shape: {data.shape}")
        st.write(f"- Columnas: {data.columns.tolist()}")
        st.write(f"- Tipo de columnas: {type(data.columns)}")
        if isinstance(data.columns, pd.MultiIndex):
            st.write(f"- Niveles: {data.columns.nlevels}")
            st.write(f"- Nivel 0: {data.columns.get_level_values(0).unique().tolist()}")
            st.write(f"- Nivel 1: {data.columns.get_level_values(1).unique().tolist()}")
        st.write(f"- Primeras 3 filas:")
        st.dataframe(data.head(3))
        st.write("---")
    except Exception as e:
        st.write(f"**{ticker}**: Error - {e}")

# Agregar botón de diagnóstico en sidebar
if st.sidebar.button("🔍 Diagnosticar tickers problemáticos"):
    st.subheader("🔍 Diagnóstico de Tickers")
    tickers_problema = ["SPY", "QQQ", "TLT", "GLD", "SLV"]
    for ticker in tickers_problema:
        diagnosticar_ticker(ticker, fecha_inicio, fecha_fin)

# --- Categorías macroeconómicas mejoradas ---
categorias = {
    "🏦 Bonos EE.UU.": ["TLT", "IEF", "SHY", "GOVT"],
    "🌍 Bonos Emergentes": ["EMB", "PCY", "VWOB"],
    "📈 Acciones EE.UU.": ["SPY", "QQQ", "IWM", "DIA"],
    "🌏 Acciones Internacionales": ["VEA", "VWO", "IEFA"],
    "🌱 Commodities Agrícolas": ["DBA", "SOIL", "CORN", "WEAT"],
    "⛽ Energía": ["USO", "XLE", "UNG", "ICLN"],
    "🪙 Metales Preciosos": ["GLD", "SLV", "PPLT", "PDBC"],
    "🔩 Metales Industriales": ["COPX", "JJN", "REMX"],
    "🏠 Real Estate": ["VNQ", "SCHH", "REM"],
    "💱 Divisas": ["UUP", "FXE", "FXY", "FXB"],
    "📊 Indicadores Macro": ["^TNX", "^VIX", "TIP", "^IRX"],
    "🦄 Crypto": ["BTC-USD", "ETH-USD", "COIN"],
    "🎯 Mag 7": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"],
    "🇨🇳 China": ["MCHI", "FXI", "ASHR", "BABA", "JD"],
    "🇪🇺 Europa": ["EZU", "VGK", "IEUR"],
    "🇯🇵 Japón": ["EWJ", "DXJ", "IEFA"],
}

# --- Sidebar: Configuración mejorada ---
st.sidebar.header("🔧 Configuración Avanzada")

# Selector de análisis
tipo_analisis = st.sidebar.selectbox(
    "🎯 Tipo de Análisis",
    [
        "Dashboard Completo",
        "Análisis de Riesgo",
        "Detección de Anomalías",
        "Análisis de Correlaciones",
        "Regímenes de Volatilidad",
        "Comparativa Sectorial"
    ]
)

# Botón para limpiar todo y usar solo tickers manuales
modo_limpiar = st.sidebar.checkbox("🧹 Modo manual: solo tickers propios", value=False)

if modo_limpiar:
    st.sidebar.info("✅ Modo manual activado")
    with st.sidebar.expander("✏️ Ingresá tus tickers"):
        tickers_manual_input = st.text_input(
            "Tickers (ej: AAPL, TSLA, BTC-USD)",
            value="SPY,QQQ,TLT,GLD"
        )
    tickers_seleccionados = [t.strip().upper() for t in tickers_manual_input.split(",") if t.strip()]
else:
    # Selector múltiple mejorado
    with st.sidebar.expander("🔍 Seleccionar categorías", expanded=True):
        seleccionadas = st.multiselect(
            "Categorías de activos",
            options=list(categorias.keys()),
            default=["🏦 Bonos EE.UU.", "📈 Acciones EE.UU.", "🪙 Metales Preciosos"]
        )
    
    tickers_seleccionados = sum([categorias[cat] for cat in seleccionadas], [])
    
    with st.sidebar.expander("✏️ Tickers adicionales"):
        tickers_manual_input = st.text_input("Agregar más", "")
        if tickers_manual_input:
            tickers_manual_list = [t.strip().upper() for t in tickers_manual_input.split(",") if t.strip()]
            tickers_seleccionados += tickers_manual_list

# --- Parámetros avanzados ---
with st.sidebar.expander("⚙️ Parámetros Avanzados"):
    ventana_volatilidad = st.slider("Ventana para volatilidad móvil", 10, 120, 30)
    threshold_anomalias = st.slider("Umbral detección anomalías (Z-score)", 1.5, 4.0, 2.5)
    incluir_fines_semana = st.checkbox("Incluir fines de semana", False)

# --- Fechas ---
with st.sidebar.expander("📅 Rango de fechas"):
    fecha_fin = st.date_input("Fecha final", value=date.today())
    
    # Opciones rápidas de periodo
    periodo_rapido = st.selectbox(
        "Periodo rápido",
        ["Personalizado", "1 mes", "3 meses", "6 meses", "1 año", "2 años", "5 años"]
    )
    
    if periodo_rapido != "Personalizado":
        dias = {"1 mes": 30, "3 meses": 90, "6 meses": 180, "1 año": 365, "2 años": 730, "5 años": 1825}
        fecha_inicio = fecha_fin - timedelta(days=dias[periodo_rapido])
    else:
        fecha_inicio = st.date_input("Fecha inicial", value=fecha_fin - timedelta(days=365))

# Validaciones
if fecha_inicio >= fecha_fin:
    st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin.")
    st.stop()

tickers = sorted(set(tickers_seleccionados))
if not tickers:
    st.warning("⚠️ Selecciona al menos un activo.")
    st.stop()

# --- Carga de datos mejorada ---
with st.spinner("Cargando datos..."):
    data, errores = cargar_datos_avanzado(tuple(tickers), fecha_inicio, fecha_fin)

# Mostrar errores si los hay
if errores:
    with st.sidebar.expander(f"⚠️ Errores de carga ({len(errores)})"):
        for ticker, error in errores.items():
            st.write(f"**{ticker}**: {error}")

if data.empty:
    st.error("❌ No se pudieron cargar datos. Verifica los tickers.")
    st.stop()

# --- Dashboard según tipo de análisis ---
if tipo_analisis == "Dashboard Completo":
    # --- Gráfico principal mejorado ---
    st.subheader("📊 Evolución de Activos")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo_grafico = st.selectbox("Tipo", ["Normalizado (Base 100)", "Precios Absolutos", "Rendimientos"])
    with col2:
        escala_log = st.checkbox("Escala logarítmica", False)
    with col3:
        mostrar_volumen = st.checkbox("Mostrar señales", False)
    
    # Preparar datos según tipo
    if tipo_grafico == "Normalizado (Base 100)":
        data_plot = data / data.iloc[0] * 100
        ylabel = "Rendimiento (Base 100)"
    elif tipo_grafico == "Rendimientos":
        data_plot = data.pct_change().cumsum() * 100
        ylabel = "Rendimiento Acumulado (%)"
    else:
        data_plot = data
        ylabel = "Precio"
    
    fig = px.line(
        data_plot, 
        x=data_plot.index, 
        y=data_plot.columns,
        title=f"Evolución de activos - {tipo_grafico}"
    )
    
    fig.update_layout(
        height=600,
        yaxis_type="log" if escala_log else "linear",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- Métricas avanzadas ---
    st.subheader("📈 Análisis de Riesgo y Rendimiento")
    metricas_df = calcular_metricas_avanzadas(data)
    
    if not metricas_df.empty:
        # Mostrar tabla con formato condicional
        st.dataframe(
            metricas_df.set_index("Activo").style
            .background_gradient(cmap="RdYlGn", subset=["Retorno Total (%)", "Sharpe", "Calmar"])
            .background_gradient(cmap="RdYlGn_r", subset=["Volatilidad (%)", "Max Drawdown (%)", "VaR 95% (%)"])
            .format({
                "Retorno Total (%)": "{:.2f}%",
                "Retorno Anual (%)": "{:.2f}%",
                "Volatilidad (%)": "{:.2f}%",
                "Max Drawdown (%)": "{:.2f}%",
                "VaR 95% (%)": "{:.2f}%"
            }),
            use_container_width=True
        )

elif tipo_analisis == "Detección de Anomalías":
    st.subheader("🚨 Detección de Anomalías")
    
    anomalias = detectar_anomalias(data, ventana=ventana_volatilidad, threshold=threshold_anomalias)
    
    if anomalias:
        for activo, info in anomalias.items():
            with st.expander(f"🔍 Anomalías en {activo} ({len(info['fechas'])} detectadas)"):
                anomalias_df = pd.DataFrame({
                    'Fecha': info['fechas'],
                    'Rendimiento (%)': [f"{x*100:.2f}%" for x in info['valores']],
                    'Z-Score': [f"{x:.2f}" for x in info['z_scores']]
                })
                st.dataframe(anomalias_df, use_container_width=True)
                
                # Gráfico de la serie con anomalías marcadas
                serie = data[activo].dropna()
                returns = serie.pct_change().dropna()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=returns.index, 
                    y=returns*100,
                    mode='lines',
                    name=f'Rendimientos {activo}',
                    line=dict(color='blue', width=1)
                ))
                
                # Marcar anomalías
                fig.add_trace(go.Scatter(
                    x=info['fechas'],
                    y=[x*100 for x in info['valores']],
                    mode='markers',
                    name='Anomalías',
                    marker=dict(color='red', size=8, symbol='x')
                ))
                
                fig.update_layout(
                    title=f"Rendimientos y anomalías - {activo}",
                    xaxis_title="Fecha",
                    yaxis_title="Rendimiento (%)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"✅ No se detectaron anomalías con umbral Z-score > {threshold_anomalias}")

elif tipo_analisis == "Regímenes de Volatilidad":
    st.subheader("📊 Análisis de Regímenes de Volatilidad")
    
    regimenes = analisis_regimenes(data, ventana=ventana_volatilidad)
    
    # Resumen de regímenes actuales
    col1, col2, col3 = st.columns(3)
    regimenes_actuales = {"Baja Volatilidad": 0, "Volatilidad Media": 0, "Alta Volatilidad": 0}
    
    for activo, info in regimenes.items():
        regimen_actual = info['actual']
        if regimen_actual in regimenes_actuales:
            regimenes_actuales[regimen_actual] += 1
    
    with col1:
        st.metric("🟢 Baja Volatilidad", regimenes_actuales["Baja Volatilidad"])
    with col2:
        st.metric("🟡 Volatilidad Media", regimenes_actuales["Volatilidad Media"])
    with col3:
        st.metric("🔴 Alta Volatilidad", regimenes_actuales["Alta Volatilidad"])
    
    # Gráficos por activo
    for activo, info in regimenes.items():
        with st.expander(f"📈 {activo} - Régimen actual: {info['actual']}"):
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'Precio de {activo}', 'Volatilidad Móvil y Régimen'),
                shared_xaxis=True,
                vertical_spacing=0.1
            )
            
            # Precio
            fig.add_trace(
                go.Scatter(x=data.index, y=data[activo], name=f'Precio {activo}'),
                row=1, col=1
            )
            
            # Volatilidad con colores por régimen
            vol_data = info['volatilidad'].dropna()
            regimen_data = info['regimen'].dropna()
            
            colors = {'Baja Volatilidad': 'green', 'Volatilidad Media': 'orange', 'Alta Volatilidad': 'red'}
            for regimen in colors.keys():
                mask = regimen_data == regimen
                if mask.any():
                    fig.add_trace(
                        go.Scatter(
                            x=vol_data[mask].index,
                            y=vol_data[mask],
                            mode='markers',
                            name=regimen,
                            marker=dict(color=colors[regimen], size=4)
                        ),
                        row=2, col=1
                    )
            
            fig.update_layout(height=500, showlegend=True)
            fig.update_xaxes(title_text="Fecha", row=2, col=1)
            fig.update_yaxes(title_text="Precio", row=1, col=1)
            fig.update_yaxes(title_text="Volatilidad (%)", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)

# --- Footer con información adicional ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Métricas explicadas")
st.sidebar.markdown("""
**Sharpe Ratio**: Rendimiento ajustado por riesgo
**Calmar Ratio**: Rendimiento anual / Max Drawdown  
**VaR 95%**: Pérdida máxima esperada 95% del tiempo
**Skewness**: Asimetría de los rendimientos
**Kurtosis**: "Cola" de la distribución
""")

# Mostrar información del dataset
st.sidebar.markdown("---")
st.sidebar.info(f"""
📈 **Datos cargados:**
- Activos: {len(data.columns)}
- Período: {fecha_inicio} a {fecha_fin}
- Observaciones: {len(data)}
""")

# --- Descarga de datos mejorada ---
if not data.empty:
    @st.cache_data
    def preparar_descarga(df, metricas_df=None):
        output = {}
        output['precios'] = df.to_csv().encode("utf-8")
        if metricas_df is not None and not metricas_df.empty:
            output['metricas'] = metricas_df.to_csv(index=False).encode("utf-8")
        return output
    
    archivos = preparar_descarga(data, calcular_metricas_avanzadas(data) if 'metricas_df' in locals() else None)
    
    st.sidebar.download_button(
        label="📥 Descargar precios (CSV)",
        data=archivos['precios'],
        file_name=f"precios_macro_{date.today()}.csv",
        mime="text/csv"
    )
    
    if 'metricas' in archivos:
        st.sidebar.download_button(
            label="📊 Descargar métricas (CSV)",
            data=archivos['metricas'],
            file_name=f"metricas_macro_{date.today()}.csv",
            mime="text/csv"
        )
