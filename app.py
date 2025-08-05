import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Comparativa Acciones vs Índices",
    page_icon="📈",
    layout="wide"
)

# Título principal
st.title("📈 Dashboard Comparativa Acciones vs Índices")
st.markdown("---")

# Función para obtener el nombre de la empresa
@st.cache_data(ttl=86400)  # Cache por 24 horas
def get_company_name(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('longName', info.get('shortName', symbol))
    except:
        return symbol

# Datos de los índices y sus empresas con cobertura completa del mercado
indices_data = {
    "S&P 500": {
        "symbol": "^GSPC",
        "stocks": [
            "MSFT", "AAPL", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "BRK-B", "LLY", "JPM",
            "AVGO", "TSLA", "V", "XOM", "UNH", "MA", "JNJ", "HD", "PG", "COST"
        ]
    },
    "Nasdaq Composite": {
        "symbol": "^IXIC",
        "stocks": [
            "MSFT", "AAPL", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "AVGO", "TSLA", "COST",
            "PEP", "ADBE", "NFLX", "AMD", "TMUS", "CSCO", "QCOM", "AMGN", "CMCSA", "ISRG"
        ]
    },
    "Dow Jones": {
        "symbol": "^DJI",
        "stocks": [
            "UNH", "GS", "MSFT", "CAT", "HD", "AMGN", "CRM", "MCD", "V", "JNJ",
            "TRV", "JPM", "AXP", "HON", "PG", "IBM", "AAPL", "CVX", "BA", "MRK"
        ]
    },
    "Russell 2000": {
        "symbol": "^RUT",
        "stocks": [
            "SMCI", "MSTR", "CVNA", "AFRM", "PLTR", "CELH", "VST", "APP", "ELF", "GTLB",
            "KRYS", "WFRD", "TOL", "LNW", "FIX", "CHRD", "ENSG", "JBL", "CNM", "FN"
        ]
    },
    "Tecnología (XLK)": {
        "symbol": "XLK",
        "stocks": [
            "MSFT", "AAPL", "NVDA", "AVGO", "CRM", "ORCL", "ADBE", "NOW", "INTU", "IBM",
            "TXN", "QCOM", "AMD", "MU", "INTC", "ADI", "LRCX", "KLAC", "CDNS", "SNPS"
        ]
    },
    "Financiero (XLF)": {
        "symbol": "XLF",
        "stocks": [
            "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK",
            "C", "AXP", "SCHW", "CB", "MMC", "ICE", "PGR", "AON", "USB", "TFC"
        ]
    },
    "Energético (XLE)": {
        "symbol": "XLE",
        "stocks": [
            "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "MPC", "VLO", "OXY", "BKR",
            "KMI", "WMB", "OKE", "HES", "DVN", "FANG", "APA", "EQT", "COG", "MRO"
        ]
    },
    "Salud (XLV)": {
        "symbol": "XLV",
        "stocks": [
            "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ABT", "ISRG", "DHR",
            "BSX", "AMGN", "SYK", "MDT", "GILD", "BDX", "REGN", "VRTX", "ELV", "CI"
        ]
    },
    "Industriales (XLI)": {
        "symbol": "XLI",
        "stocks": [
            "CAT", "RTX", "HON", "UPS", "LMT", "BA", "DE", "GE", "ADP", "MMM",
            "TDG", "NOC", "EMR", "ETN", "ITW", "PH", "WM", "GD", "RSG", "NSC"
        ]
    },
    "Consumo Discrecional (XLY)": {
        "symbol": "XLY",
        "stocks": [
            "TSLA", "AMZN", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "CMG",
            "ORLY", "AZO", "ROST", "YUM", "GM", "F", "MAR", "HLT", "ABNB", "MGM"
        ]
    },
    "Consumo Básico (XLP)": {
        "symbol": "XLP",
        "stocks": [
            "PG", "COST", "WMT", "PEP", "KO", "PM", "MO", "MDLZ", "CL", "GIS",
            "KMB", "SYY", "KHC", "CHD", "K", "HSY", "MKC", "CAG", "CPB", "HRL"
        ]
    },
    "Servicios Públicos (XLU)": {
        "symbol": "XLU",
        "stocks": [
            "NEE", "SO", "DUK", "CEG", "SRE", "AEP", "VST", "D", "PCG", "PEG",
            "EXC", "XEL", "ED", "ETR", "AWK", "ES", "FE", "EIX", "PPL", "CMS"
        ]
    },
    "Bienes Raíces (XLRE)": {
        "symbol": "XLRE",
        "stocks": [
            "PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "DLR", "EXR", "BXP",
            "SBAC", "VTR", "ARE", "MAA", "EQR", "INVH", "ESS", "KIM", "REG", "UDR"
        ]
    },
    "Materiales (XLB)": {
        "symbol": "XLB",
        "stocks": [
            "LIN", "SHW", "APD", "FCX", "ECL", "NUE", "NEM", "DOW", "VMC", "MLM",
            "PPG", "CTVA", "DD", "IFF", "PKG", "IP", "CF", "ALB", "MOS", "FMC"
        ]
    }
}

# Sidebar para controles
st.sidebar.header("🔧 Configuración")

# Selección de índice (radio buttons)
selected_index = st.sidebar.radio(
    "Selecciona un Índice:",
    list(indices_data.keys())
)

# Selección de período (radio buttons)
period_options = {
    "24 meses": 24,
    "12 meses": 12,
    "6 meses": 6,
    "3 meses": 3
}

selected_period_text = st.sidebar.radio(
    "Selecciona el Período:",
    list(period_options.keys())
)

selected_period = period_options[selected_period_text]

# Botón procesar
process_button = st.sidebar.button("🚀 Procesar", type="primary")

# Función para obtener datos de Yahoo Finance
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_stock_data(symbol, months):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
       
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
       
        if data.empty:
            return None
           
        # Calcular rendimiento base 100
        data['Rendimiento_Base100'] = (data['Close'] / data['Close'].iloc[0]) * 100
        return data
    except Exception as e:
        st.error(f"Error obteniendo datos para {symbol}: {str(e)}")
        return None

# Función para normalizar datos a base 100
def normalize_to_base100(data):
    if data is None or data.empty:
        return None
    return (data['Close'] / data['Close'].iloc[0]) * 100

# Inicializar estado de sesión para mantener los datos
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Procesamiento cuando se presiona el botón
if process_button:
    st.markdown(f"## 📊 Análisis: {selected_index} - {selected_period_text}")
   
    with st.spinner(f"Obteniendo datos de {selected_index} y sus empresas..."):
        # Obtener datos del índice
        index_symbol = indices_data[selected_index]["symbol"]
        index_data = get_stock_data(index_symbol, selected_period)
       
        if index_data is None:
            st.error(f"No se pudieron obtener datos del índice {selected_index}")
            st.stop()
       
        # Obtener datos de las acciones
        stocks_data = {}
        stocks_performance = {}
        company_names = {}
       
        progress_bar = st.progress(0)
        total_stocks = len(indices_data[selected_index]["stocks"])
       
        for i, stock in enumerate(indices_data[selected_index]["stocks"]):
            stock_data = get_stock_data(stock, selected_period)
            if stock_data is not None:
                stocks_data[stock] = stock_data
                # Obtener nombre de la empresa
                company_names[stock] = get_company_name(stock)
                # Calcular rendimiento final
                initial_price = stock_data['Close'].iloc[0]
                final_price = stock_data['Close'].iloc[-1]
                stocks_performance[stock] = ((final_price / initial_price) * 100) - 100
           
            progress_bar.progress((i + 1) / total_stocks)
       
        progress_bar.empty()
       
        # Calcular rendimiento del índice
        index_initial = index_data['Close'].iloc[0]
        index_final = index_data['Close'].iloc[-1]
        index_performance = ((index_final / index_initial) * 100) - 100
        
        # Guardar datos en el estado de sesión
        st.session_state.index_data = index_data
        st.session_state.stocks_data = stocks_data
        st.session_state.stocks_performance = stocks_performance
        st.session_state.company_names = company_names
        st.session_state.index_performance = index_performance
        st.session_state.selected_index = selected_index
        st.session_state.selected_period_text = selected_period_text
        st.session_state.data_loaded = True

# Mostrar gráfico y controles si los datos están cargados
if st.session_state.data_loaded:
    # Recuperar datos del estado de sesión
    index_data = st.session_state.index_data
    stocks_data = st.session_state.stocks_data
    stocks_performance = st.session_state.stocks_performance
    company_names = st.session_state.company_names
    index_performance = st.session_state.index_performance
    selected_index = st.session_state.selected_index
    selected_period_text = st.session_state.selected_period_text
       
    # CONTROLES INTERACTIVOS DEL GRÁFICO
    st.markdown("### 🎛️ Controles del Gráfico")
    
    # Crear controles en columnas
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
    
    with ctrl_col1:
        show_index = st.checkbox("📊 Mostrar Índice", value=True)
    
    with ctrl_col2:
        show_above = st.checkbox("🟢 Mostrar Superiores", value=True)
    
    with ctrl_col3:
        show_below = st.checkbox("🔴 Mostrar Inferiores", value=True)
        
    with ctrl_col4:
        if st.button("🔄 Mostrar Todas"):
            show_index = True
            show_above = True
            show_below = True
    
    # GRÁFICO INTERACTIVO
    # Crear el gráfico
    fig = go.Figure()
    
    # Preparar datos normalizados del índice
    index_normalized = normalize_to_base100(index_data)
   
    # Añadir línea del índice solo si está seleccionado
    if show_index:
        fig.add_trace(go.Scatter(
            x=index_data.index,
            y=index_normalized,
            mode='lines',
            name=f'{selected_index} (Índice)',
            line=dict(color='black', width=4, dash='dash'),
            hovertemplate=f'<b>{selected_index}</b><br>Fecha: %{{x}}<br>Base 100: %{{y:.2f}}<extra></extra>'
        ))
   
    # Preparar colores para las acciones
    colors_above = ['darkgreen', 'green', 'lime', 'forestgreen', 'mediumseagreen', 'springgreen', 'limegreen', 'lightgreen', 'palegreen', 'darkseagreen']
    colors_below = ['darkred', 'red', 'crimson', 'firebrick', 'indianred', 'lightcoral', 'salmon', 'darksalmon', 'orange', 'darkorange']
    
    color_above_idx = 0
    color_below_idx = 0
   
    # Añadir líneas de las acciones según los filtros
    for stock, data in stocks_data.items():
        if data is not None:
            stock_performance = stocks_performance.get(stock, 0)
            is_above_index = stock_performance > index_performance
            
            # Decidir si mostrar esta línea
            should_show = False
            if is_above_index and show_above:
                should_show = True
                color = colors_above[color_above_idx % len(colors_above)]
                color_above_idx += 1
            elif not is_above_index and show_below:
                should_show = True
                color = colors_below[color_below_idx % len(colors_below)]
                color_below_idx += 1
            
            if should_show:
                stock_normalized = normalize_to_base100(data)
                company_name = company_names.get(stock, stock)
                display_name = f"{stock} - {company_name}"
                
                # Agregar emoji según rendimiento
                perf_emoji = "🟢" if is_above_index else "🔴"
                display_name_with_emoji = f"{perf_emoji} {display_name}"
               
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=stock_normalized,
                    mode='lines',
                    name=display_name_with_emoji if len(display_name_with_emoji) <= 55 else f"{perf_emoji} {stock} - {company_name[:35]}...",
                    line=dict(color=color, width=2),
                    hovertemplate=f'<b>{display_name}</b><br>Rendimiento: {stock_performance:.2f}%<br>Fecha: %{{x}}<br>Base 100: %{{y:.2f}}<extra></extra>'
                ))
   
    # Configurar el layout del gráfico - MEJORADO para evitar superposición
    # Contar cuántas líneas se están mostrando para ajustar la leyenda
    total_traces = len(fig.data)
    legend_height = min(0.95, max(0.3, total_traces * 0.04))
    
    # Determinar título dinámico según filtros
    title_parts = []
    if show_index:
        title_parts.append("Índice")
    if show_above:
        title_parts.append("Superiores")
    if show_below:
        title_parts.append("Inferiores")
    
    if not title_parts:
        title_suffix = "Sin datos seleccionados"
    else:
        title_suffix = " + ".join(title_parts)
    
    fig.update_layout(
        title=dict(
            text=f'Comparativa Base 100: {selected_index} - {title_suffix} ({selected_period_text})',
            x=0.5,  # Centrar el título
            xanchor='center'
        ),
        xaxis_title='Fecha',
        yaxis_title='Rendimiento Base 100',
        hovermode='x unified',
        height=700,  # Aumentar altura para dar más espacio
        showlegend=True if total_traces > 0 else False,
        legend=dict(
            orientation="v",  # Leyenda vertical
            yanchor="top",
            y=legend_height,
            xanchor="left",
            x=1.01,  # Posicionar fuera del área del gráfico
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1
        ),
        margin=dict(l=50, r=250, t=80, b=50)  # Más espacio a la derecha para leyenda más ancha
    )
    
    # Mostrar mensaje si no hay datos seleccionados
    if total_traces == 0:
        fig.add_annotation(
            text="No hay datos seleccionados para mostrar<br>Activa al menos una opción arriba",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
            align="center"
        )
   
    st.plotly_chart(fig, use_container_width=True)
   
    # ANÁLISIS DE RENDIMIENTO - Ahora debajo del gráfico
    st.markdown("---")
    st.markdown("## 📈 Análisis de Rendimiento vs Índice")
    
    # Separar empresas por encima y debajo del índice
    above_index = []
    below_index = []
   
    for stock, performance in stocks_performance.items():
        if performance > index_performance:
            above_index.append((stock, performance))
        else:
            below_index.append((stock, performance))
   
    # Ordenar por rendimiento
    above_index.sort(key=lambda x: x[1], reverse=True)
    below_index.sort(key=lambda x: x[1], reverse=True)
   
    # Crear tres columnas para mejor organización
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Mostrar índice de referencia
        st.markdown("### 📊 Índice de Referencia")
        st.markdown(f"**{selected_index}**")
        st.markdown(f"Rendimiento: **{index_performance:.2f}%**")
        
        # Estadísticas adicionales
        st.markdown("### 📊 Estadísticas Generales")
        st.markdown(f"**Empresas analizadas**: {len(stocks_performance)}")
        st.markdown(f"**Por encima del índice**: {len(above_index)}")
        st.markdown(f"**Por debajo del índice**: {len(below_index)}")
       
        if stocks_performance:
            avg_performance = np.mean(list(stocks_performance.values()))
            st.markdown(f"**Rendimiento promedio**: {avg_performance:.2f}%")
            best_performance = max(stocks_performance.values())
            worst_performance = min(stocks_performance.values())
            st.markdown(f"**Mejor rendimiento**: {best_performance:.2f}%")
            st.markdown(f"**Peor rendimiento**: {worst_performance:.2f}%")
    
    with col2:
        # Mostrar empresas por encima del índice
        st.markdown("### 🟢 Por Encima del Índice")
        if above_index:
            for stock, perf in above_index:
                company_name = company_names.get(stock, stock)
                diff = perf - index_performance
                # Truncar nombre de empresa si es muy largo
                display_company = company_name if len(company_name) <= 30 else f"{company_name[:27]}..."
                st.markdown(f"**{stock}** - {display_company}")
                st.markdown(f"🔹 {perf:.2f}% (✅ +{diff:.2f}%)")
                st.markdown("")
        else:
            st.markdown("*No hay empresas por encima del índice*")
    
    with col3:
        # Mostrar empresas por debajo del índice
        st.markdown("### 🔴 Por Debajo del Índice")
        if below_index:
            for stock, perf in below_index:
                company_name = company_names.get(stock, stock)
                diff = perf - index_performance
                # Truncar nombre de empresa si es muy largo
                display_company = company_name if len(company_name) <= 30 else f"{company_name[:27]}..."
                st.markdown(f"**{stock}** - {display_company}")
                st.markdown(f"🔹 {perf:.2f}% (❌ {diff:.2f}%)")
                st.markdown("")
        else:
            st.markdown("*No hay empresas por debajo del índice*")

