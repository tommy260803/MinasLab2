import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from datetime import datetime, timedelta
from core.db_manager import engine
from core.audit_logger import log_action

@st.cache_data(ttl=300)
def load_filters_data():
    """Carga los datos iniciales para los filtros de forma cacheada."""
    with engine.connect() as conn:
        equipments_df = pd.read_sql("SELECT id, code, name FROM equipments", conn)
        sensor_types_df = pd.read_sql("SELECT DISTINCT sensor_type FROM sensors", conn)
    return equipments_df, sensor_types_df

def get_kpi_data():
    """Consulta los datos de los KPIs optimizados con Pandas/SQLAlchemy."""
    with engine.connect() as conn:
        # 1 y 2. Estado de equipos y Disponibilidad
        eq_status = pd.read_sql("SELECT status, COUNT(*) as total FROM equipments GROUP BY status", conn)
        
        # 3. Alertas en últimas 24h (Probabilidad de falla > 70%)
        alerts = pd.read_sql("""
            SELECT COUNT(*) as alerts 
            FROM ai_predictions 
            WHERE failure_probability > 0.7 
            -- En prod sería NOW() - INTERVAL '24 hours', usamos datos fijos para el demo
        """, conn).iloc[0]['alerts']
        
        # 4. Predicciones realizadas (Total global para simular el dashboard)
        preds_today = pd.read_sql("""
            SELECT COUNT(*) as total FROM ai_predictions
        """, conn).iloc[0]['total']
        
        # 5. Equipo con mayor riesgo
        highest_risk = pd.read_sql("""
            SELECT e.name, p.failure_probability 
            FROM ai_predictions p
            JOIN equipments e ON e.id = p.equipment_id
            ORDER BY p.failure_probability DESC
            LIMIT 1
        """, conn)
        
    return eq_status, alerts, preds_today, highest_risk

def render_kpis(eq_status, alerts, preds_today, highest_risk):
    """Muestra las tarjetas KPI en la parte superior."""
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    status_dict = dict(zip(eq_status['status'], eq_status['total']))
    operativos = status_dict.get('OPERATIVO', 0)
    en_mante = status_dict.get('EN_MANTENIMIENTO', 0)
    fuera = status_dict.get('FUERA_DE_SERVICIO', 0)
    total = operativos + en_mante + fuera
    disponibilidad = (operativos / total * 100) if total > 0 else 0
    
    with col1:
        st.metric("✅ Equipos Activos", operativos, f"{disponibilidad:.1f}% Disp.")
    with col2:
        st.metric("🛠️ En Mantenimiento", en_mante, delta_color="off")
    with col3:
        st.metric("❌ Con Falla", fuera, "- Crítico" if fuera > 0 else "OK", delta_color="inverse")
    with col4:
        st.metric("⚠️ Alertas (24h)", alerts, "Requiere Revisión" if alerts > 0 else "Normal", delta_color="inverse")
    with col5:
        st.metric("🤖 Predicciones IA", preds_today)
    with col6:
        if not highest_risk.empty:
            name = highest_risk.iloc[0]['name']
            prob = highest_risk.iloc[0]['failure_probability'] * 100
            st.metric("🔥 Mayor Riesgo", f"{name[:12]}...", f"{prob:.1f}%", delta_color="inverse")
        else:
            st.metric("🔥 Mayor Riesgo", "N/A")

