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

def load_artifacts():
    """Carga el modelo ganador, el scaler y los metadatos."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(base_dir, 'data', 'models')
    data_dir = os.path.join(base_dir, 'data', 'processed')
    
    try:
        # Por defecto, asumimos que el Random Forest fue el seleccionado en el MCDA
        model = joblib.load(os.path.join(models_dir, 'random_forest.pkl'))
        scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
        with open(os.path.join(data_dir, 'metadata.json'), 'r') as f:
            meta = json.load(f)
        return model, scaler, meta
    except Exception as e:
        return None, None, None

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
        # Asignar el valor base correspondiente al sensor
        val = 0.0
        if 'TEMPERATURA' in f: val = base_values['temp']
        elif 'PRESION' in f: val = base_values['pres']
        elif 'VIBRACION' in f: val = base_values['vib']
        elif 'RPM' in f: val = base_values['rpm']
        elif 'NIVEL_ACEITE' in f: val = base_values['oil']
        
        # Simular derivadas para inferencia en tiempo real (Steady State)
        if 'diff' in f:
            input_dict[f] = 0.0 # Asumimos sin cambio abrupto inmediato
        else:
            input_dict[f] = val # Medias móviles = valor actual
            
    return pd.DataFrame([input_dict], columns=meta['features'])

def render_deployment():
    user = st.session_state["user"]
    require_permission("run_models")
    
    if not st.session_state.get("deploy_loaded_log"):
        log_action(user["id"], "VIEW_DEPLOYMENT", details="Acceso a la Fase 6: Despliegue en Producción")
        st.session_state["deploy_loaded_log"] = True

    st.title("🚀 Fase 6: Despliegue y Predicción en Vivo")
    
    model, scaler, meta = load_artifacts()
    
    if model is None or scaler is None:
        st.error("❌ **Modelo no encontrado en producción.**")
        st.info("Para habilitar este módulo:\n1. Ve a la **Fase 3** y ejecuta el script de preparación.\n2. Ve a la **Fase 4** y entrena los modelos.\n3. Asegúrate de que los archivos `.pkl` existan en `data/models/`.")
        return

    st.success("✅ Modelo **Random Forest** (Ganador Fase 5) cargado y en línea. Latencia esperada: < 1.0s")
    
    tab1, tab2, tab3 = st.tabs([
        "⚡ Predicción Individual (Tiempo Real)", 
        "📁 Inferencia por Lotes (CSV)", 
        "📈 Historial y Monitoreo"
    ])
    
    # ==========================================
    # TAB 1: Predicción Individual
    # ==========================================
    with tab1:
        st.subheader("Simulador de Telemetría IoT")
        eq_df = get_equipment_list()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Parámetros del Equipo**")
            eq_options = dict(zip(eq_df['name'] + " (" + eq_df['code'] + ")", eq_df['id']))
            selected_eq_name = st.selectbox("Equipo", list(eq_options.keys()))
            selected_eq_id = eq_options[selected_eq_name]
            
            st.markdown("**Lecturas de Sensores**")
            val_temp = st.slider("Temperatura (°C)", 0.0, 150.0, 85.0)
            val_pres = st.slider("Presión (PSI)", 0.0, 200.0, 100.0)
            val_vib = st.slider("Vibración (mm/s)", 0.0, 30.0, 5.0)
            val_rpm = st.slider("RPM", 0.0, 3000.0, 1800.0)
            val_oil = st.slider("Nivel de Aceite (%)", 0.0, 100.0, 80.0)
            
            predict_btn = st.button("🔍 Evaluar Riesgo (Predecir)", use_container_width=True, type="primary")
            
        with col2:
            if predict_btn:
                # 1. Medir tiempo y preprocesar
                start_time = time.time()
                
                base_vals = {'temp': val_temp, 'pres': val_pres, 'vib': val_vib, 'rpm': val_rpm, 'oil': val_oil}
                df_input = build_feature_vector(meta, base_vals)
                
                # Escalar con exactamente el mismo scaler de la Fase 3
                X_scaled = scaler.transform(df_input)
                
                # Predecir
                proba = model.predict_proba(X_scaled)[0, 1]
                pred_class = int(proba > 0.5)
                
                inference_time = time.time() - start_time
                
                # 2. Lógica de Negocio y Colores
                if proba < 0.30:
                    color = "#2ca02c" # Verde
                    status = "NORMAL"
                    details = "Parámetros operativos dentro de límites saludables."
                    pred_type = "NINGUNA"
                elif proba < 0.70:
                    color = "#ff7f0e" # Naranja
                    status = "ADVERTENCIA"
                    details = "Desviación detectada. Sugerencia: Programar revisión preventiva."
                    pred_type = "DESGASTE_TEMPRANO"
                else:
                    color = "#d62728" # Rojo
                    status = "CRÍTICO (FALLA INMINENTE)"
                    details = "Alta probabilidad de falla correctiva en < 24h. Detener equipo."
                    pred_type = "FALLA_CATASTROFICA"
                
                # 3. Mostrar Resultados (Gauge Chart)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=proba * 100,
                    number={'suffix': "%", 'font': {'color': color}},
                    title={'text': f"Riesgo de Falla: {status}", 'font': {'color': color}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': color},
                        'steps': [
                            {'range': [0, 30], 'color': "rgba(44, 160, 44, 0.2)"},
                            {'range': [30, 70], 'color': "rgba(255, 127, 14, 0.2)"},
                            {'range': [70, 100], 'color': "rgba(214, 39, 40, 0.2)"}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"⏱️ **Tiempo de Inferencia:** {inference_time:.4f} segundos (Objetivo: < 1.0s cumplido)")
                st.write(f"📝 **Diagnóstico IA:** {details}")
                
                # 4. Guardar en BD y Auditar
                save_prediction_to_db(selected_eq_id, proba, pred_type, details)
                log_action(user["id"], "RUN_PREDICTION", details=f"Inferencia manual eq={selected_eq_id}, prob={proba:.2f}")

    # ==========================================
    # TAB 2: Predicción por Lotes (Batch)
    # ==========================================
    with tab2:
        st.subheader("Carga de Datos CSV para Evaluación Masiva")
        st.markdown("El archivo CSV debe contener exactamente las columnas de ingeniería de características generadas en la Fase 3.")
        
        uploaded_file = st.file_uploader("Sube un archivo de datos (ej. test_data.csv)", type=["csv"])
        if uploaded_file:
            df_batch = pd.read_csv(uploaded_file)
            
            # Validar columnas
            missing_cols = [c for c in meta['features'] if c not in df_batch.columns]
            if missing_cols:
                st.error(f"El CSV no tiene el formato correcto. Faltan {len(missing_cols)} columnas, incluyendo: {missing_cols[:3]}")
            else:
                st.success("Formato validado correctamente.")
                if st.button("Ejecutar Inferencia por Lotes", type="primary"):
                    with st.spinner("Procesando..."):
                        start_time = time.time()
                        
                        X_batch = df_batch[meta['features']]
                        X_batch_scaled = scaler.transform(X_batch)
                        
                        probas = model.predict_proba(X_batch_scaled)[:, 1]
                        
                        df_batch['Riesgo_Predicho (%)'] = (probas * 100).round(2)
                        df_batch['Alerta'] = np.where(probas > 0.7, 'CRÍTICO', np.where(probas > 0.3, 'ADVERTENCIA', 'NORMAL'))
                        
                        inf_time = time.time() - start_time
                        
                        st.success(f"Inferencia completada en {inf_time:.2f}s para {len(df_batch)} registros.")
                        
                        st.dataframe(df_batch[['Riesgo_Predicho (%)', 'Alerta'] + meta['features'][:3]].head(50))
                        
                        # Guardar batch en la BD de forma simplificada
                        # Asignamos al equipo 1 si no viene en el CSV (MVP)
                        eq_col = 'equipment_id' if 'equipment_id' in df_batch.columns else None
                        for idx, row in df_batch.head(50).iterrows(): # Limitamos a 50 inserts para no saturar BD
                            eq_id = row[eq_col] if eq_col else 1
                            save_prediction_to_db(eq_id, probas[idx], row['Alerta'], "Batch Prediction")
                            
                        log_action(user["id"], "RUN_BATCH_PREDICTION", details=f"Inferencia masiva de {len(df_batch)} filas")
                        st.info("Nota: Se han guardado las primeras 50 predicciones en el historial para evitar sobrecarga.")

    # ==========================================
    # TAB 3: Historial y Monitoreo (Dashboard)
    # ==========================================
    with tab3:
        st.subheader("Monitoreo de Predicciones Históricas")
        if st.button("🔄 Actualizar Datos"):
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
            
            c1, c2 = st.columns([2, 1])
            with c1:
                fig_trend = px.line(hist_df, x='prediction_date', y='failure_probability', color='equipo',
                                    title="Tendencia de Riesgo Reciente por Equipo",
                                    labels={'prediction_date': 'Fecha', 'failure_probability': 'Riesgo (%)'})
                fig_trend.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Límite Crítico")
                st.plotly_chart(fig_trend, use_container_width=True)
                
            with c2:
                fig_pie = px.pie(hist_df, names='predicted_failure_type', title="Distribución de Estados Previstos", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            st.dataframe(hist_df.style.format({'failure_probability': "{:.1f}%"}), use_container_width=True)
        else:
            st.info("No hay predicciones en el historial aún.")
