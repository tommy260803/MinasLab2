import os
import time
import json
import joblib
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, roc_auc_score, average_precision_score,
                             confusion_matrix, roc_curve, precision_recall_curve)
from sklearn.model_selection import KFold, StratifiedKFold, TimeSeriesSplit, GridSearchCV

import warnings
warnings.filterwarnings('ignore')

def run_evaluation_pipeline():
    print("="*60)
    print("🔬 FASE 5: EVALUACIÓN Y SELECCIÓN RIGUROSA DE MODELOS")
    print("="*60)

    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, 'data', 'processed')
    models_dir = os.path.join(base_dir, 'data', 'models')
    
    # 1. Carga de Datos
    print("[1/5] Cargando datos (Train/Test) y Modelos...")
    try:
        X_train = pd.read_csv(os.path.join(data_dir, 'train_data.csv'))
        X_test = pd.read_csv(os.path.join(data_dir, 'test_data.csv'))
        with open(os.path.join(data_dir, 'metadata.json'), 'r') as f:
            meta = json.load(f)
        target = meta['target']
        y_train = X_train.pop(target)
        y_test = X_test.pop(target)
        
        # Eliminar columnas no predictivas para CV
        drop_cols = ['reading_timestamp', 'equipment_id', 'time_to_failure']
        for c in drop_cols:
            if c in X_train.columns: X_train.pop(c)
            if c in X_test.columns: X_test.pop(c)
        
        # Imputar NaN con mediana (necesario para SVM)
        imputer = SimpleImputer(strategy='median')
        X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=X_train.columns, index=X_train.index)
        X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=X_test.columns, index=X_test.index)
        X_train = X_train_imputed
        X_test = X_test_imputed
            
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return

    # Carga de modelos tradicionales
    try:
        rf_model = joblib.load(os.path.join(models_dir, 'random_forest.pkl'))
        xgb_model = joblib.load(os.path.join(models_dir, 'xgboost.pkl'))
        svm_model = joblib.load(os.path.join(models_dir, 'svm.pkl'))
    except Exception as e:
        print(f"Error cargando modelos tradicionales: {e}")
        return

    models = {
        'Random Forest': rf_model,
        'XGBoost': xgb_model,
        'SVM (RBF)': svm_model
    }

    results = {'metrics': {}, 'curves': {}, 'cv': {}, 'stats': {}, 'tuning': {}, 'robustness': {}}

    # 2. Evaluación Base en Test
    print("[2/5] Calculando Métricas Base y Curvas ROC/PR en conjunto de Test...")
    for name, model in models.items():
        start_time = time.time()
        preds = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        inference_time = time.time() - start_time
        
        results['metrics'][name] = {
            'Accuracy': accuracy_score(y_test, preds),
            'Precision': precision_score(y_test, preds, zero_division=0),
            'Recall': recall_score(y_test, preds, zero_division=0),
            'F1-Score': f1_score(y_test, preds, zero_division=0),
            'AUC-ROC': roc_auc_score(y_test, proba),
            'AUC-PR': average_precision_score(y_test, proba),
            'Inference Time (s)': inference_time,
            'Confusion Matrix': confusion_matrix(y_test, preds).tolist()
        }
        
        fpr, tpr, _ = roc_curve(y_test, proba)
        prec, rec, _ = precision_recall_curve(y_test, proba)
        results['curves'][name] = {
            'fpr': fpr.tolist(), 'tpr': tpr.tolist(),
            'prec': prec.tolist(), 'rec': rec.tolist()
        }

    # 3. Validación Cruzada (3 Estrategias)
    print("[3/5] Ejecutando Validación Cruzada Múltiple (KFold, Stratified, TimeSeries)...")
    cv_strategies = {
        'K-Fold': KFold(n_splits=5, shuffle=True, random_state=42),
        'Stratified K-Fold': StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        'Time Series Split': TimeSeriesSplit(n_splits=5) # Obligatorio para series de tiempo
    }
    
    # Crear copias de modelos para CV (sin early_stopping para XGBoost)
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    import xgboost as xgb
    
    cv_models = {
        'Random Forest': RandomForestClassifier(n_estimators=150, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1),
        'XGBoost': xgb.XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42, eval_metric='auc', n_jobs=-1),
        'SVM (RBF)': SVC(kernel='rbf', C=1.0, gamma='scale', class_weight='balanced', probability=True, random_state=42)
    }
    
    for name, model in cv_models.items():
        results['cv'][name] = {}
        for cv_name, cv_splitter in cv_strategies.items():
            from sklearn.model_selection import cross_val_score
            try:
                scores = cross_val_score(model, X_train, y_train, cv=cv_splitter, scoring='f1', n_jobs=-1, error_score='raise')
            except Exception:
                scores = cross_val_score(model, X_train, y_train, cv=cv_splitter, scoring='f1', n_jobs=-1, error_score=np.nan)
            results['cv'][name][cv_name] = {'mean': float(np.nanmean(scores)), 'std': float(np.nanstd(scores)), 'folds': [float(x) for x in scores.tolist()]}

    # 4. Pruebas Estadísticas y Estabilidad
    print("[4/5] Realizando Pruebas Estadísticas y de Robustez (McNemar, T-Test, Bootstrap, Ruido)...")
    
    # McNemar (RF vs XGBoost)
    rf_preds = models['Random Forest'].predict(X_test)
    xgb_preds = models['XGBoost'].predict(X_test)
    
    c00 = sum((rf_preds == y_test) & (xgb_preds == y_test))
    c01 = sum((rf_preds == y_test) & (xgb_preds != y_test))
    c10 = sum((rf_preds != y_test) & (xgb_preds == y_test))
    c11 = sum((rf_preds != y_test) & (xgb_preds != y_test))
    contingency = [[c00, c01], [c10, c11]]
    mcnemar_res = mcnemar(contingency, exact=False, correction=True)
    results['stats']['McNemar_RF_vs_XGB'] = {'pvalue': mcnemar_res.pvalue, 'statistic': mcnemar_res.statistic}

    # T-Test Pareado en TimeSeries CV (RF vs XGB)
    rf_cv_folds = results['cv']['Random Forest']['Time Series Split']['folds']
    xgb_cv_folds = results['cv']['XGBoost']['Time Series Split']['folds']
    t_stat, p_val = stats.ttest_rel(rf_cv_folds, xgb_cv_folds)
    results['stats']['TTest_RF_vs_XGB'] = {'pvalue': float(p_val), 'statistic': float(t_stat)}

    # Estabilidad Bootstrap (100 iteraciones)
    for name, model in models.items():
        boot_f1 = []
        np.random.seed(42)
        n_size = len(y_test)
        for _ in range(100):
            idx = np.random.choice(len(X_test), size=n_size, replace=True)
            X_sample = X_test.iloc[idx]
            y_sample = y_test.iloc[idx]
            boot_preds = model.predict(X_sample)
            boot_f1.append(f1_score(y_sample, boot_preds, zero_division=0))
        results['stats'][f'Bootstrap_F1_{name}'] = np.percentile(boot_f1, [2.5, 97.5]).tolist()

    # Análisis de Sensibilidad al Ruido (Degradación)
    noise_levels = [0.1, 0.2, 0.3, 0.5]
    for name, model in models.items():
        results['robustness'][name] = {}
        for noise in noise_levels:
            np.random.seed(42)
            X_noisy = X_test + np.random.normal(0, noise, X_test.shape)
            noisy_preds = model.predict(X_noisy)
            results['robustness'][name][str(noise)] = f1_score(y_test, noisy_preds, zero_division=0)

    # 5. Optimización de Hiperparámetros (Simulada para mantener tiempo de ejecución)
    print("[5/5] Ejecutando Optimización de Hiperparámetros (Grid Search en RF)...")
    # Para no demorar la prueba, hacemos un grid pequeño
    param_grid = {'n_estimators': [100, 200], 'max_depth': [10, 15]}
    grid_search = GridSearchCV(RandomForestClassifier(class_weight='balanced', random_state=42), param_grid, cv=3, scoring='f1', n_jobs=-1)
    grid_search.fit(X_train[:1000], y_train[:1000]) # Subsample por rapidez
    
    results['tuning']['Random Forest'] = {
        'best_params': grid_search.best_params_,
        'best_cv_score': grid_search.best_score_
    }

    # Guardar resultados
    eval_file = os.path.join(data_dir, 'evaluation_results.pkl')
    joblib.dump(results, eval_file)
    print(f"\n✅ Evaluación Completada con Éxito. Resultados guardados en: {eval_file}")

if __name__ == "__main__":
    run_evaluation_pipeline()
