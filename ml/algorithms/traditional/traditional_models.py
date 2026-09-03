import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import xgboost as xgb

def train_random_forest(X_train, y_train, random_state=42):
    """
    Algoritmo 1: Random Forest.
    Justificación Arquitectónica: Ensemble robusto basado en múltiples árboles de decisión. 
    Es excelente para datos tabulares y resiste muy bien el sobreajuste (overfitting).
    Se usa `class_weight='balanced'` para penalizar más los errores en la clase minoritaria (fallas).
    """
    model = RandomForestClassifier(
        n_estimators=150, 
        max_depth=12, 
        class_weight='balanced', 
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def train_xgboost(X_train, y_train, X_val, y_val, random_state=42):
    """
    Algoritmo 2: XGBoost (Extreme Gradient Boosting).
    Justificación Arquitectónica: Algoritmo SOTA para datos estructurados. 
    Aplica gradiente descendente integrado con regularización (L1/L2). 
    Se maneja el desbalanceo ajustando el parámetro `scale_pos_weight`.
    """
    # Cálculo dinámico del peso para la clase minoritaria
    pos_count = sum(y_train)
    neg_count = len(y_train) - pos_count
    scale_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    model = xgb.XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        scale_pos_weight=scale_weight,
        random_state=random_state,
        eval_metric='auc',
        early_stopping_rounds=20,
        n_jobs=-1
    )
    # Se utiliza Early Stopping evaluando contra el set de validación
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model

def train_svm(X_train, y_train, random_state=42):
    """
    Algoritmo 3: Support Vector Machine (Kernel RBF).
    Justificación Arquitectónica: Proyecta los datos a un plano multidimensional 
    para encontrar un hiperplano de separación óptimo para relaciones no lineales complejas.
    Se requiere `probability=True` para su integración en el Dashboard de Riesgos.
    """
    model = SVC(
        kernel='rbf',
        C=1.0,
        gamma='scale',
        class_weight='balanced',
        probability=True,
        random_state=random_state
    )
    model.fit(X_train, y_train)
    return model
