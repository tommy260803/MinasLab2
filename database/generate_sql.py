import os
import random
from datetime import datetime, timedelta

schema_sql = """-- database/schema.sql
-- Diseño de la Base de Datos para el Sistema de Mantenimiento Predictivo

DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS maintenances CASCADE;
DROP TABLE IF EXISTS ai_predictions CASCADE;
DROP TABLE IF EXISTS sensor_readings CASCADE;
DROP TABLE IF EXISTS sensors CASCADE;
DROP TABLE IF EXISTS equipments CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- 1. Tabla de Roles
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE roles IS 'Roles del sistema (RBAC)';

-- 2. Tabla de Permisos
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE permissions IS 'Permisos granulares del sistema';

-- 3. Tabla Intermedia Rol-Permiso (N:M)
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
COMMENT ON TABLE role_permissions IS 'Matriz de asignación de permisos a roles';

-- 4. Tabla de Usuarios
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE users IS 'Usuarios del sistema. Las contraseñas se almacenan con bcrypt.';
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- 5. Bitácora de Accesos (Audit Logs)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE audit_logs IS 'Bitácora de seguridad y acciones de los usuarios';
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- 6. Equipos Mineros
CREATE TABLE equipments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('OPERATIVO', 'EN_MANTENIMIENTO', 'FUERA_DE_SERVICIO')),
    purchase_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE equipments IS 'Registro de equipos de carguío (ej. palas, camiones)';
CREATE INDEX idx_equipments_status ON equipments(status);

-- 7. Sensores
CREATE TABLE sensors (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER NOT NULL REFERENCES equipments(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    sensor_type VARCHAR(50) NOT NULL CHECK (sensor_type IN ('TEMPERATURA', 'PRESION', 'VIBRACION', 'RPM', 'NIVEL_ACEITE')),
    unit VARCHAR(20) NOT NULL,
    min_threshold NUMERIC,
    max_threshold NUMERIC,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE sensors IS 'Sensores instalados en los equipos';
CREATE INDEX idx_sensors_equipment_id ON sensors(equipment_id);

-- 8. Lecturas de Sensores
CREATE TABLE sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    reading_value NUMERIC NOT NULL,
    reading_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE sensor_readings IS 'Datos recolectados de los sensores (Time Series)';
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(reading_timestamp DESC);

-- 9. Predicciones de IA
CREATE TABLE ai_predictions (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER NOT NULL REFERENCES equipments(id) ON DELETE CASCADE,
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    failure_probability NUMERIC NOT NULL CHECK (failure_probability >= 0 AND failure_probability <= 1),
    predicted_failure_type VARCHAR(100),
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ai_predictions IS 'Resultados del motor de IA (CRISP-DM)';
CREATE INDEX idx_ai_predictions_equipment_id ON ai_predictions(equipment_id);
CREATE INDEX idx_ai_predictions_date ON ai_predictions(prediction_date DESC);

-- 10. Mantenimientos
CREATE TABLE maintenances (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER NOT NULL REFERENCES equipments(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    maintenance_type VARCHAR(50) NOT NULL CHECK (maintenance_type IN ('PREVENTIVO', 'CORRECTIVO', 'PREDICTIVO')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PROGRAMADO', 'EN_PROGRESO', 'COMPLETADO', 'CANCELADO')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE maintenances IS 'Historial de órdenes de mantenimiento';
CREATE INDEX idx_maintenances_equipment_id ON maintenances(equipment_id);
CREATE INDEX idx_maintenances_status ON maintenances(status);
"""

# Bcrypt válido generado con coste 12 para 'password123'
hash_pw = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2IK/3JGEA6"

