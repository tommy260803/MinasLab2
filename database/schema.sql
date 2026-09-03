-- database/schema.sql
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
