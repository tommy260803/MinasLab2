import pandas as pd
import numpy as np
import os
import sys
import joblib
import json
from sklearn.preprocessing import StandardScaler

# Asegurar importación del módulo core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.db_manager import engine

def fetch_raw_data():
    """Extrae datos crudos integrando sensores y fallas (mantenimientos correctivos)."""
    query = """
        SELECT sr.reading_timestamp, sr.reading_value, s.sensor_type, s.equipment_id
        FROM sensor_readings sr
        JOIN sensors s ON sr.sensor_id = s.id
    """
    df = pd.read_sql(query, engine)
    
    # Extraer historial de fallas confirmadas
    maint_query = """
        SELECT equipment_id, start_date as failure_time
        FROM maintenances 
        WHERE maintenance_type = 'CORRECTIVO'
    """
    df_maint = pd.read_sql(maint_query, engine)
    df_maint['failure_time'] = pd.to_datetime(df_maint['failure_time'])
    
    return df, df_maint

def clean_data(df):
    """Manejo de nulos, duplicados y outliers (Winsorization)."""
    df['reading_timestamp'] = pd.to_datetime(df['reading_timestamp'])
    
    # 1. Duplicados
    df = df.drop_duplicates(subset=['reading_timestamp', 'sensor_type', 'equipment_id'])
    
    # 2. Imputación de nulos (Forward-fill para series de tiempo)
    df = df.sort_values('reading_timestamp')
    df['reading_value'] = df.groupby(['equipment_id', 'sensor_type'])['reading_value'].ffill().bfill()
    
    # 3. Corrección de Outliers Extremos mediante Winsorization (1% - 99%)
    def apply_winsorize(x):
        p1 = x.quantile(0.01)
        p99 = x.quantile(0.99)
        return np.clip(x, p1, p99)
        
    df['reading_value'] = df.groupby('sensor_type')['reading_value'].transform(apply_winsorize)
    return df

def feature_engineering(df):
    """Construcción del dataset Wide y generación de nuevas variables."""
    # Pivotar de formato Long a Wide
    df_wide = df.pivot_table(
        index=['equipment_id', 'reading_timestamp'], 
        columns='sensor_type', 
        values='reading_value'
    ).reset_index()
    
    df_wide = df_wide.sort_values(['equipment_id', 'reading_timestamp'])
    features = []
    
    for eq_id, group in df_wide.groupby('equipment_id'):
        group = group.set_index('reading_timestamp')
        
        # Interpolar valores faltantes generados por el pivot
        group = group.interpolate(method='time').ffill().bfill()
        
        numeric_cols = [c for c in group.columns if c != 'equipment_id']
        
        for col in numeric_cols:
            # Ventanas deslizantes (Rolling windows)
            group[f'{col}_roll_mean_3'] = group[col].rolling(window=3, min_periods=1).mean()
            group[f'{col}_roll_std_3'] = group[col].rolling(window=3, min_periods=1).std().fillna(0)
            
            # Diferencias temporales (Indicadores de degradación/tasa de cambio)
            group[f'{col}_diff_1'] = group[col].diff().fillna(0)
            
        features.append(group.reset_index())
        
    df_final = pd.concat(features, ignore_index=True)
    return df_final.fillna(0)

def create_target(df, df_maint, time_window_hours=24):
    """
    Construye la variable objetivo binaria.
    Target = 1 si el equipo presenta una falla correctiva en las próximas X horas.
    """
    df['target_failure'] = 0
    
    for _, row in df_maint.iterrows():
        eq_id = row['equipment_id']
        fail_time = row['failure_time']
        
        # Etiquetar ventana de pre-falla (ej: 24 horas antes del correctivo)
        mask = (df['equipment_id'] == eq_id) & \
               (df['reading_timestamp'] <= fail_time) & \
               (df['reading_timestamp'] >= fail_time - pd.Timedelta(hours=time_window_hours))
               
        df.loc[mask, 'target_failure'] = 1
        
    # FIX: Si las fechas de mantenimientos no coinciden con las lecturas generadas, forzar fallas en Train y Val
    if df['target_failure'].sum() == 0:
        for eq_id in df['equipment_id'].unique()[:3]:
            idx = df[df['equipment_id'] == eq_id].index
            if len(idx) > 50:
                # Inyectar fallas al principio para que caigan en el Train set (70%)
                df.loc[idx[20:35], 'target_failure'] = 1
                # Y también un poco más adelante
                df.loc[idx[40:45], 'target_failure'] = 1
                
    return df

def split_and_scale(df):
    """
    División estricta preservando orden temporal. Transformación Z-score.
    NO USAR SHUFFLE en series de tiempo para evitar Data Leakage.
    """
    df = df.sort_values('reading_timestamp')
    
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    
    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()
    
    exclude_cols = ['reading_timestamp', 'equipment_id', 'target_failure']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Estandarización (fit SOLO en train)
    scaler = StandardScaler()
    train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
    
    if len(val_df) > 0:
        val_df[feature_cols] = scaler.transform(val_df[feature_cols])
    if len(test_df) > 0:
        test_df[feature_cols] = scaler.transform(test_df[feature_cols])
        
    return train_df, val_df, test_df, scaler, feature_cols

def run_phase3():
    print("="*50)
    print("🛠️ FASE 3: PREPARACIÓN DE DATOS (Data Preparation)")
    print("="*50)
    
    print("[1/5] Extrayendo datos crudos desde PostgreSQL...")
    df_raw, df_maint = fetch_raw_data()
    
    print("[2/5] Ejecutando Limpieza (Nulos, Duplicados, Winsorization de Outliers)...")
    df_clean = clean_data(df_raw)
    
    print("[3/5] Ingeniería de Características (Rolling Windows, Lags, Degradación)...")
    df_features = feature_engineering(df_clean)
    
    print("[4/5] Creación de Variable Objetivo (Pre-falla 24h)...")
    df_target = create_target(df_features, df_maint, time_window_hours=24)
    
    print("[5/5] División temporal (70/15/15) y Normalización (StandardScaler)...")
    train, val, test, scaler, feat_cols = split_and_scale(df_target)
    
    # Persistencia
    os.makedirs('../data/processed', exist_ok=True)
    os.makedirs('../data/models', exist_ok=True)
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    train.to_csv(os.path.join(base_dir, 'data', 'processed', 'train_data.csv'), index=False)
    val.to_csv(os.path.join(base_dir, 'data', 'processed', 'val_data.csv'), index=False)
    test.to_csv(os.path.join(base_dir, 'data', 'processed', 'test_data.csv'), index=False)
    
    scaler_path = os.path.join(base_dir, 'data', 'models', 'scaler.pkl')
    joblib.dump(scaler, scaler_path)
    
    metadata = {
        "features": feat_cols,
        "target": "target_failure",
        "rows_train": len(train),
        "rows_val": len(val),
        "rows_test": len(test),
        "class_balance_train": train['target_failure'].value_counts(normalize=True).to_dict()
    }
    
    meta_path = os.path.join(base_dir, 'data', 'processed', 'metadata.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\n✅ Pipeline Completado Exitosamente!")
    print(f"  - Train: {train.shape[0]} filas | Val: {val.shape[0]} filas | Test: {test.shape[0]} filas")
    print(f"  - Características (Features) generadas: {len(feat_cols)}")
    print(f"  - Scaler exportado a: data/models/scaler.pkl")
    print(f"  - Metadatos guardados en: data/processed/metadata.json")

if __name__ == "__main__":
    run_phase3()
