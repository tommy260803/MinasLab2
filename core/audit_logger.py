from datetime import datetime
from sqlalchemy import text
import socket
from core.db_manager import SessionLocal

def get_ip():
    """Obtiene la IP local para el registro."""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return '127.0.0.1'

def log_action(user_id, action, ip_address=None, details=None):
    """
    Registra una operación en la bitácora de accesos.
    Captura timestamp, IP y detalle de la operación.
    """
    if ip_address is None:
        ip_address = get_ip()
        
    try:
        with SessionLocal() as session:
            query = text("""
                INSERT INTO audit_logs (user_id, action, ip_address, details, created_at) 
                VALUES (:user_id, :action, :ip, :details, :created_at)
            """)
            session.execute(query, {
                "user_id": user_id,
                "action": action,
                "ip": ip_address,
                "details": details,
                "created_at": datetime.now()
            })
            session.commit()
    except Exception as e:
        # Fallback robusto en caso de que falte la columna 'details' en la BD u otro problema
        try:
            with SessionLocal() as session:
                full_action = f"{action} | {details}" if details else action
                query_fallback = text("""
                    INSERT INTO audit_logs (user_id, action, ip_address, created_at) 
                    VALUES (:user_id, :action, :ip, :created_at)
                """)
                session.execute(query_fallback, {
                    "user_id": user_id,
                    "action": full_action[:255],
                    "ip": ip_address,
                    "created_at": datetime.now()
                })
                session.commit()
        except Exception as fallback_err:
            print(f"Error crítico al registrar bitácora: {fallback_err}")