else:
    # Mostrar instrucciones iniciales solo si no hay datos cargados
    if not st.session_state.get('data_loaded', False):
        # Mostrar instrucciones iniciales
        st.markdown("""
        ## 👋 Bienvenido al Dashboard de Comparativa de Acciones
       
        ### 📋 Instrucciones:
        1. **Selecciona un índice** en el panel izquierdo
        2. **Elige el período** de análisis (3, 6, 12 o 24 meses)
        3. **Presiona "Procesar"** para generar el análisis
       
        ### 📈 Funcionalidades:
        - **Gráfico comparativo** con base 100 desde el inicio del período
        - **Índice de referencia** en línea negra gruesa punteada
        - **Empresas individuales** en diferentes colores
        - **Lista de empresas** por encima y debajo del índice
        - **Estadísticas** de rendimiento relativo
       
        ### 🎯 Objetivo:
        Identificar empresas que están **atrasadas** o **adelantadas** respecto a su índice de referencia para detectar oportunidades de inversión.
        """)
       
        # Mostrar información de los índices disponibles
        st.markdown("### 📊 Índices Disponibles:")
        for index_name, index_info in indices_data.items():
            with st.expander(f"{index_name} ({index_info['symbol']})"):
                st.write(f"**Top 20 empresas**: {', '.join(index_info['stocks'][:10])}...")

# Footer
st.markdown("---")
if st.session_state.get('data_loaded', False):
    if st.button("🔄 Cargar Nuevos Datos", type="secondary"):
        # Limpiar el estado para permitir nueva carga
        for key in ['data_loaded', 'index_data', 'stocks_data', 'stocks_performance', 
                   'company_names', 'index_performance', 'selected_index', 'selected_period_text']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.markdown("💡 **Nota**: Los datos se obtienen de Yahoo Finance y pueden tener un retraso de hasta 15 minutos.")
