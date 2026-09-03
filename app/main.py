import streamlit as st
from core.auth_service import authenticate_user
from core.permissions import get_role_permissions, require_permission
from core.audit_logger import log_action

# Configuración de página
st.set_page_config(page_title="App Mantenimiento Predictivo", page_icon="⚙️", layout="wide")

def render_login_page():
    """Renderiza la página de inicio de sesión."""
    st.title("⚙️ Mantenimiento Predictivo Minero")
    st.markdown("### Acceso al Sistema")
    
    # Centrar el formulario de login visualmente
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=True):
            st.markdown("Por favor ingrese sus credenciales para continuar.")
            username = st.text_input("Usuario", placeholder="ej. admin_juan")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submit_btn:
                if not username or not password:
                    st.warning("⚠️ Debes ingresar usuario y contraseña.")
                else:
                    with st.spinner("Autenticando..."):
                        success, msg, data = authenticate_user(username, password)
                    
                    if success:
                        token, user_data = data
                        # NUNCA guardamos el password en session_state, solo el token y metadata
                        st.session_state["token"] = token
                        st.session_state["user"] = user_data
                        st.session_state["permissions"] = get_role_permissions(user_data["role_id"])
                        
                        # Registro de auditoría
                        log_action(
                            user_id=user_data["id"], 
                            action="LOGIN_SUCCESS", 
                            details=f"Login exitoso para el usuario {username}"
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                        # Registrar intento fallido
                        log_action(
                            user_id=None, 
                            action="LOGIN_FAILED", 
                            details=f"Fallo de autenticación para username: {username}"
                        )

def render_main_app():
    """Renderiza la aplicación principal una vez autenticado."""
    user = st.session_state["user"]
    
    with st.sidebar:
        st.markdown(f"### 👤 Hola, **{user['username']}**")
        st.markdown(f"*Rol ID: {user['role_id']}*")
        st.divider()
        
        # Logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            log_action(user["id"], "LOGOUT", details="Cierre de sesión manual")
            st.session_state.clear()
            st.rerun()

    st.title("📊 Panel de Control (Dashboard)")
    
    # Ejemplo de protección RBAC en la interfaz
    try:
        # Se verifica si tiene permiso para ver el dashboard
        require_permission("view_dashboard")
        
        st.success("¡Bienvenido al sistema! Tienes acceso a esta sección.")
        
        # Registrar acceso al módulo principal de forma silenciosa
        if not st.session_state.get("dashboard_logged"):
            log_action(user["id"], "ACCESS_MODULE", details="Acceso al módulo: Dashboard")
            st.session_state["dashboard_logged"] = True
            
        col1, col2 = st.columns(2)
        with col1:
            st.info("Aquí irán las métricas principales (KPIs) de los equipos.")
        with col2:
            if "run_models" in st.session_state["permissions"]:
                st.warning("🤖 Tienes permiso especial para ejecutar modelos IA.")
                if st.button("Ejecutar Modelo Predictivo"):
                    log_action(user["id"], "RUN_AI_MODEL", details="Ejecución manual de predicción IA")
                    st.toast("Modelo ejecutado exitosamente.")
            else:
                st.write("No tienes permisos para ejecutar modelos IA.")
                
    except st.runtime.scriptrunner.StopException:
        # StopException es lanzado por st.stop() en require_permission
        pass

if __name__ == "__main__":
    # Ruteo principal basado en el estado de la sesión
    if "token" not in st.session_state:
        render_login_page()
    else:
        render_main_app()
