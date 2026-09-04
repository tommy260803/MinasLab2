import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime
from core.audit_logger import log_action
from core.permissions import require_permission

def get_phase3_status():
    """Verifica si la Fase 3 ha sido ejecutada y retorna su estado."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    models_dir = os.path.join(base_dir, 'data', 'models')
    
    metadata_path = os.path.join(processed_dir, 'metadata.json')
    scaler_path = os.path.join(models_dir, 'scaler.pkl')
    
    has_metadata = os.path.exists(metadata_path)
    has_scaler = os.path.exists(scaler_path)
    
    status = {
        'executed': has_metadata and has_scaler,
        'metadata': None,
        'files': {
            'train_data.csv': os.path.exists(os.path.join(processed_dir, 'train_data.csv')),
            'val_data.csv': os.path.exists(os.path.join(processed_dir, 'val_data.csv')),
            'test_data.csv': os.path.exists(os.path.join(processed_dir, 'test_data.csv')),
            'metadata.json': has_metadata,
            'scaler.pkl': has_scaler
        }
    }
    
    if has_metadata:
        with open(metadata_path, 'r') as f:
            status['metadata'] = json.load(f)
    
    return status

def render_data_preparation():
    user = st.session_state["user"]
    require_permission("run_models")
    
    if not st.session_state.get("phase3_loaded_log"):
        log_action(user["id"], "VIEW_PHASE3", details="Acceso a Fase 3: Preparación de Datos")
        st.session_state["phase3_loaded_log"] = True
    
    st.markdown("## 📊 Fase 3: Preparación de Datos")
    st.markdown("*Data Preparation - Pipeline CRISP-DM*")
    
    status = get_phase3_status()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Estado", "✅ Ejecutada" if status['executed'] else "❌ Pendiente")
    with col2:
        if status['metadata']:
            st.metric("Filas Train", f"{status['metadata'].get('rows_train', 0):,}")
        else:
            st.metric("Filas Train", "N/A")
    with col3:
        if status['metadata']:
            st.metric("Features", len(status['metadata'].get('features', [])))
        else:
            st.metric("Features", "N/A")
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📋 Estado Actual", "⚙️ Ejecutar Pipeline", "📖 Documentación"])
    
    with tab1:
        st.subheader("Archivos Generados")
        
        files_data = []
        for filename, exists in status['files'].items():
            files_data.append({
                'Archivo': filename,
                'Estado': '✅ Existe' if exists else '❌ No encontrado'
            })
        
        df_files = pd.DataFrame(files_data)
        st.dataframe(df_files, use_container_width=True, hide_index=True)
        
        if status['metadata']:
            st.markdown("### 📊 Metadatos del Pipeline")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.json({
                    'target': status['metadata'].get('target'),
                    'rows_train': status['metadata'].get('rows_train'),
                    'rows_val': status['metadata'].get('rows_val'),
                    'rows_test': status['metadata'].get('rows_test')
                })
            with col_b:
                st.json({
                    'class_balance': status['metadata'].get('class_balance_train'),
                    'num_features': len(status['metadata'].get('features', []))
                })
        else:
            st.warning("⚠️ No hay metadatos disponibles. Ejecuta el pipeline primero.")
    
    with tab2:
        st.subheader("Ejecutar Pipeline de Preparación")
        
        st.markdown("""
        Esta acción ejecuta la **Fase 3 de CRISP-DM** completa:
        1. Extracción de datos crudos desde PostgreSQL (sensores IoT)
        2. Limpieza: eliminación de duplicados, imputación de nulos, winsorization de outliers
        3. Ingeniería de características: rolling windows, diferencias temporales
        4. Creación de variable objetivo (pre-falla 24 horas)
         5. División temporal (70/15/15) y normalización (StandardScaler)
        """)
        
        if status['executed']:
            st.warning("⚠️ **Atención:** Esto sobrescribirá los datos preparados actuales y el scaler.")
        
        if st.button("🚀 Ejecutar Fase 3: Preparación de Datos", type="primary", use_container_width=True):
            log_action(user["id"], "RUN_PHASE3", details="Inicio del pipeline Fase 3: Preparación de Datos")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                from ml.phase3_data_preparation import run_phase3
                
                status_text.text("📊 Iniciando Fase 3: Preparación de Datos...")
                progress_bar.progress(10)
                
                start_time = time.time()
                
                import io
                import contextlib
                
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    run_phase3()
                
                training_output = f.getvalue()
                elapsed = time.time() - start_time
                
                progress_bar.progress(100)
                status_text.text("✅ Preparación de datos completada!")
                
                st.success(f"🎉 **Pipeline completado en {elapsed:.1f} segundos.**")
                
                with st.expander("📋 Salida del Pipeline (Log)", expanded=False):
                    st.code(training_output, language=None)
                
                log_action(user["id"], "PHASE3_COMPLETED", details=f"Pipeline Fase 3 completado en {elapsed:.1f}s")
                
                st.rerun()
                
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ Error en la ejecución")
                st.error(f"Error durante la ejecución: {e}")
                st.exception(e)
                log_action(user["id"], "PHASE3_FAILED", details=f"Error: {str(e)[:200]}")
    
    with tab3:
        st.subheader("Documentación de la Fase 3")
        
        st.markdown("""
        ### 📖 ¿Qué hace la Fase 3?
        
        La Fase 3 de CRISP-DM (Data Preparation) transforma los datos crudos en un dataset listo para el entrenamiento de modelos de Machine Learning.
        
        ### 🔄 Pipeline Completo
        
        #### 1. Extracción de Datos
        - **Fuente:** PostgreSQL (tablas `sensor_readings`, `sensors`, `maintenances`)
        - **Variables:** TEMPERATURA, PRESION, VIBRACION, RPM, NIVEL_ACEITE
        
        #### 2. Limpieza de Datos
        - Eliminación de duplicados
        - Imputación de valores nulos (forward-fill para series temporales)
        - Winsorization de outliers extremos (1% - 99%)
        
        #### 3. Ingeniería de Características
        - **Rolling Windows:** Media y desviación estándar en ventanas de 3 registros
        - **Diferencias Temporales:** Tasa de cambio entre registros consecutivos
        
        #### 4. Variable Objetivo
        - **Target binario:** 1 si el equipo falla en las próximas 24 horas, 0 en caso contrario
        - Basado en mantenimientos correctivos históricos
        
        #### 5. División y Normalización
        - **Split temporal:** 70% train, 15% validación, 15% test
        - **Normalización:** StandardScaler (fit solo en train para evitar data leakage)
        
        ### 📁 Archivos Generados
        
        | Archivo | Descripción |
        |---------|-------------|
        | `train_data.csv` | Datos de entrenamiento (70%) |
        | `val_data.csv` | Datos de validación (15%) |
        | `test_data.csv` | Datos de prueba (15%) |
        | `scaler.pkl` | Scaler ajustado para normalización |
        | `metadata.json` | Metadatos del pipeline |
        """)
