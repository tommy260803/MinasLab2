import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Conv1D, MaxPooling1D, Input, RepeatVector, TimeDistributed, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.ensemble import RandomForestClassifier
import os

# Suprimir advertencias de TF para consola limpia
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

def train_cnn_lstm(X_train, y_train, X_val, y_val):
    """
    Algoritmo 4: Híbrido CNN-LSTM.
    Justificación Arquitectónica: La capa Convolucional 1D extrae características locales (patrones 
    o picos inmediatos en las variables), y pasa este mapa de características a la capa LSTM para 
    capturar las dependencias a largo plazo y la degradación temporal antes de una falla.
    """
    # Reshape obligatorio para entrada de red neuronal (samples, features, channels)
    X_train_reshaped = X_train.values.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_val_reshaped = X_val.values.reshape((X_val.shape[0], X_val.shape[1], 1))
    
    # Manejo algorítmico del desbalanceo
    neg, pos = np.bincount(y_train)
    total = neg + pos
    weight_0 = (1 / neg) * (total / 2.0)
    weight_1 = (1 / pos) * (total / 2.0) if pos > 0 else 1.0
    class_weight = {0: weight_0, 1: weight_1}
    
    model = Sequential([
        # Bloque Convolucional
        Conv1D(filters=64, kernel_size=3, activation='relu', padding='same', input_shape=(X_train.shape[1], 1)),
        MaxPooling1D(pool_size=2, padding='same'),
        
        # Bloque Recurrente (LSTM)
        LSTM(64, return_sequences=False),
        Dropout(0.3), # Regularización
        
        # Bloque de Clasificación Densa
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=[tf.keras.metrics.AUC(name='auc')])
    
    # Prevención de Overfitting mediante Checkpoints / Early Stopping
    early_stop = EarlyStopping(monitor='val_auc', mode='max', patience=10, restore_best_weights=True)
    
    model.fit(
        X_train_reshaped, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_val_reshaped, y_val),
        class_weight=class_weight,
        callbacks=[early_stop],
        verbose=0 # Silencioso
    )
    return model

def train_lstm_ae_rf(X_train, y_train, random_state=42):
    """
    Algoritmo 5: Híbrido en Dos Etapas (LSTM-Autoencoder + Random Forest).
    Justificación Arquitectónica: Usa un Autoencoder (red no supervisada) para hacer 
    reducción de dimensionalidad no lineal. El encoder extrae una "representación latente" 
    robusta del estado del equipo. Esta representación se pasa luego a un Random Forest 
    para la clasificación supervisada final.
    """
    X_train_reshaped = X_train.values.reshape((X_train.shape[0], X_train.shape[1], 1))
    
    inputs = Input(shape=(X_train.shape[1], 1))
    
    # Parte 1: ENCODER (Comprime la información)
    encoded = LSTM(32, activation='relu', return_sequences=False)(inputs)
    
    # Parte 2: DECODER (Intenta reconstruir la señal)
    decoded = RepeatVector(X_train.shape[1])(encoded)
    decoded = LSTM(32, activation='relu', return_sequences=True)(decoded)
    decoded = TimeDistributed(Dense(1))(decoded)
    
    autoencoder = Model(inputs, decoded)
    encoder = Model(inputs, encoded) # Modelo recortado que solo extrae características latentes
    
    autoencoder.compile(optimizer='adam', loss='mse')
    
    early_stop_ae = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
    
    # Entrenar Autoencoder para reconstrucción
    autoencoder.fit(X_train_reshaped, X_train_reshaped, epochs=30, batch_size=32, callbacks=[early_stop_ae], verbose=0)
    
    # Extraer el espacio latente (Dimensionality Reduction)
    X_train_latent = encoder.predict(X_train_reshaped, verbose=0)
    
    # Parte 3: Entrenar el clasificador Random Forest sobre el espacio latente
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=random_state)
    rf.fit(X_train_latent, y_train)
    
    # Retornamos ambos para que en predicción podamos hacer: RF.predict(Encoder.predict(X))
    return encoder, rf
