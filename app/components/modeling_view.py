import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import json
import time
from datetime import datetime
from core.audit_logger import log_action
from core.permissions import require_permission
from app.components.ui_styles import (
    page_header, section_header, render_styled_table, render_kpi_card,
    card_container_begin, card_container_end
)

def get_models_status():
    """Verifica qué modelos están entrenados y disponibles."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(base_dir, 'data', 'models')
    data_dir = os.path.join(base_dir, 'data', 'processed')
    
    models_info = {
        'Random Forest': {'file': 'random_forest.pkl', 'type': 'Tradicional', 'framework': 'Scikit-Learn'},
        'XGBoost': {'file': 'xgboost.pkl', 'type': 'Tradicional', 'framework': 'XGBoost'},
        'SVM (RBF)': {'file': 'svm.pkl', 'type': 'Tradicional', 'framework': 'Scikit-Learn'},
        'CNN-LSTM': {'file': 'cnn_lstm.keras', 'type': 'Híbrido (Deep Learning)', 'framework': 'TensorFlow/Keras'},
        'LSTM-AE + RF': {'file': 'lstm_ae_rf.pkl', 'type': 'Híbrido (Ensamble)', 'framework': 'TensorFlow + Scikit-Learn'}
    }
    
    status = {}
    for name, info in models_info.items():
        file_path = os.path.join(models_dir, info['file'])
        exists = os.path.exists(file_path)
        size = os.path.getsize(file_path) / 1024 if exists else 0
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M') if exists else 'N/A'
        status[name] = {
            **info,
            'trained': exists,
            'size_kb': round(size, 2),
            'last_modified': mod_time
        }
    
    return status

def get_training_metadata():
    """Carga metadatos del entrenamiento si existen."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    meta_path = os.path.join(base_dir, 'data', 'processed', 'metadata.json')
    
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            return json.load(f)
    return None

def get_algorithm_details():
    """Retorna información detallada de cada algoritmo."""
    return {
        'Random Forest': {
            'description': 'Ensamble de árboles de decisión entrenados con bagging. Robusto ante overfitting y maneja bien datos desbalanceados con class_weight="balanced".',
            'params': 'n_estimators=150, max_depth=12, class_weight=balanced',
            'pros': ['Robusto ante overfitting', 'No requiere escalado', 'Maneja desbalanceo', 'Feature importance'],
            'cons': ['Menor interpretabilidad que un solo árbol', 'Puede ser lento con muchos árboles']
        },
        'XGBoost': {
            'description': 'Gradient Boosting optimizado con regularización L1/L2. Usa early stopping para prevenir overfitting. Estado del arte en competiciones Kaggle.',
            'params': 'n_estimators=300, learning_rate=0.05, max_depth=6, eval_metric=auc',
            'pros': ['Alto rendimiento', 'Regularización incorporada', 'Early stopping', 'Maneja valores nulos'],
            'cons': ['Sensible a hiperparámetros', 'Requiere más tiempo de entrenamiento']
        },
        'SVM (RBF)': {
            'description': 'Support Vector Machine con kernel RBF. Excelente en espacios de alta dimensionalidad. Busca el hiperplano de máximo margen.',
            'params': 'kernel=rbf, C=1.0, gamma=scale, class_weight=balanced',
            'pros': ['Efectivo en alta dimensionalidad', 'Kernel no lineal', 'Memoria eficiente'],
            'cons': ['Lento con grandes volúmenes', 'Sensible a escala', 'No genera probabilidades directamente']
        },
        'CNN-LSTM': {
            'description': 'Híbrido que combina capas convolucionales (extraen patrones locales) con LSTM (capturan dependencias temporales a largo plazo).',
            'params': 'Conv1D(64) + MaxPooling + LSTM(64) + Dense(32)',
            'pros': ['Captura patrones espaciales y temporales', 'Auto-extracción de features', 'Estado del arte en series'],
            'cons': ['Requiere grandes datos', 'Costoso computacionalmente', 'Caja negra']
        },
        'LSTM-AE + RF': {
            'description': 'Ensamble en dos etapas: un Autoencoder LSTM extrae representación latente no lineal, luego un Random Forest clasifica.',
            'params': 'Encoder LSTM(32) → RF(n_estimators=100)',
            'pros': ['Reduce dimensionalidad no lineal', 'Combinación potente', 'Representación latente robusta'],
            'cons': ['Complejo de implementar', 'Dos etapas de entrenamiento', 'Difícil de interpretar']
        }
    }

