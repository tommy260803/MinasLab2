import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from core.auth_service import authenticate_user
from core.permissions import get_role_permissions, require_permission
from core.audit_logger import log_action
from app.components.ui_styles import (
    inject_enterprise_styles, apply_enterprise_plotly_theme,
    render_sidebar_header, render_user_profile, page_header,
    card_container_begin, card_container_end
)

# Configuración de página
st.set_page_config(page_title="Mantenimiento Predictivo", page_icon="⚙️", layout="wide")

# Inyectar CSS y temas
inject_enterprise_styles()
apply_enterprise_plotly_theme()

def render_login_page():
    """Renderiza la página de inicio de sesión."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        card_container_begin()
        st.markdown("<h2 style='text-align: center; margin-bottom: 8px;'>Plataforma Predictiva</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 24px;'>Acceso Corporativo</p>", unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submit_btn:
                if not username or not password:
                    st.warning("⚠️ Debes ingresar usuario y contraseña.")
                else:
                    with st.spinner("Autenticando..."):
                        success, msg, data = authenticate_user(username, password)
                    
                    if success:
                        token, user_data = data
                        st.session_state["token"] = token
                        st.session_state["user"] = user_data
                        st.session_state["permissions"] = get_role_permissions(user_data["role_id"])
                        log_action(user_data["id"], "LOGIN_SUCCESS", f"Login exitoso: {username}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                        log_action(None, "LOGIN_FAILED", f"Fallo de autenticación: {username}")
        card_container_end()

def render_main_app():
    """Renderiza la aplicación principal y su navegación."""
    user = st.session_state["user"]
    
    # Mapeo de roles para el frontend
    roles = {1: "Administrador", 2: "Operador", 3: "Invitado", 4: "Analista"}
    role_name = roles.get(user["role_id"], "Usuario")
    
    with st.sidebar:
        # 1. Identidad del sistema / usuario
        render_sidebar_header("MINER-AI PRO")
        render_user_profile(user['username'], role_name)
        
        # 2. Navegación principal
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; padding-left: 4px;">Navegación</div>', unsafe_allow_html=True)
        
        menu_options = {
            "dashboard": {"icon": "📊", "label": "Dashboard Principal"},
            "eda": {"icon": "🔬", "label": "Exploración de Datos"},
            "phase3": {"icon": "📋", "label": "Fase 3: Preparación de Datos"},
            "modeling": {"icon": "⚙️", "label": "Motor IA (Fase 4)"},
            "eval": {"icon": "🧠", "label": "Evaluación de Modelos"},
            "deploy": {"icon": "🚀", "label": "Despliegue Producción"},
            "reports": {"icon": "📑", "label": "Reportes Oficiales"}
        }
        
        # Filtrar opciones según rol
        available_keys = ["dashboard"]
        if user["role_id"] in [1, 4]:
            available_keys.extend(["eda", "phase3", "modeling", "eval", "deploy", "reports"])
            
        # Estado actual de navegación
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "dashboard"
            
        st.markdown('<div class="nav-button-container">', unsafe_allow_html=True)
        for key in available_keys:
            opt = menu_options[key]
            # Usar data-active en CSS si es posible, o marcadores visuales:
            is_active = st.session_state["current_page"] == key
            prefix = "🔹 " if is_active else "  "
            
            # En Streamlit los st.button nativos no soportan atributos custom directamente, 
            # así que simularemos el active state alterando el label o dependiendo del CSS global.
            label = f"{prefix}{opt['icon']}  {opt['label']}"
            
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state["current_page"] = key
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. Separador para filtros (los filtros se inyectarán aquí por las vistas individuales)
        st.markdown("<hr style='border: none; border-top: 1px solid #2D3139; margin: 16px 0;'>", unsafe_allow_html=True)
        
        # Reservamos un contenedor vacío para que las vistas puedan inyectar filtros
        filters_container = st.container()
        
        # 5. Acciones secundarias
        st.markdown("<div style='flex-grow: 1; min-height: 50px;'></div>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión", use_container_width=True):
            log_action(user["id"], "LOGOUT", "Cierre de sesión manual")
            st.session_state.clear()
            st.rerun()

    # Inyectamos el filters_container en session_state para que las vistas lo usen
    st.session_state["sidebar_filters"] = filters_container

    # Ruteo basado en current_page
    selection = st.session_state["current_page"]
    
    if selection == "dashboard":
        try:
            require_permission("view_dashboard")
            from app.components.dashboard_view import render_dashboard
            render_dashboard()
        except st.runtime.scriptrunner.StopException:
            pass
    elif selection == "eda":
        from app.components.eda_view import render_eda
        render_eda()
    elif selection == "phase3":
        from app.components.data_preparation_view import render_data_preparation
        render_data_preparation()
    elif selection == "modeling":
        from app.components.modeling_view import render_modeling
        render_modeling()
    elif selection == "eval":
        from app.components.evaluation_view import render_evaluation
        render_evaluation()
    elif selection == "deploy":
        from app.components.deployment_view import render_deployment
        render_deployment()
    elif selection == "reports":
        from app.components.reports_view import render_reports
        render_reports()

if __name__ == "__main__":
    if "token" not in st.session_state:
        render_login_page()
    else:
        render_main_app()
