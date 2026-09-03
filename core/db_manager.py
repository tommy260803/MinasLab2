import os
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

def get_db_url():
    # Intenta obtener configuración por variables de entorno primero
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    name = os.getenv('DB_NAME')
    
    # Si no están, intentamos leer de config.yaml si existe
    if not host:
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'database' in config:
                    host = config['database'].get('host', 'localhost')
                    port = config['database'].get('port', 5432)
                    user = config['database'].get('user', 'postgres')
                    password = config['database'].get('password', 'secret_password')
                    name = config['database'].get('name', 'predictive_maintenance_db')
                    
                    # Fix: Limpiar literales ${VAR} de YAML si no fueron sustituidos
                    if str(port).startswith('${'): port = 5432
                    if str(host).startswith('${'): host = 'localhost'
                    if str(user).startswith('${'): user = 'postgres'
                    if str(password).startswith('${'): password = 'secret_password'
                    if str(name).startswith('${'): name = 'predictive_maintenance_db'
        except Exception:
            host, port, user, password, name = 'localhost', '5432', 'postgres', 'secret_password', 'predictive_maintenance_db'
            
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

# Configuración del motor de conexión y manejo de pooling
engine = create_engine(get_db_url(), pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """Context manager manual para las sesiones de Base de Datos."""
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()

def run_migrations():
    """Ejecuta cambios de esquema en caliente requeridos por los nuevos módulos."""
    try:
        with SessionLocal() as session:
            # Agregamos la columna details si no existe en audit_logs para cumplir el requerimiento
            session.execute(text("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS details TEXT;"))
            session.commit()
    except Exception as e:
        print(f"Alerta de migración: {e}")

run_migrations()
