import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
from core.audit_logger import log_action
from core.permissions import require_permission

def load_evaluation_results():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(base_dir, 'data', 'processed', 'evaluation_results.pkl')
    if os.path.exists(file_path):
        return joblib.load(file_path)
    return None

def render_evaluation():
    user = st.session_state["user"]
    require_permission("run_models") # Requiere permiso de Data Scientist/Analista
    
    if not st.session_state.get("eval_loaded_log"):
        log_action(user["id"], "VIEW_EVALUATION", details="Acceso a la Fase 5: Selección de Modelos (MCDA)")
        st.session_state["eval_loaded_log"] = True

    st.title("🏆 Fase 5: Evaluación y Selección del Mejor Modelo")
    
    results = load_evaluation_results()
    if not results:
        st.error("⚠️ No se encontraron los resultados de evaluación. Debes ejecutar `python ml/phase5_evaluation.py` primero.")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Métricas y Curvas", 
        "🧮 Matrices de Confusión", 
        "🔄 Validación Cruzada", 
        "🔬 Pruebas Estadísticas", 
        "⚖️ Selección Multicriterio (MCDA)"
    ])
    
    # --- TAB 1: Métricas Base ---
    with tab1:
        st.subheader("Rendimiento en Conjunto de Prueba (Test Set)")
        metrics_df = pd.DataFrame(results['metrics']).T
        st.dataframe(metrics_df.style.highlight_max(axis=0, subset=['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC-ROC', 'AUC-PR'], color='lightgreen')
                                     .highlight_min(axis=0, subset=['Inference Time (s)'], color='lightgreen'), 
                     use_container_width=True)
                     
        col1, col2 = st.columns(2)
        with col1:
            # Curvas ROC
            fig_roc = go.Figure()
            for name, curves in results['curves'].items():
                fig_roc.add_trace(go.Scatter(x=curves['fpr'], y=curves['tpr'], mode='lines', name=f"{name} (AUC={results['metrics'][name]['AUC-ROC']:.3f})"))
            fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', line=dict(dash='dash', color='gray'), showlegend=False))
            fig_roc.update_layout(title="Curva ROC (Receiver Operating Characteristic)", xaxis_title="False Positive Rate", yaxis_title="True Positive Rate")
            st.plotly_chart(fig_roc, use_container_width=True)
            
        with col2:
            # Curvas PR
            fig_pr = go.Figure()
            for name, curves in results['curves'].items():
                fig_pr.add_trace(go.Scatter(x=curves['rec'], y=curves['prec'], mode='lines', name=f"{name} (AUC-PR={results['metrics'][name]['AUC-PR']:.3f})"))
            fig_pr.update_layout(title="Curva Precision-Recall", xaxis_title="Recall (Sensibilidad)", yaxis_title="Precision")
            st.plotly_chart(fig_pr, use_container_width=True)

    # --- TAB 2: Matrices de Confusión ---
    with tab2:
        st.subheader("Matrices de Confusión (Absolutas y Normalizadas)")
        cols = st.columns(len(results['metrics']))
        for i, (name, data) in enumerate(results['metrics'].items()):
            cm = np.array(data['Confusion Matrix'])
            with cols[i]:
                fig_cm = px.imshow(cm, text_auto=True, color_continuous_scale='Blues', 
                                   title=f"{name}", labels=dict(x="Predicción", y="Realidad"))
                fig_cm.update_xaxes(side="bottom")
                st.plotly_chart(fig_cm, use_container_width=True)

    # --- TAB 3: Cross Validation ---
    with tab3:
        st.subheader("Validación Cruzada (Múltiples Estrategias)")
        st.info("💡 **Time Series Split** es la estrategia más rigurosa para este proyecto ya que respeta el flujo cronológico de los datos IoT, evitando fuga de información futura.")
        
        cv_data = []
        for model_name, strats in results['cv'].items():
            for strat_name, scores in strats.items():
                cv_data.append({'Modelo': model_name, 'Estrategia': strat_name, 'F1 Mean': scores['mean'], 'F1 Std': scores['std']})
        
        cv_df = pd.DataFrame(cv_data)
        fig_cv = px.bar(cv_df, x='Modelo', y='F1 Mean', color='Estrategia', barmode='group',
                        error_y='F1 Std', title="Comparativa de F1-Score por Estrategia de Validación")
        st.plotly_chart(fig_cv, use_container_width=True)

    # --- TAB 4: Pruebas Estadísticas ---
    with tab4:
        st.subheader("Análisis Estadístico de Robustez")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📉 Prueba de McNemar (Predicciones Individuales)")
            pval_mc = results['stats']['McNemar_RF_vs_XGB']['pvalue']
            st.metric("P-Value (RF vs XGBoost)", f"{pval_mc:.4e}")
            if pval_mc < 0.05:
                st.success("H0 Rechazada: Hay diferencia estadísticamente significativa en cómo se equivocan los modelos.")
            else:
                st.warning("H0 Aceptada: Los modelos cometen errores en proporciones similares.")
                
            st.markdown("#### 📈 Prueba T Pareada (Folds de Validación)")
            pval_t = results['stats']['TTest_RF_vs_XGB']['pvalue']
            st.metric("P-Value T-Test (Time Series Folds)", f"{pval_t:.4e}")
            if pval_t < 0.05:
                st.success("H0 Rechazada: Un modelo es estadísticamente superior al otro de forma consistente.")
            else:
                st.warning("H0 Aceptada: No hay diferencia significativa en el rendimiento promedio.")

        with c2:
            st.markdown("#### 🎲 Estabilidad Bootstrap (95% CI de F1-Score)")
            boot_data = []
            for name in results['metrics'].keys():
                ci = results['stats'].get(f'Bootstrap_F1_{name}', [0, 0])
                boot_data.append({'Modelo': name, 'Límite Inferior': ci[0], 'Límite Superior': ci[1]})
            st.table(pd.DataFrame(boot_data).set_index('Modelo'))
            
            st.markdown("#### ⚙️ Optimización GridSearch")
            for model_name, tuning in results.get('tuning', {}).items():
                st.info(f"**{model_name} Best Params:** {tuning['best_params']} \n\n(CV Score: {tuning['best_cv_score']:.4f})")
                
        st.markdown("#### 🔊 Sensibilidad al Ruido (Degradación Gaussiana)")
        noise_df = pd.DataFrame(results['robustness']).reset_index().melt(id_vars='index', var_name='Modelo', value_name='F1-Score')
        noise_df.rename(columns={'index': 'Nivel de Ruido (Desviación)'}, inplace=True)
        fig_noise = px.line(noise_df, x='Nivel de Ruido (Desviación)', y='F1-Score', color='Modelo', markers=True,
                            title="Caída de rendimiento ante ruido simulado en sensores")
        st.plotly_chart(fig_noise, use_container_width=True)

    # --- TAB 5: Selección Multicriterio (MCDA) ---
    with tab5:
        st.subheader("⚖️ Selección Ponderada del Modelo Ganador (MCDA)")
        st.markdown("Ajusta los pesos de negocio. La suma debe dar 100%. Los modelos se normalizarán (Min-Max) para calcular un Score Final.")
        
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            w_recall = st.number_input("Peso: Recall (Detectar Fallas)", min_value=0.0, max_value=1.0, value=0.35, step=0.05)
            w_f1 = st.number_input("Peso: F1-Score (Balance)", min_value=0.0, max_value=1.0, value=0.20, step=0.05)
        with col_w2:
            w_auc = st.number_input("Peso: AUC-ROC", min_value=0.0, max_value=1.0, value=0.20, step=0.05)
            w_acc = st.number_input("Peso: Accuracy Global", min_value=0.0, max_value=1.0, value=0.10, step=0.05)
        with col_w3:
            w_inf = st.number_input("Peso: Tiempo Inferencia (Velocidad)", min_value=0.0, max_value=1.0, value=0.10, step=0.05)
            w_rob = st.number_input("Peso: Robustez (Ruido Máximo)", min_value=0.0, max_value=1.0, value=0.05, step=0.05)
            
        total_weight = w_recall + w_f1 + w_auc + w_acc + w_inf + w_rob
        
        if abs(total_weight - 1.0) > 0.001:
            st.error(f"La suma de los pesos es {total_weight:.2f}. Debe ser exactamente 1.0 (100%). Ajuste los valores.")
        else:
            # Calcular ranking
            mcda_data = []
            for name in results['metrics'].keys():
                mcda_data.append({
                    'Modelo': name,
                    'Recall': results['metrics'][name]['Recall'],
                    'F1': results['metrics'][name]['F1-Score'],
                    'AUC': results['metrics'][name]['AUC-ROC'],
                    'Accuracy': results['metrics'][name]['Accuracy'],
                    'Inference_Time': results['metrics'][name]['Inference Time (s)'],
                    'Robustness': results['robustness'][name].get('0.5', 0) # F1 score con ruido alto
                })
            df_m = pd.DataFrame(mcda_data).set_index('Modelo')
            
            # Normalización Min-Max
            df_norm = (df_m - df_m.min()) / (df_m.max() - df_m.min() + 1e-9)
            # Invertir métricas de costo (Tiempo de inferencia)
            df_norm['Inference_Time'] = 1 - df_norm['Inference_Time']
            
            # Calcular score
            final_scores = (
                df_norm['Recall'] * w_recall +
                df_norm['F1'] * w_f1 +
                df_norm['AUC'] * w_auc +
                df_norm['Accuracy'] * w_acc +
                df_norm['Inference_Time'] * w_inf +
                df_norm['Robustness'] * w_rob
            ) * 100
            
            df_final = pd.DataFrame({'Score Global (%)': final_scores}).sort_values('Score Global (%)', ascending=False)
            
            st.markdown("### 🏆 Ranking Final")
            st.dataframe(df_final.style.background_gradient(cmap='viridis'), use_container_width=True)
            
            winner = df_final.index[0]
            st.success(f"🎉 **Modelo Ganador Recomendado para Producción:** {winner}")
            
            # Botón de confirmación (Simulación)
            if st.button("Promover Modelo a Producción (Fase 6)"):
                log_action(user["id"], "MODEL_PROMOTED", details=f"Modelo {winner} seleccionado para producción con score {df_final.iloc[0]['Score Global (%)']:.1f}")
                st.balloons()
                st.success(f"El modelo {winner} ha sido etiquetado en la base de datos como ACTIVO. ¡Listo para la Fase 6 de Deployment!")
