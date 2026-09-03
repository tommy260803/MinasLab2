import streamlit as st
from core.permissions import require_permission

def require_auth():
    """Utilidad para proteger páginas individuales."""
    if "token" not in st.session_state:
        st.error("Debe iniciar sesión para acceder a esta página.")
        st.stop()
