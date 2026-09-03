import streamlit as st
from sqlalchemy import text
from core.db_manager import SessionLocal
from core.audit_logger import log_action

def get_role_permissions(role_id):
    """
    Consulta a la BD la matriz de permisos para un rol específico.
    Retorna una lista de nombres de permisos (ej: ['view_dashboard', 'run_models']).
    """
    try:
        with SessionLocal() as session:
            query = text("""
                SELECT p.name 
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = :role_id
            """)
            result = session.execute(query, {"role_id": role_id})
            return [row[0] for row in result]
    except Exception as e:
        print(f"Error obteniendo permisos para rol {role_id}: {e}")
        return []

def require_permission(permission_name):
    """
    Valida que el usuario en sesión activa tenga el permiso requerido.
    Detiene la ejecución en Streamlit si no cuenta con la autorización.
    """
    if "user" not in st.session_state or "token" not in st.session_state:
        st.error("🔒 Acceso denegado. Por favor, inicie sesión.")
        st.stop()
        
    user = st.session_state["user"]
    permissions = st.session_state.get("permissions", [])
    
    if permission_name not in permissions:
        st.error(f"⛔ Acceso denegado: No tienes el permiso requerido ({permission_name}) para este módulo.")
        log_action(
            user_id=user["id"], 
            action="UNAUTHORIZED_ACCESS", 
            details=f"Intento de acceso denegado a módulo protegido por: {permission_name}"
        )
        st.stop()