seed_sql = f"""-- database/seed_data.sql
-- Inserción de datos de prueba (Seed Data)

-- 1. Roles
INSERT INTO roles (id, name, description) VALUES
(1, 'Administrador', 'Control total del sistema'),
(2, 'Ingeniero Confiabilidad', 'Gestiona modelos y análisis'),
(3, 'Operador', 'Visualiza tableros y alertas'),
(4, 'Analista de Datos', 'Explora datos y métricas');

-- 2. Permisos
INSERT INTO permissions (id, name, description) VALUES
(1, 'view_dashboard', 'Ver tableros principales'),
(2, 'manage_users', 'Gestionar usuarios'),
(3, 'run_models', 'Ejecutar modelos IA'),
(4, 'manage_equipment', 'Gestionar equipos mineros'),
(5, 'manage_maintenance', 'Gestionar órdenes de mantenimiento');

-- 3. Rol-Permiso (N:M)
INSERT INTO role_permissions (role_id, permission_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
(2, 1), (2, 3), (2, 4), (2, 5),
(3, 1),
(4, 1), (4, 3);

-- 4. Usuarios (Contraseña: password123)
INSERT INTO users (id, role_id, username, email, password_hash) VALUES
(1, 1, 'admin_juan', 'juan.admin@mina.com', '{hash_pw}'),
(2, 2, 'ing_maria', 'maria.ing@mina.com', '{hash_pw}'),
(3, 3, 'ope_carlos', 'carlos.ope@mina.com', '{hash_pw}'),
(4, 4, 'ana_lucia', 'lucia.ana@mina.com', '{hash_pw}');

-- 5. Bitácora de Accesos
INSERT INTO audit_logs (user_id, action, ip_address) VALUES
(1, 'LOGIN_SUCCESS', '192.168.1.10'),
(2, 'LOGIN_SUCCESS', '192.168.1.12'),
(3, 'LOGIN_SUCCESS', '192.168.1.15'),
(4, 'LOGIN_SUCCESS', '192.168.1.18'),
(1, 'CREATE_USER', '192.168.1.10');

-- 6. Equipos Mineros
INSERT INTO equipments (id, code, name, equipment_type, status, purchase_date) VALUES
(1, 'CA-001', 'Camión Autónomo 01', 'CAMION_EXTRACCION', 'OPERATIVO', '2020-01-15'),
(2, 'CA-002', 'Camión Autónomo 02', 'CAMION_EXTRACCION', 'OPERATIVO', '2020-01-15'),
(3, 'CA-003', 'Camión Autónomo 03', 'CAMION_EXTRACCION', 'EN_MANTENIMIENTO', '2021-03-10'),
(4, 'PH-101', 'Pala Hidráulica 101', 'PALA_HIDRAULICA', 'OPERATIVO', '2019-11-20'),
(5, 'PH-102', 'Pala Hidráulica 102', 'PALA_HIDRAULICA', 'OPERATIVO', '2021-05-05'),
(6, 'PE-201', 'Perforadora 201', 'PERFORADORA', 'FUERA_DE_SERVICIO', '2018-08-12');

-- 7. Sensores
INSERT INTO sensors (id, equipment_id, code, sensor_type, unit, min_threshold, max_threshold) VALUES
(1, 1, 'SENS-TEMP-01', 'TEMPERATURA', '°C', -10, 110),
(2, 1, 'SENS-PRES-01', 'PRESION', 'PSI', 30, 150),
(3, 2, 'SENS-TEMP-02', 'TEMPERATURA', '°C', -10, 110),
(4, 2, 'SENS-VIB-01', 'VIBRACION', 'mm/s', 0, 15),
(5, 3, 'SENS-RPM-01', 'RPM', 'RPM', 0, 2500),
(6, 4, 'SENS-TEMP-03', 'TEMPERATURA', '°C', -10, 120),
(7, 4, 'SENS-ACEITE-01', 'NIVEL_ACEITE', '%', 20, 100),
(8, 5, 'SENS-PRES-02', 'PRESION', 'PSI', 30, 150),
(9, 5, 'SENS-VIB-02', 'VIBRACION', 'mm/s', 0, 20),
(10, 6, 'SENS-TEMP-04', 'TEMPERATURA', '°C', -10, 110),
(11, 6, 'SENS-RPM-02', 'RPM', 'RPM', 0, 3000);

-- 9. Predicciones IA
INSERT INTO ai_predictions (equipment_id, failure_probability, predicted_failure_type, details) VALUES
(1, 0.12, 'NINGUNA', 'Equipo operando en rangos normales'),
(3, 0.85, 'FALLA_MOTOR', 'Alta probabilidad de falla debido a exceso de temperatura e irregularidad en RPM'),
(6, 0.95, 'FALLA_HIDRAULICA', 'Presión crítica detectada previamente, el equipo requiere atención urgente'),
(2, 0.05, 'NINGUNA', 'Parámetros óptimos'),
(4, 0.40, 'DESGASTE_RODAMIENTOS', 'Vibración incrementando gradualmente en últimos 7 días');

-- 10. Mantenimientos
INSERT INTO maintenances (id, equipment_id, user_id, maintenance_type, start_date, end_date, status, notes) VALUES
(1, 1, 2, 'PREVENTIVO', '2023-01-10 08:00:00', '2023-01-10 18:00:00', 'COMPLETADO', 'Cambio de aceite y filtros de rutina'),
(2, 2, 2, 'PREVENTIVO', '2023-02-15 08:00:00', '2023-02-15 16:00:00', 'COMPLETADO', 'Revisión de frenos y suspensión'),
(3, 3, 2, 'PREDICTIVO', '2023-10-25 09:00:00', NULL, 'EN_PROGRESO', 'Alerta IA: Intervención para revisar motor por alta temperatura'),
(4, 4, 2, 'PREVENTIVO', '2023-05-20 07:00:00', '2023-05-21 12:00:00', 'COMPLETADO', 'Mantenimiento semestral general'),
(5, 5, 2, 'CORRECTIVO', '2023-08-14 10:00:00', '2023-08-16 15:00:00', 'COMPLETADO', 'Reemplazo de manguera hidráulica rota'),
(6, 6, 2, 'CORRECTIVO', '2023-10-20 08:00:00', NULL, 'PROGRAMADO', 'Reemplazo de motor principal por falla catastrófica'),
(7, 1, 2, 'PREVENTIVO', '2023-06-10 08:00:00', '2023-06-10 18:00:00', 'COMPLETADO', 'Cambio de aceite de mitad de año'),
(8, 2, 2, 'PREDICTIVO', '2023-07-05 09:00:00', '2023-07-06 14:00:00', 'COMPLETADO', 'Reemplazo de rodamiento preventivo sugerido por vibración');

-- Generando 500+ lecturas de sensores
"""

