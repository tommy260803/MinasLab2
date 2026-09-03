import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sqlalchemy import text
from datetime import datetime, timedelta
from core.db_manager import engine
from core.audit_logger import log_action

@st.cache_data(ttl=300)
def load_filters_data():
    with engine.connect() as conn:
        equipments_df = pd.read_sql("SELECT id, code, name FROM equipments", conn)
        sensor_types_df = pd.read_sql("SELECT DISTINCT sensor_type FROM sensors", conn)
    return equipments_df, sensor_types_df

def fetch_eda_data(eq_id, start_date, end_date):
    query = """
        SELECT sr.reading_timestamp, sr.reading_value, s.sensor_type
        FROM sensor_readings sr
        JOIN sensors s ON sr.sensor_id = s.id
        WHERE s.equipment_id = %(eq_id)s
        AND sr.reading_timestamp >= %(start)s
        AND sr.reading_timestamp <= %(end)s
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={'eq_id': eq_id, 'start': start_date, 'end': end_date + timedelta(days=1)})
    return df

def calculate_outliers_iqr(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return ((series < lower_bound) | (series > upper_bound)).sum(), lower_bound, upper_bound

def render_eda():
    user = st.session_state["user"]
    
    # 1. Verificación estricta de Roles (Solo Admin y Analista)
    if user["role_id"] not in [1, 4]:
        st.error("Acceso denegado: El módulo de Análisis Exploratorio (EDA) es exclusivo para Administradores y Analistas de Datos.")
        st.stop()
        
    # Registro de auditoría
    if not st.session_state.get("eda_loaded_log"):
        log_action(user["id"], "VIEW_EDA", details="Acceso al módulo EDA (CRISP-DM Fase 2)")
        st.session_state["eda_loaded_log"] = True

    st.markdown("## 🔬 Análisis Exploratorio de Datos (EDA)")
    st.markdown("*Fase 2 de CRISP-DM: Comprensión de los Datos*")
    
    eq_df, sens_df = load_filters_data()
    if eq_df.empty:
        st.warning("No hay equipos en la base de datos.")
        return
        
    st.sidebar.markdown("### 🔍 Filtros EDA")
    eq_options = dict(zip(eq_df['name'] + " (" + eq_df['code'] + ")", eq_df['id']))
    selected_eq_name = st.sidebar.selectbox("Seleccione un Equipo", list(eq_options.keys()), key='eda_eq')
    selected_eq_id = eq_options[selected_eq_name]
    
    date_range = st.sidebar.date_input("Rango de Fechas", 
                                       value=(datetime(2023, 10, 20), datetime(2023, 11, 20)), key='eda_dates')
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = datetime(2023, 10, 20), datetime(2023, 11, 20)
        
    sensor_types = sens_df['sensor_type'].tolist()
    selected_sensors = st.sidebar.multiselect("Tipos de Sensores", sensor_types, default=sensor_types, key='eda_sensors')
    
    show_outliers = st.sidebar.checkbox("Mostrar Outliers en Gráficas", value=True)
    
    df = fetch_eda_data(selected_eq_id, start_date, end_date)
    
    if df.empty:
        st.info("No hay datos de sensores para el equipo y rango de fechas seleccionados.")
        return
        
    if selected_sensors:
        df = df[df['sensor_type'].isin(selected_sensors)]
        
    if df.empty:
        st.info("No hay datos para los sensores seleccionados.")
        return
        
    # Formato Wide para correlaciones y estadísticas
    df_wide = df.pivot_table(index='reading_timestamp', columns='sensor_type', values='reading_value').reset_index()
    
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Estadísticas Descriptivas", "📉 Visualizaciones Interactivas", "🚨 Calidad de Datos"])
    
    with tab1:
        st.subheader("Estadísticas Descriptivas Globales")
        desc_stats = []
        for col in df_wide.columns:
            if col != 'reading_timestamp':
                s = df_wide[col].dropna()
                if len(s) > 0:
                    desc_stats.append({
                        'Sensor': col,
                        'Count': len(s),
                        'Media': s.mean(),
                        'Mediana': s.median(),
                        'Desv. Est.': s.std(),
                        'Mínimo': s.min(),
                        'P25 (Q1)': s.quantile(0.25),
                        'P75 (Q3)': s.quantile(0.75),
                        'Máximo': s.max(),
                        'Asimetría': s.skew() if len(s) > 2 else np.nan,
                        'Curtosis': s.kurtosis() if len(s) > 3 else np.nan
                    })
        stats_df = pd.DataFrame(desc_stats)
        st.dataframe(stats_df.style.format(precision=3), use_container_width=True)
        
        # Botón Exportar
        csv = stats_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Exportar Resumen a CSV",
            data=csv,
            file_name=f"eda_resumen_{selected_eq_name}.csv",
            mime="text/csv",
            on_click=lambda: log_action(st.session_state["user"]["id"], "EXPORT_EDA", details="Descarga de reporte EDA estadístico")
        )

    with tab2:
        st.subheader("Análisis Visual")
        
        # Filtrado opcional de outliers para gráficas
        plot_df = df.copy()
        if not show_outliers:
            for s_type in plot_df['sensor_type'].unique():
                s_mask = plot_df['sensor_type'] == s_type
                series = plot_df.loc[s_mask, 'reading_value']
                _, lower, upper = calculate_outliers_iqr(series)
                plot_df.loc[s_mask & ((plot_df['reading_value'] < lower) | (plot_df['reading_value'] > upper)), 'reading_value'] = np.nan
            plot_df = plot_df.dropna(subset=['reading_value'])

        c1, c2 = st.columns(2)
        with c1:
            fig_hist = px.histogram(plot_df, x='reading_value', color='sensor_type', 
                                    barmode='overlay', title='Histograma de Distribución',
                                    marginal='violin')
            st.plotly_chart(fig_hist, use_container_width=True)
        with c2:
            fig_box = px.box(plot_df, x='sensor_type', y='reading_value', color='sensor_type',
                             title='Boxplots (Detección de Outliers)')
            st.plotly_chart(fig_box, use_container_width=True)
            
        c3, c4 = st.columns(2)
        with c3:
            numeric_cols = df_wide.select_dtypes(include=[np.number]).columns
            corr_df = df_wide[numeric_cols].corr()
            fig_corr = px.imshow(corr_df, text_auto='.2f', aspect="auto", 
                                 color_continuous_scale='RdBu_r', title='Heatmap de Correlación (Pearson)')
            st.plotly_chart(fig_corr, use_container_width=True)
        with c4:
            sensors_avail = df_wide.drop(columns=['reading_timestamp']).columns.tolist()
            if len(sensors_avail) >= 2:
                fig_scatter = px.scatter(df_wide, x=sensors_avail[0], y=sensors_avail[1], 
                                         title=f'Scatter: {sensors_avail[0]} vs {sensors_avail[1]}')
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Seleccione al menos 2 tipos de sensores para ver el Scatter Plot de correlación.")

        st.markdown("#### Series Temporales (Zoom Interactivo)")
        fig_ts = px.line(plot_df, x='reading_timestamp', y='reading_value', color='sensor_type', facet_row='sensor_type')
        fig_ts.update_yaxes(matches=None) # Escalas independientes para cada sensor
        st.plotly_chart(fig_ts, use_container_width=True)
        
        # Conteo de Alertas
        with engine.connect() as conn:
            alertas = pd.read_sql("SELECT COUNT(*) as c FROM ai_predictions WHERE equipment_id = %s", conn, params=(selected_eq_id,)).iloc[0]['c']
            st.info(f"**Total histórico de predicciones (Alertas de IA)** evaluadas para este equipo: {alertas}")

    with tab3:
        st.subheader("Auditoría y Calidad de Datos")
        
        dq_results = []
        for col in df_wide.columns:
            if col != 'reading_timestamp':
                s = df_wide[col]
                total = len(s)
                nulls = s.isna().sum()
                
                s_clean = s.dropna()
                outliers_iqr, _, _ = calculate_outliers_iqr(s_clean)
                
                z_scores = np.abs((s_clean - s_clean.mean()) / s_clean.std()) if s_clean.std() > 0 else np.zeros(len(s_clean))
                outliers_z = (z_scores > 3).sum()
                
                dq_results.append({
                    'Sensor': col,
                    'Nulos': nulls,
                    '% Nulos': f"{(nulls/total*100):.2f}%" if total>0 else "0%",
                    'Outliers (IQR)': outliers_iqr,
                    'Outliers (Z>3)': outliers_z
                })
        
        dq_df = pd.DataFrame(dq_results)
        st.table(dq_df)
        
        duplicados = df_wide.duplicated(subset=['reading_timestamp']).sum()
        if duplicados > 0:
            st.warning(f"**Registros duplicados por timestamp:** {duplicados}")
        else:
            st.success("**Registros duplicados por timestamp:** 0")
        
        st.markdown("### 📋 Reporte de Calidad y Sugerencias")
        if any(dq_df['Nulos'] > 0):
            st.error("⚠️ Se han detectado valores nulos. \n\n**Recomendación Fase 3 (Data Prep):** Aplicar técnicas de imputación (media/mediana) o forward-fill (ffill) dado que son series temporales.")
        elif any(dq_df['Outliers (Z>3)'] > 0):
            st.warning("⚠️ Hay presencia de outliers estadísticos (Z-score > 3). \n\n**Recomendación Fase 3 (Data Prep):** Investigar si son eventos reales (fallas) o errores de los sensores. Evaluar usar *Winsorization* o modelos robustos (Tree-based).")
        else:
            st.success("✅ La calidad de datos de esta muestra es óptima. Se puede proceder con la extracción de características (Feature Engineering).")