def render_charts(selected_eq_id, start_date, end_date, selected_sensors):
    """Genera 4 gráficos interactivos con Plotly."""
    st.markdown("### Análisis Gráfico Interactivo")
    
    col_chart1, col_chart2 = st.columns(2)
    
    query_sensors = """
        SELECT sr.reading_timestamp, sr.reading_value, s.sensor_type, s.code, s.unit
        FROM sensor_readings sr
        JOIN sensors s ON sr.sensor_id = s.id
        WHERE s.equipment_id = %(eq_id)s
        AND sr.reading_timestamp >= %(start)s
        AND sr.reading_timestamp <= %(end)s
    """
    
    with engine.connect() as conn:
        df_sensors = pd.read_sql(query_sensors, conn, params={
            'eq_id': selected_eq_id,
            'start': start_date,
            'end': end_date + timedelta(days=1)
        })
        
        df_maint = pd.read_sql("""
            SELECT maintenance_type, COUNT(*) as count 
            FROM maintenances 
            WHERE equipment_id = %(eq_id)s
            GROUP BY maintenance_type
        """, conn, params={'eq_id': selected_eq_id})
        
        df_risk = pd.read_sql("""
            SELECT prediction_date, failure_probability, predicted_failure_type 
            FROM ai_predictions 
            WHERE equipment_id = %(eq_id)s
            ORDER BY prediction_date ASC
        """, conn, params={'eq_id': selected_eq_id})
    
    with col_chart1:
        if not df_sensors.empty and selected_sensors:
            df_sensors_filtered = df_sensors[df_sensors['sensor_type'].isin(selected_sensors)]
            if not df_sensors_filtered.empty:
                fig1 = px.line(df_sensors_filtered, x='reading_timestamp', y='reading_value', color='code',
                               title='1. Evolución Temporal de Sensores',
                               labels={'reading_timestamp': 'Fecha', 'reading_value': 'Valor'},
                               hover_data=['sensor_type', 'unit'])
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No hay datos para los tipos de sensor seleccionados.")
        else:
            st.info("No hay lecturas de sensores en el rango seleccionado.")
            
    with col_chart2:
        if not df_maint.empty:
            fig2 = px.pie(df_maint, values='count', names='maintenance_type',
                          title='2. Mantenimientos por Tipo',
                          color='maintenance_type',
                          color_discrete_map={'PREVENTIVO': '#2CA02C', 'CORRECTIVO': '#D62728', 'PREDICTIVO': '#FF7F0E'},
                          hole=0.4) # Donut chart para mejor estética
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay órdenes de mantenimiento para este equipo.")
            
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        if not df_risk.empty:
            fig3 = px.area(df_risk, x='prediction_date', y='failure_probability',
                           title='3. Evolución del Riesgo de Falla',
                           color_discrete_sequence=['#d62728'])
            fig3.update_layout(yaxis_tickformat='.0%')
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay predicciones IA históricas para este equipo.")
            
    with col_chart4:
        # Gauge de Riesgo
        current_risk = df_risk.iloc[-1]['failure_probability'] if not df_risk.empty else 0
        fig4 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_risk * 100,
            number={'suffix': "%"},
            title={'text': "4. Nivel de Riesgo Actual (IA)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "rgba(0,0,0,0.2)"},
                'steps': [
                    {'range': [0, 30], 'color': "#2ca02c"}, # Verde
                    {'range': [30, 70], 'color': "#ff7f0e"}, # Naranja
                    {'range': [70, 100], 'color': "#d62728"} # Rojo
                ]
            }
        ))
        st.plotly_chart(fig4, use_container_width=True)

def render_dashboard():
    user = st.session_state["user"]
    
    # Registro de auditoría
    if not st.session_state.get("dashboard_loaded_log"):
        log_action(user["id"], "VIEW_DASHBOARD", details="Visualización del Dashboard Principal interactivo")
        st.session_state["dashboard_loaded_log"] = True

    st.markdown("## 📊 Dashboard Principal: Mantenimiento Predictivo")
    
    # KPIs Globales
    eq_status, alerts, preds_today, highest_risk = get_kpi_data()
    render_kpis(eq_status, alerts, preds_today, highest_risk)
    st.divider()

    # Filtros
    st.sidebar.markdown("### 🔍 Filtros del Dashboard")
    eq_df, sens_df = load_filters_data()
    
    if eq_df.empty:
        st.warning("No hay equipos registrados en la base de datos.")
        return
        
    eq_options = dict(zip(eq_df['name'] + " (" + eq_df['code'] + ")", eq_df['id']))
    selected_eq_name = st.sidebar.selectbox("Seleccione un Equipo", list(eq_options.keys()))
    selected_eq_id = eq_options[selected_eq_name]
    
    date_range = st.sidebar.date_input("Rango de Fechas", 
                                       value=(datetime(2023, 10, 20), datetime(2023, 11, 20)))
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = datetime(2023, 10, 20), datetime(2023, 11, 20)
        
    sensor_types = sens_df['sensor_type'].tolist()
    selected_sensors = st.sidebar.multiselect("Tipos de Sensores", sensor_types, default=sensor_types)
    
    # Renderizar Gráficos
    render_charts(selected_eq_id, start_date, end_date, selected_sensors)