def render_modeling():
    user = st.session_state["user"]
    require_permission("run_models")
    
    if not st.session_state.get("modeling_loaded_log"):
        log_action(user["id"], "VIEW_MODELING", details="Acceso al Motor de IA (Fase 4: Modelado)")
        st.session_state["modeling_loaded_log"] = True

    page_header("Motor de Inteligencia Artificial", "Entrenamiento de algoritmos predictivos (CRISP-DM Fase 4)")
    
    models_status = get_models_status()
    metadata = get_training_metadata()
    trained_count = sum(1 for m in models_status.values() if m['trained'])
    total_models = len(models_status)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Modelos Entrenados", f"{trained_count}/{total_models}", "success" if trained_count == total_models else "warning", "Progreso del pipeline", "🧠")
    with col2:
        feats = len(metadata.get('features', [])) if metadata else 0
        render_kpi_card("Features Generadas", str(feats) if metadata else "N/A", "neutral", "Variables derivadas", "✨")
    with col3:
        rows = metadata.get('rows_train', 0) if metadata else 0
        render_kpi_card("Filas de Train", f"{rows:,}" if metadata else "N/A", "neutral", "Volumen de datos", "💾")
    with col4:
        if metadata:
            balance = metadata.get('class_balance_train', {})
            pos_pct = balance.get('1', 0) * 100
            render_kpi_card("Desbalance Clase Falla", f"{pos_pct:.1f}%", "warning", "Requiere compensación", "⚖️")
        else:
            render_kpi_card("Clase Positiva", "N/A", "neutral", None, "⚖️")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Estado de Modelos",
        "🔬 Detalle de Algoritmos",
        "⚙️ Ejecutar Pipeline",
        "📈 Arquitectura"
    ])
    
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Estado de los Modelos en Disco")
        
        status_data = []
        for name, info in models_status.items():
            status_data.append({
                'Modelo': name,
                'Tipo': info['type'],
                'Framework': info['framework'],
                'Estado': '✅ Entrenado' if info['trained'] else '❌ No entrenado',
                'Tamaño (KB)': info['size_kb'] if info['trained'] else 0,
                'Última Modificación': info['last_modified']
            })
        
        df_status = pd.DataFrame(status_data)
        
        card_container_begin()
        render_styled_table(df_status)
        card_container_end()
        
        if trained_count == 0:
            st.warning("⚠️ No hay modelos entrenados. Ve a la pestaña 'Ejecutar Pipeline' para compilar la inteligencia.")
        elif trained_count < total_models:
            st.info(f"ℹ️ Hay {total_models - trained_count} modelo(s) sin entrenar. Considera ejecutar el pipeline completo.")
        else:
            st.success(f"✅ Todos los modelos están entrenados y disponibles.")
        
        if metadata:
            st.markdown("### 📋 Metadatos del Dataset Procesado")
            card_container_begin()
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Particiones:**")
                st.json({
                    'target': metadata.get('target'),
                    'rows_train': metadata.get('rows_train'),
                    'rows_val': metadata.get('rows_val'),
                    'rows_test': metadata.get('rows_test')
                })
            with col_b:
                st.markdown("**Ingeniería de Características:**")
                st.json({
                    'class_balance': metadata.get('class_balance_train'),
                    'num_features': len(metadata.get('features', []))
                })
            card_container_end()
    
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Detalle Teórico de Algoritmos Implementados")
        
        algo_details = get_algorithm_details()
        
        for name, details in algo_details.items():
            info = models_status[name]
            with st.expander(f"{'✅' if info['trained'] else '❌'} **{name}** — {info['type']}", expanded=False):
                st.markdown(f"**Descripción:** {details['description']}")
                st.code(f"Hiperparámetros base: {details['params']}", language="python")
                
                col_p, col_c = st.columns(2)
                with col_p:
                    st.markdown("<span style='color:#00C853; font-weight:bold;'>Ventajas Competitivas:</span>", unsafe_allow_html=True)
                    for pro in details['pros']:
                        st.markdown(f"- ✅ {pro}")
                with col_c:
                    st.markdown("<span style='color:#FFAB00; font-weight:bold;'>Limitaciones Técnicas:</span>", unsafe_allow_html=True)
                    for con in details['cons']:
                        st.markdown(f"- ⚠️ {con}")
    
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Ejecución del Pipeline de Entrenamiento")
        
        card_container_begin()
        st.markdown("""
        Esta acción ejecuta la **Fase 4 de CRISP-DM** de forma automatizada:
        1. Carga los datos preparados (tensores y dataframes) de la Fase 3.
        2. Entrena los 3 algoritmos tradicionales (RF, XGBoost, SVM).
        3. Entrena los 2 algoritmos híbridos profundos (CNN-LSTM, LSTM-AE+RF).
        4. Serializa todos los modelos en disco para inferencia de baja latencia.
        """)
        
        if trained_count > 0:
            st.warning("⚠️ **Atención:** Esto reentrenará TODOS los modelos existentes. Las métricas previas se sobreescribirán.")
        
        if not metadata:
            st.error("❌ No se encontraron datos preparados. Debes ejecutar primero la Fase 3 (Data Preparation).")
        else:
            st.success(f"✅ Datos listos en memoria compartida: {metadata.get('rows_train', 0):,} instancias vectorizadas.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Lanzar Pipeline de Entrenamiento Completo", type="primary", use_container_width=True):
                log_action(user["id"], "RUN_TRAINING", details="Inicio del pipeline de entrenamiento Fase 4")
                
                st.markdown("<br>", unsafe_allow_html=True)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    from ml.phase4_modeling import run_phase4
                    
                    status_text.markdown("**🧠 Inicializando hiperparámetros y allocando memoria...**")
                    progress_bar.progress(10)
                    
                    start_time = time.time()
                    
                    import io
                    import contextlib
                    
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        run_phase4()
                    
                    training_output = f.getvalue()
                    elapsed = time.time() - start_time
                    
                    progress_bar.progress(100)
                    status_text.markdown("**✅ Pipeline completado satisfactoriamente.**")
                    
                    st.success(f"🎉 **Entrenamiento completado en {elapsed:.1f} segundos.**")
                    
                    with st.expander("📋 Ver Log de Sistema de la Corrida", expanded=False):
                        st.code(training_output, language="shell")
                    
                    log_action(user["id"], "TRAINING_COMPLETED", details=f"Pipeline Fase 4 completado en {elapsed:.1f}s")
                    
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.error("❌ Excepción capturada durante el entrenamiento.")
                    st.error(f"Error interno: {e}")
                    log_action(user["id"], "TRAINING_FAILED", details=f"Error: {str(e)[:200]}")
        card_container_end()
    
    with tab4:
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Arquitectura Lógica CRISP-DM")
        
        phases = [
            {"name": "Fase 1: Business Understanding", "status": "Completada", "color": "green", "desc": "Definición del problema: mantenimiento predictivo para equipos de carguío minero. Objetivos: reducir MTTR ≥20%, aumentar disponibilidad ≥5%."},
            {"name": "Fase 2: Data Understanding", "status": "Completada", "color": "green", "desc": "Análisis de fuentes de datos (PostgreSQL): sensores IoT, equipos, mantenimientos. Variables: TEMPERATURA, PRESION, VIBRACION, RPM, NIVEL_ACEITE."},
            {"name": "Fase 3: Data Preparation", "status": "Completada", "color": "green", "desc": "Feature engineering: rolling windows, diferencias temporales. Limpieza: nulos, duplicados, winsorization de outliers. División temporal 70/15/15."},
            {"name": "Fase 4: Modeling (Motor IA)", "status": "Activa", "color": "blue", "desc": "Entrenamiento de 5 algoritmos: 3 tradicionales (RF, XGBoost, SVM) y 2 híbridos (CNN-LSTM, LSTM-AE+RF). Uso de class_weight para desbalanceo."},
            {"name": "Fase 5: Evaluation", "status": "Pendiente", "color": "orange", "desc": "Evaluación rigurosa: validación cruzada (KFold, Stratified, TimeSeries), pruebas estadísticas (McNemar, T-Test), selección multicriterio (MCDA)."},
            {"name": "Fase 6: Deployment", "status": "Pendiente", "color": "orange", "desc": "Despliegue en producción: predicción individual en tiempo real, inferencia por lotes (CSV), monitoreo de historial de predicciones."}
        ]
        
        card_container_begin()
        for phase in phases:
            color_map = {"green": "🟢", "blue": "🔵", "orange": "🟠", "red": "🔴"}
            icon = color_map.get(phase["color"], "⚪")
            st.markdown(f"<div style='font-size: 15px; font-weight: 600; color: #E2E8F0; margin-bottom: 4px;'>{icon} {phase['name']} <span style='font-size: 12px; color: #94A3B8; font-weight: normal; margin-left: 8px;'>[{phase['status']}]</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 13px; color: #94A3B8; margin-bottom: 16px;'>{phase['desc']}</div>", unsafe_allow_html=True)
            if phase != phases[-1]:
                st.markdown("<hr style='border: none; border-top: 1px solid #2D3139; margin: 0 0 16px 0;'>", unsafe_allow_html=True)
        card_container_end()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🏗️ Arquitectura de Procesamiento (Topología)")
        st.markdown("""
        ```
        ┌─────────────────────────────────────────────────────┐
        │              MOTOR DE INTELIGENCIA ARTIFICIAL       │
        ├──────────────────────┬──────────────────────────────┤
        │   ALGORITMOS         │   ALGORITMOS                 │
        │   TRADICIONALES      │   HÍBRIDOS (Deep Learning)   │
        ├──────────────────────┼──────────────────────────────┤
        │ • Random Forest      │ • CNN-LSTM                   │
        │ • XGBoost            │ • LSTM-Autoencoder + RF      │
        │ • SVM (RBF)          │                              │
        ├──────────────────────┴──────────────────────────────┤
        │  Data Pipeline: PostgreSQL → Feature Engineering    │
        │  → StandardScaler → Train/Val/Test Split → Models   │
        └─────────────────────────────────────────────────────┘
        ```
        """)
