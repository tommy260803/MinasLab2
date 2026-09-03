import pandas as pd
import numpy as np
import os
import joblib
import json
import warnings

# Suprimir advertencias menores de scikit-learn
warnings.filterwarnings('ignore')

from ml.algorithms.traditional.traditional_models import train_random_forest, train_xgboost, train_svm
from ml.algorithms.hybrid.hybrid_models import train_cnn_lstm, train_lstm_ae_rf

def run_phase4():
    print("="*60)
    print("🧠 FASE 4: MODELADO (Model Training - CRISP-DM)")
    print("="*60)
    
    # 1. Cargar Datos y Metadatos de la Fase 3
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, 'data', 'processed')
    models_dir = os.path.join(base_dir, 'data', 'models')
    
    print("[1/3] Cargando conjuntos de datos preparados...")
    
    try:
        train = pd.read_csv(os.path.join(data_dir, 'train_data.csv'))
        val = pd.read_csv(os.path.join(data_dir, 'val_data.csv'))
        
        with open(os.path.join(data_dir, 'metadata.json'), 'r') as f:
            meta = json.load(f)
    except FileNotFoundError:
        print("❌ Error: No se encontraron los datos preparados. Ejecute primero la Fase 3.")
        return
        
    features = meta['features']
    target = meta['target']
    
    X_train = train[features]
    y_train = train[target]
    
    X_val = val[features]
    y_val = val[target]
    
    print(f"  -> Features procesadas: {len(features)}")
    print(f"  -> Tamaño de Entrenamiento: {len(X_train)} filas (Fallas: {y_train.sum()})")
    print(f"  -> Tamaño de Validación: {len(X_val)} filas (Fallas: {y_val.sum()})")
    
    # =========================================================================
    # 2. ALGORITMOS TRADICIONALES
    # =========================================================================
    print("\n[2/3] Entrenando Modelos Tradicionales (Scikit-Learn / XGBoost)...")
    
    print("  ⏳ Entrenando [1/5] Random Forest...")
    rf_model = train_random_forest(X_train, y_train)
    joblib.dump(rf_model, os.path.join(models_dir, 'random_forest.pkl'))
    print("     ✅ Guardado como: random_forest.pkl")
    
    print("  ⏳ Entrenando [2/5] XGBoost (Con validación Early Stopping)...")
    xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
    joblib.dump(xgb_model, os.path.join(models_dir, 'xgboost.pkl'))
    print("     ✅ Guardado como: xgboost.pkl")
    
    print("  ⏳ Entrenando [3/5] Support Vector Machine (Kernel RBF)...")
    svm_model = train_svm(X_train, y_train)
    joblib.dump(svm_model, os.path.join(models_dir, 'svm.pkl'))
    print("     ✅ Guardado como: svm.pkl")
    
    # =========================================================================
    # 3. ALGORITMOS HÍBRIDOS (DEEP LEARNING)
    # =========================================================================
    print("\n[3/3] Entrenando Modelos Híbridos (Deep Learning Keras/TensorFlow)...")
    
    print("  ⏳ Entrenando [4/5] Red Neuronal CNN-LSTM...")
    cnn_lstm = train_cnn_lstm(X_train, y_train, X_val, y_val)
    cnn_lstm.save(os.path.join(models_dir, 'cnn_lstm.keras'))
    print("     ✅ Guardado como: cnn_lstm.keras")
    
    print("  ⏳ Entrenando [5/5] Ensamble Híbrido: LSTM-Autoencoder + Random Forest...")
    ae_encoder, ae_rf = train_lstm_ae_rf(X_train, y_train)
    ae_encoder.save(os.path.join(models_dir, 'lstm_ae_encoder.keras'))
    joblib.dump(ae_rf, os.path.join(models_dir, 'lstm_ae_rf.pkl'))
    print("     ✅ Guardado como: lstm_ae_encoder.keras y lstm_ae_rf.pkl")
    
    print("\n🚀 ¡Fase 4 Completada! Todos los modelos de Inteligencia Artificial han sido serializados y están listos para la Fase 5 (Evaluación).")

if __name__ == "__main__":
    run_phase4()
