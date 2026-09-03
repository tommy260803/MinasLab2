import streamlit as st
import pandas as pd
import plotly.express as px
import os
import tempfile
from datetime import datetime
from core.db_manager import engine
from core.audit_logger import log_action
from core.permissions import require_permission
from core.report_generator import generate_pdf, generate_word, generate_excel

def get_report_data(report_type, start_date, end_date):
    """Extrae los datos desde PostgreSQL según el tipo de reporte solicitado."""
    with engine.connect() as conn:
        if report_type == "Auditoría de Accesos":
            query = f"""
                SELECT u.username as Usuario, u.role_id as Rol, a.action as Accion, a.details as Detalles, a.ip_address as IP, a.created_at as Fecha
                FROM audit_logs a
                JOIN users u ON a.user_id = u.id
                WHERE a.created_at >= '{start_date}' AND a.created_at <= '{end_date} 23:59:59'
                ORDER BY a.created_at DESC
            """
        elif report_type == "Estado de Mantenimientos":
            query = f"""
                SELECT e.name as Equipo, e.code as Codigo, m.maintenance_type as Tipo, m.start_date as Fecha_Inicio, 
                       m.end_date as Fecha_Fin, m.cost as Costo, m.status as Estado
                FROM maintenances m
                JOIN equipments e ON m.equipment_id = e.id
                WHERE m.start_date >= '{start_date}' AND m.start_date <= '{end_date} 23:59:59'
                ORDER BY m.start_date DESC
            """
        elif report_type == "Historial de Predicciones AI":
            query = f"""
                SELECT e.name as Equipo, p.prediction_date as Fecha, (p.failure_probability * 100) as Probabilidad_Riesgo, 
                       p.predicted_failure_type as Estado_Predicho, p.details as Diagnostico
                FROM ai_predictions p
                JOIN equipments e ON p.equipment_id = e.id
                WHERE p.prediction_date >= '{start_date}' AND p.prediction_date <= '{end_date} 23:59:59'
                ORDER BY p.prediction_date DESC
            """
        else:
            return pd.DataFrame()
            
        df = pd.read_sql(query, conn)
    return df

def generate_dynamic_plot(df, report_type):
    """Genera un gráfico Plotly contextual para embeber en el reporte."""
    if df.empty: return None
    
    if report_type == "Auditoría de Accesos":
        return px.pie(df, names='Accion', title='Distribución de Acciones en el Sistema', hole=0.3)
    elif report_type == "Estado de Mantenimientos":
        return px.bar(df, x='Equipo', y='Costo', color='Tipo', title='Costos de Mantenimiento por Equipo y Tipo')
    elif report_type == "Historial de Predicciones AI":
        return px.line(df, x='Fecha', y='Probabilidad_Riesgo', color='Equipo', title='Evolución del Riesgo de Falla')
    
    return None

def render_reports():
    user = st.session_state["user"]
    require_permission("view_dashboard") # Se asume que roles altos (Admin/Analista) tienen este permiso
    
    if not st.session_state.get("reports_loaded_log"):
        log_action(user["id"], "VIEW_REPORTS", details="Acceso a Módulo de Reportes Profesionales")
        st.session_state["reports_loaded_log"] = True

    st.title("📄 Generador de Reportes Profesionales")
    st.markdown("Exporta la inteligencia de negocio y auditoría a formatos **PDF**, **Word (.docx)** o **Excel (.xlsx)**.")
    
    # 1. Filtros UI
    col1, col2, col3 = st.columns(3)
    with col1:
        report_types = ["Auditoría de Accesos", "Estado de Mantenimientos", "Historial de Predicciones AI"]
        report_type = st.selectbox("Tipo de Reporte", report_types)
    with col2:
        start_date = st.date_input("Fecha Inicio", value=pd.to_datetime('2023-01-01'))
    with col3:
        end_date = st.date_input("Fecha Fin", value=datetime.today())
        
    export_format = st.radio("Formato de Exportación", ["PDF", "Word (.docx)", "Excel (.xlsx)"], horizontal=True)
    
    # 2. Vista Previa de Datos
    st.subheader(f"Vista Previa: {report_type}")
    df = get_report_data(report_type, start_date, end_date)
    
    if df.empty:
        st.warning("No hay datos para el rango de fechas seleccionado.")
        return
        
    st.dataframe(df.head(10), use_container_width=True)
    st.caption(f"Total de registros encontrados: {len(df)}")
    
    # Gráfico en vivo
    fig = generate_dynamic_plot(df, report_type)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        
    # 3. Generación y Descarga
    st.divider()
    summary_text = f"Reporte filtrado desde {start_date} hasta {end_date}. Se encontraron {len(df)} registros relevantes. Datos generados bajo la cuenta de {user['username']}."
    
    if st.button(f"⚙️ Generar y Descargar Reporte en {export_format.split()[0]}", type="primary"):
        with st.spinner("Procesando reporte profesional..."):
            try:
                # Si hay gráfico y es PDF/Word, tratar de guardarlo como imagen temporal
                img_path = None
                if fig and "Excel" not in export_format:
                    try:
                        temp_dir = tempfile.gettempdir()
                        img_path = os.path.join(temp_dir, 'temp_plot.png')
                        fig.write_image(img_path, engine="kaleido")
                    except Exception as e:
                        img_path = None # Falla silenciosa si kaleido no está disponible
                
                # Enrutar al generador correcto
                title = f"Reporte de {report_type}"
                if "PDF" in export_format:
                    file_bytes = generate_pdf(title, summary_text, df, img_path)
                    mime = "application/pdf"
                    ext = "pdf"
                elif "Word" in export_format:
                    file_bytes = generate_word(title, summary_text, df, img_path)
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    ext = "docx"
                else:
                    file_bytes = generate_excel(title, summary_text, df)
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ext = "xlsx"
                    
                # Registrar auditoría de exportación
                log_action(user["id"], "EXPORT_REPORT", details=f"Exportó {report_type} en formato {ext}")
                
                # Limpiar imagen temporal
                if img_path and os.path.exists(img_path):
                    os.remove(img_path)
                
                # Entregar archivo
                file_name = f"Reporte_{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.{ext}"
                
                st.success("✅ ¡Reporte generado exitosamente!")
                st.download_button(
                    label=f"⬇️ Descargar {file_name}",
                    data=file_bytes,
                    file_name=file_name,
                    mime=mime
                )
            except Exception as e:
                st.error(f"Error generando el reporte: {e}")
                st.exception(e)
