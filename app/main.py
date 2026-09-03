import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    """Renderiza la aplicación principal y su navegación una vez autenticado."""
    user = st.session_state["user"]
    
    with st.sidebar:
        st.markdown(f"### 👤 Hola, **{user['username']}**")
        st.markdown(f"*Rol ID: {user['role_id']}*")
        st.divider()
        
        # Menú de Navegación Dinámico por Roles
        menu_options = ["Dashboard Principal"]
        if user["role_id"] in [1, 4]:  # Admin y Analista
            menu_options.append("EDA (Análisis Exploratorio)")
            menu_options.append("Fase 5: Evaluación de Modelos")
            menu_options.append("Fase 6: Despliegue (Producción)")
            menu_options.append("Reportes Profesionales")
            
        selection = st.radio("Navegación", menu_options)
        st.divider()
        
        # Logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            log_action(user["id"], "LOGOUT", details="Cierre de sesión manual")
            st.session_state.clear()
            st.rerun()

    if selection == "Dashboard Principal":
        # Panel Principal protegido con RBAC
        try:
            require_permission("view_dashboard")
            from app.components.dashboard_view import render_dashboard
            render_dashboard()
        except st.runtime.scriptrunner.StopException:
            pass
            
    elif selection == "EDA (Análisis Exploratorio)":
        from app.components.eda_view import render_eda
        render_eda()
        
    elif selection == "Fase 5: Evaluación de Modelos":
        from app.components.evaluation_view import render_evaluation
        render_evaluation()
        
    elif selection == "Fase 6: Despliegue (Producción)":
        from app.components.deployment_view import render_deployment
        render_deployment()
        
    elif selection == "Reportes Profesionales":
        from app.components.reports_view import render_reports
        render_reports()

if __name__ == "__main__":
    # Ruteo principal basado en el estado de la sesión
    if "token" not in st.session_state:
        render_login_page()
    else:
        render_main_app()
