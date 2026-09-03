import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import time
from datetime import datetime
from sqlalchemy import text
from core.db_manager import engine
from core.audit_logger import log_action
from core.permissions import require_permission
import json
from sklearn.impute import SimpleImputer
from app.components.ui_styles import (
    page_header, section_header, render_styled_table,
    card_container_begin, card_container_end
)

def load_artifacts():
    """Carga el modelo ganador, el scaler y los metadatos."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(base_dir, 'data', 'models')
    data_dir = os.path.join(base_dir, 'data', 'processed')
    
    try:
        scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
        with open(os.path.join(data_dir, 'metadata.json'), 'r') as f:
            meta = json.load(f)
        
        eval_path = os.path.join(data_dir, 'evaluation_results.pkl')
        model_name = 'Random Forest'
        if os.path.exists(eval_path):
            eval_results = joblib.load(eval_path)
            best_f1 = -1
            for name, metrics in eval_results.get('metrics', {}).items():
                if metrics.get('F1-Score', 0) > best_f1:
                    best_f1 = metrics['F1-Score']
                    model_name = name
        
        model_map = {
            'Random Forest': 'random_forest.pkl',
            'XGBoost': 'xgboost.pkl',
            'SVM (RBF)': 'svm.pkl'
        }
        model_file = model_map.get(model_name, 'random_forest.pkl')
        model = joblib.load(os.path.join(models_dir, model_file))
        
        return model, scaler, meta, model_name
    except Exception as e:
        return None, None, None, None

def save_prediction_to_db(eq_id, prob, pred_type, details):
    """Persiste la predicción en PostgreSQL con trazabilidad."""
    try:
        with engine.begin() as conn: # begin() maneja el commit automático
            query = text("""
                INSERT INTO ai_predictions (equipment_id, failure_probability, predicted_failure_type, details, prediction_date)
                VALUES (:eq_id, :prob, :pred_type, :details, :pdate)
            """)
            conn.execute(query, {
                'eq_id': eq_id, 
                'prob': float(prob), 
                'pred_type': pred_type, 
                'details': details,
                'pdate': datetime.now()
            })
    except Exception as e:
        st.error(f"Error de base de datos al guardar predicción: {e}")

def get_equipment_list():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT id, code, name FROM equipments", conn)
    return df

def build_feature_vector(meta, base_values):
    """Reconstruye el vector de características exacto usado en entrenamiento."""
    input_dict = {}
    for f in meta['features']:
        val = 0.0
        if 'TEMPERATURA' in f: val = base_values['temp']
        elif 'PRESION' in f: val = base_values['pres']
        elif 'VIBRACION' in f: val = base_values['vib']
        elif 'RPM' in f: val = base_values['rpm']
        elif 'NIVEL_ACEITE' in f: val = base_values['oil']
        
        if 'diff' in f:
            input_dict[f] = 0.0
        else:
            input_dict[f] = val
            
    return pd.DataFrame([input_dict], columns=meta['features'])

def render_deployment():
    user = st.session_state["user"]
    require_permission("run_models")
    
    if not st.session_state.get("deploy_loaded_log"):
        log_action(user["id"], "VIEW_DEPLOYMENT", details="Acceso a la Fase 6: Despliegue en Producción")
        st.session_state["deploy_loaded_log"] = True

    page_header("Despliegue y Predicción en Vivo", "Entorno de Producción e Inferencia (Fase 6)")
    
    model, scaler, meta, model_name = load_artifacts()
    
    if model is None or scaler is None:
        st.error("❌ **Modelo no encontrado en producción.**")
        st.info("Para habilitar este módulo:\n1. Ve a la **Fase 3** y ejecuta el script de preparación.\n2. Ve a la **Fase 4** y entrena los modelos.\n3. Asegúrate de que los archivos `.pkl` existan en `data/models/`.")
        return

    st.success(f"✅ Modelo Activo: **{model_name}** | Latencia Esperada: < 1.0s")
    
    tab1, tab2, tab3 = st.tabs([
        "⚡ Predicción Individual (Tiempo Real)", 
        "📁 Inferencia por Lotes (CSV)", 
        "📈 Monitoreo de Desempeño"
    ])
    
    # ==========================================
    # TAB 1: Predicción Individual
    # ==========================================
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Simulador de Telemetría IoT")
        eq_df = get_equipment_list()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            card_container_begin()
            st.markdown("<div style='font-size: 14px; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 12px;'>Parámetros de Operación</div>", unsafe_allow_html=True)
            eq_options = dict(zip(eq_df['name'] + " (" + eq_df['code'] + ")", eq_df['id']))
            selected_eq_name = st.selectbox("Equipo Asignado", list(eq_options.keys()))
            selected_eq_id = eq_options[selected_eq_name]
            
            st.markdown("<hr style='border: none; border-top: 1px solid #2D3139; margin: 16px 0;'>", unsafe_allow_html=True)
            val_temp = st.slider("Temperatura (°C)", 0.0, 150.0, 85.0)
            val_pres = st.slider("Presión (PSI)", 0.0, 200.0, 100.0)
            val_vib = st.slider("Vibración (mm/s)", 0.0, 30.0, 5.0)
            val_rpm = st.slider("Velocidad (RPM)", 0.0, 3000.0, 1800.0)
            val_oil = st.slider("Nivel de Lubricante (%)", 0.0, 100.0, 80.0)
            st.markdown("<br>", unsafe_allow_html=True)
            predict_btn = st.button("Evaluar Riesgo Operativo", use_container_width=True, type="primary")
            card_container_end()
            
        with col2:
            if predict_btn:
                card_container_begin()
                start_time = time.time()
                
                base_vals = {'temp': val_temp, 'pres': val_pres, 'vib': val_vib, 'rpm': val_rpm, 'oil': val_oil}
                df_input = build_feature_vector(meta, base_vals)
                
                imputer = SimpleImputer(strategy='median')
                df_input = pd.DataFrame(imputer.fit_transform(df_input), columns=df_input.columns)
                
                X_scaled = scaler.transform(df_input)
                
                proba = model.predict_proba(X_scaled)[0, 1]
                pred_class = int(proba > 0.5)
                
                inference_time = time.time() - start_time
                
                if proba < 0.30:
                    color = "#00C853" 
                    status = "ESTADO NORMAL"
                    details = "Parámetros operativos dentro de límites saludables."
                    pred_type = "NINGUNA"
                elif proba < 0.70:
                    color = "#FFAB00"
                    status = "ADVERTENCIA"
                    details = "Desviación detectada. Sugerencia: Programar revisión preventiva."
                    pred_type = "DESGASTE_TEMPRANO"
                else:
                    color = "#D50000"
                    status = "ESTADO CRÍTICO"
                    details = "Alta probabilidad de falla. Detener equipo inmediatamente."
                    pred_type = "FALLA_CATASTROFICA"
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=proba * 100,
                    number={'suffix': "%", 'font': {'color': color, 'size': 48}},
                    title={'text': f"Riesgo de Falla Operativa", 'font': {'color': '#94A3B8', 'size': 14}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickcolor': '#2D3139'},
                        'bar': {'color': color, 'thickness': 0.3},
                        'bgcolor': "rgba(0,0,0,0)",
                        'borderwidth': 0,
                        'steps': [
                            {'range': [0, 30], 'color': "rgba(0, 200, 83, 0.1)"},
                            {'range': [30, 70], 'color': "rgba(255, 171, 0, 0.1)"},
                            {'range': [70, 100], 'color': "rgba(213, 0, 0, 0.1)"}
                        ]
                    }
                ))
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown(f"**Diagnóstico del Modelo:** <span style='color: {color}; font-weight: 600;'>{status}</span>", unsafe_allow_html=True)
                st.write(f"📝 {details}")
                st.markdown(f"<div style='font-size: 12px; color: #94A3B8; margin-top: 16px;'>⏱️ Tiempo de Inferencia: {inference_time:.4f}s</div>", unsafe_allow_html=True)
                
                save_prediction_to_db(selected_eq_id, proba, pred_type, details)
                log_action(user["id"], "RUN_PREDICTION", details=f"Inferencia manual eq={selected_eq_id}, prob={proba:.2f}")
                card_container_end()

    # ==========================================
    # TAB 2: Predicción por Lotes (Batch)
    # ==========================================
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Inferencia Masiva mediante Archivos")
        st.markdown("<p style='color: #94A3B8; font-size: 14px;'>El archivo debe contener el vector de características (Feature Engineering) generado en la Fase 3.</p>", unsafe_allow_html=True)
        
        card_container_begin()
        uploaded_file = st.file_uploader("Seleccione un archivo (.csv)", type=["csv"])
        if uploaded_file:
            df_batch = pd.read_csv(uploaded_file)
            
            missing_cols = [c for c in meta['features'] if c not in df_batch.columns]
            if missing_cols:
                st.error(f"El CSV no tiene el formato correcto. Faltan {len(missing_cols)} columnas, incluyendo: {missing_cols[:3]}")
            else:
                st.success("Formato validado. Listo para inferencia.")
                if st.button("Procesar Lote de Datos", type="primary"):
                    with st.spinner("Procesando inferencia..."):
                        start_time = time.time()
                        
                        X_batch = df_batch[meta['features']]
                        imputer = SimpleImputer(strategy='median')
                        X_batch = pd.DataFrame(imputer.fit_transform(X_batch), columns=X_batch.columns)
                        X_batch_scaled = scaler.transform(X_batch)
                        
                        probas = model.predict_proba(X_batch_scaled)[:, 1]
                        
                        df_batch['Riesgo_Predicho (%)'] = (probas * 100).round(2)
                        df_batch['Alerta'] = np.where(probas > 0.7, 'CRÍTICO', np.where(probas > 0.3, 'ADVERTENCIA', 'NORMAL'))
                        
                        inf_time = time.time() - start_time
                        
                        st.success(f"Inferencia completada en {inf_time:.2f}s para {len(df_batch)} registros.")
                        
                        render_styled_table(df_batch[['Riesgo_Predicho (%)', 'Alerta'] + meta['features'][:3]].head(50))
                        
                        eq_col = 'equipment_id' if 'equipment_id' in df_batch.columns else None
                        for idx, row in df_batch.head(50).iterrows(): 
                            eq_id = row[eq_col] if eq_col else 1
                            save_prediction_to_db(eq_id, probas[idx], row['Alerta'], "Batch Prediction")
                            
                        log_action(user["id"], "RUN_BATCH_PREDICTION", details=f"Inferencia masiva de {len(df_batch)} filas")
                        st.info("Nota: Se han guardado las primeras 50 predicciones en el historial del sistema.")
        card_container_end()

    # ==========================================
    # TAB 3: Historial y Monitoreo (Dashboard)
    # ==========================================
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Registro Histórico de Evaluaciones (Live)")
        
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("🔄 Refrescar Monitor", use_container_width=True):
                pass
            
        with engine.connect() as conn:
            hist_df = pd.read_sql("""
                SELECT p.prediction_date, e.name as equipo, p.failure_probability, p.predicted_failure_type, p.details
                FROM ai_predictions p
                JOIN equipments e ON p.equipment_id = e.id
                ORDER BY p.prediction_date DESC
                LIMIT 200
            """, conn)
            
        if not hist_df.empty:
            hist_df['failure_probability'] = hist_df['failure_probability'] * 100
            
            c1, c2 = st.columns([6, 4])
            with c1:
                card_container_begin()
                fig_trend = px.line(hist_df, x='prediction_date', y='failure_probability', color='equipo',
                                    title="Tendencia Operativa Continua",
                                    labels={'prediction_date': 'Fecha', 'failure_probability': 'Riesgo (%)'})
                fig_trend.add_hline(y=70, line_dash="dash", line_color="#D50000", annotation_text="Límite Crítico")
                fig_trend.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_trend, use_container_width=True)
                card_container_end()
                
            with c2:
                card_container_begin()
                fig_pie = px.pie(hist_df, names='predicted_failure_type', title="Distribución de Estados Previstos", hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
                fig_pie.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_pie, use_container_width=True)
                card_container_end()
                
            card_container_begin()
            st.markdown("<div style='font-size: 14px; font-weight: 600; margin-bottom: 12px;'>Últimos 200 Registros de Inferencia</div>", unsafe_allow_html=True)
            render_styled_table(hist_df)
            card_container_end()
        else:
            st.info("No hay predicciones en el historial aún.")
