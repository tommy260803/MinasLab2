import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

def inject_enterprise_styles():
    """Inyecta el CSS global para un diseño empresarial, limpio y moderno."""
    css = """
    <style>
    /* Reset and Base Styles */
    :root {
        --bg-primary: #0E1117;
        --bg-secondary: #1E2127;
        --border-color: #2D3139;
        --text-primary: #E2E8F0;
        --text-secondary: #94A3B8;
        --accent-primary: #2962FF;
        --accent-hover: #1E4BD8;
        --success: #00C853;
        --warning: #FFAB00;
        --critical: #D50000;
    }

    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    
    .enterprise-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 24px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 12px;
        color: #FFFFFF;
    }

    .enterprise-subtitle {
        font-size: 18px;
        font-weight: 600;
        margin-top: 24px;
        margin-bottom: 16px;
        color: var(--text-primary);
    }

    /* Sidebar Redesign */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }
    
    /* Hide default sidebar padding to control it via our components */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 20px;
    }

    /* Sidebar Navigation Custom Buttons */
    .nav-button-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 24px;
    }
    
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
        text-align: left !important;
        padding: 12px 16px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        margin-bottom: 8px !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] button p {
        font-size: 14px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    
    /* Active Nav Button */
    [data-testid="stSidebar"] button[data-active="true"] {
        background-color: rgba(41, 98, 255, 0.1) !important;
        color: var(--accent-primary) !important;
        border: 1px solid rgba(41, 98, 255, 0.3) !important;
    }

    /* Enterprise Cards */
    .enterprise-card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 24px;
    }

    /* KPI Cards */
    .kpi-container {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        height: 100%;
        min-height: 120px;
    }
    
    .kpi-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
        margin: 0 0 12px 0;
    }
    
    .kpi-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .kpi-badge.success { background-color: rgba(0, 200, 83, 0.15); color: #4ADE80; }
    .kpi-badge.warning { background-color: rgba(255, 171, 0, 0.15); color: #FBBF24; }
    .kpi-badge.critical { background-color: rgba(213, 0, 0, 0.15); color: #F87171; }
    .kpi-badge.neutral { background-color: rgba(148, 163, 184, 0.15); color: #94A3B8; }
    
    .kpi-icon {
        font-size: 24px;
        color: var(--text-secondary);
        opacity: 0.7;
    }

    /* Tables */
    .enterprise-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 14px;
        margin: 16px 0;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }
    
    .enterprise-table th {
        background-color: rgba(255, 255, 255, 0.03);
        color: var(--text-secondary);
        font-weight: 600;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.05em;
    }
    
    .enterprise-table td {
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
        color: var(--text-primary);
    }
    
    .enterprise-table tr:last-child td {
        border-bottom: none;
    }
    
    .enterprise-table tbody tr:hover {
        background-color: rgba(255, 255, 255, 0.02);
    }

    /* Fix Streamlit metric generic */
    div[data-testid="metric-container"] {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        padding: 16px;
        border-radius: 8px;
    }

    /* Sidebar User Profile */
    .user-profile {
        display: flex;
        align-items: center;
        padding: 16px;
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        margin-bottom: 24px;
    }
    
    .user-avatar {
        width: 40px;
        height: 40px;
        background-color: var(--accent-primary);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        margin-right: 12px;
        font-size: 16px;
    }
    
    .user-details {
        flex: 1;
    }
    
    .user-name {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-primary);
        margin: 0;
    }
    
    .user-role {
        font-size: 12px;
        color: var(--text-secondary);
        margin: 0;
    }

    /* Fix Streamlit Input Text Colors */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="select"] span, 
    div[data-baseweb="tag"] span,
    div[data-baseweb="popover"] li,
    div[role="listbox"] li {
        color: #E2E8F0 !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def apply_enterprise_plotly_theme():
    """Genera y registra un tema de Plotly empresarial para mantener consistencia visual."""
    enterprise_colors = ['#2962FF', '#00C853', '#FFAB00', '#D50000', '#9C27B0', '#00BCD4']
    
    template = go.layout.Template()
    template.layout.plot_bgcolor = 'rgba(0,0,0,0)'
    template.layout.paper_bgcolor = 'rgba(0,0,0,0)'
    template.layout.font.color = '#94A3B8'
    template.layout.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    
    # Ejes
    template.layout.xaxis.gridcolor = '#2D3139'
    template.layout.yaxis.gridcolor = '#2D3139'
    template.layout.xaxis.linecolor = '#2D3139'
    template.layout.yaxis.linecolor = '#2D3139'
    template.layout.xaxis.zerolinecolor = '#2D3139'
    template.layout.yaxis.zerolinecolor = '#2D3139'
    
    template.layout.colorway = enterprise_colors
    
    pio.templates['enterprise_dark'] = template
    pio.templates.default = 'enterprise_dark'

def render_kpi_card(title, value, status="neutral", status_text=None, icon="📊"):
    """
    Renderiza un KPI profesional.
    status: 'success', 'warning', 'critical', 'neutral'
    """
    badge_html = f'<div class="kpi-badge {status}">{status_text}</div>' if status_text else ''
    
    html = f"""
    <div class="kpi-container">
        <div>
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            {badge_html}
        </div>
        <div class="kpi-icon">{icon}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_styled_table(df, max_rows=100):
    """Renderiza un DataFrame como una tabla empresarial HTML limpia."""
    if df.empty:
        st.info("No hay datos disponibles para mostrar.")
        return
        
    html = df.head(max_rows).to_html(classes='enterprise-table', index=False, escape=False)
    st.markdown(html, unsafe_allow_html=True)

def render_user_profile(username, role_name):
    """Renderiza la tarjeta de usuario en el sidebar."""
    initials = username[:2].upper() if username else "U"
    html = f"""
    <div class="user-profile">
        <div class="user-avatar">{initials}</div>
        <div class="user-details">
            <p class="user-name">{username}</p>
            <p class="user-role">{role_name}</p>
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)

def render_sidebar_header(title="SISTEMA EMPRESARIAL"):
    """Renderiza un encabezado limpio para el sidebar."""
    html = f"""
    <div style="padding: 10px 0 24px 0;">
        <h2 style="font-size: 18px; font-weight: 700; color: #FFFFFF; margin: 0; letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="#2962FF" stroke-width="2"/>
                <path d="M8 12L11 15L16 9" stroke="#2962FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {title}
        </h2>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)

def page_header(title, subtitle=None):
    """Renderiza el título principal de una página."""
    html = f'<div class="enterprise-title">{title}</div>'
    if subtitle:
        html += f'<p style="color: #94A3B8; margin-top: -16px; margin-bottom: 24px; font-size: 14px;">{subtitle}</p>'
    st.markdown(html, unsafe_allow_html=True)

def section_header(title):
    """Renderiza un título de sección."""
    html = f'<div class="enterprise-subtitle">{title}</div>'
    st.markdown(html, unsafe_allow_html=True)

def card_container_begin():
    """Inicia un contenedor estilo tarjeta."""
    st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)

def card_container_end():
    """Cierra un contenedor estilo tarjeta."""
    st.markdown('</div>', unsafe_allow_html=True)