def get_base_val(stype):
    if stype == 'TEMPERATURA': return 85.0, 5.0
    if stype == 'PRESION': return 100.0, 10.0
    if stype == 'VIBRACION': return 5.0, 1.5
    if stype == 'RPM': return 1800.0, 100.0
    if stype == 'NIVEL_ACEITE': return 80.0, 2.0
    return 50.0, 5.0

sensors_info = {
    1: 'TEMPERATURA', 2: 'PRESION', 3: 'TEMPERATURA', 4: 'VIBRACION',
    5: 'RPM', 6: 'TEMPERATURA', 7: 'NIVEL_ACEITE', 8: 'PRESION',
    9: 'VIBRACION', 10: 'TEMPERATURA', 11: 'RPM'
}

start_time = datetime(2023, 10, 26, 8, 0, 0)
values_sql = []
random.seed(42)

for i in range(550):
    sensor_id = random.randint(1, 11)
    stype = sensors_info[sensor_id]
    mean, std = get_base_val(stype)
    
    val = random.gauss(mean, std)
    
    # Anomalias 
    if sensor_id == 5 and i > 400: val = random.gauss(2400.0, 200.0)
    if sensor_id == 10 and i > 300: val = random.gauss(115.0, 10.0)
    
    ts = start_time + timedelta(minutes=i * 15)
    values_sql.append(f"({sensor_id}, {round(val, 2)}, '{ts.strftime('%Y-%m-%d %H:%M:%S')}')")

batch_size = 100
for idx in range(0, len(values_sql), batch_size):
    batch = values_sql[idx:idx+batch_size]
    seed_sql += "\\nINSERT INTO sensor_readings (sensor_id, reading_value, reading_timestamp) VALUES\\n" + ",\\n".join(batch) + ";\\n"

seed_sql += """
-- Ajuste de secuencias
SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));
SELECT setval('permissions_id_seq', (SELECT MAX(id) FROM permissions));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('equipments_id_seq', (SELECT MAX(id) FROM equipments));
SELECT setval('sensors_id_seq', (SELECT MAX(id) FROM sensors));
SELECT setval('maintenances_id_seq', (SELECT MAX(id) FROM maintenances));
"""

with open(r'c:\Users\Anthony Garcia\LABORATORIO2_SOFTWARE\database\schema.sql', 'w', encoding='utf-8') as f:
    f.write(schema_sql)

with open(r'c:\Users\Anthony Garcia\LABORATORIO2_SOFTWARE\database\seed_data.sql', 'w', encoding='utf-8') as f:
    f.write(seed_sql)

print("Archivos SQL generados exitosamente.")
