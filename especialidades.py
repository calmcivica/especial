import streamlit as st
import logging
from logging.handlers import RotatingFileHandler
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set page config first
st.set_page_config(page_title="Especialidades", layout="wide")

# Import dependencies after page config
import tools as t
import sql_especialidad.tools_sql as tsql
import helper as h
import json_and_excels_admin as jtc
import pandas as pd

# Constants
PAGES = [
    "Intro 🔰",
    "Practicar 🥊",
    "Exámenes 📄",
    "Progreso 📈",
    "Parreitor-3000 🤖",
    "Chatgpt"
]

# Button styling with sanitized CSS
BUTTON_STYLES = {
    "snowflake": """
        <style>.element-container:has(#button-after-sn) + div button {
            border: none;
            color: white;
            padding: 60px 60px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            background-color: #1e88e5;
        }</style>
    """,
    "snowflake_2": """
        <style>.element-container:has(#button-after-sn_2) + div button {
            border: none;
            color: white;
            padding: 60px 60px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            background-color: #1e88e5;
        }</style>
    """,
    "dbt": """
        <style>.element-container:has(#button-after-dbt) + div button {
            border: none;
            color: white;
            padding: 60px 60px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            background-color: #f4511e;
        }</style>
    """,
    "google": """
        <style>.element-container:has(#button-after-google) + div button {
            border: none;
            color: white;
            padding: 60px 60px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            background-color: #ffba03;
        }</style>
    """,
    "sql": """
        <style>.element-container:has(#button-after-sql) + div button {
            border: none;
            color: white;
            padding: 60px 60px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            background-color: #12d519;
        }</style>
    """
}

# Session state navigation functions
def go_to_page(page_name):
    """Generic function to navigate to different pages"""
    st.session_state.page = page_name
    
def go_to_snowflake():
    go_to_page("snowflake")

def go_to_snowflake_pro():
    go_to_page("snowflake_pro")

def go_to_snowflake_arch():
    go_to_page("snowflake_arch")

def go_to_dbt():
    go_to_page("dbt")

def go_to_google():
    go_to_page("google")

def go_to_sql():
    go_to_page("sql")

def go_to_admin():
    go_to_page("ADMIN")

def go_to_main():
    go_to_page("main")

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "main"
if "current_page" not in st.session_state:
    st.session_state["current_page"] = PAGES[0]

def main_page():
    """Render the main page with certification options"""
    try:
        # Admin button
        st.button("ADMIN", on_click=go_to_admin)
        
        # Set title and subtitle
        st.markdown(
            "<h1 style='text-align: center;'>Especialidades</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='text-align: center;'>¿En qué especialidad quieres volverte un máquina?</h3>",
            unsafe_allow_html=True,
        )
        
        # First row of options
        col1_1, col1_2, col1_3 = st.columns([1, 1, 1], gap="medium")
        
        with col1_1:
            st.markdown(BUTTON_STYLES["snowflake"], unsafe_allow_html=True)
            st.markdown('<span id="button-after-sn"></span>', unsafe_allow_html=True)
            col1_1.button(
                "Snowflake", on_click=go_to_snowflake, use_container_width=True
            )
        
        with col1_2:
            st.markdown(BUTTON_STYLES["dbt"], unsafe_allow_html=True)
            st.markdown('<span id="button-after-dbt"></span>', unsafe_allow_html=True)
            col1_2.button("dbt", on_click=go_to_dbt, use_container_width=True)
        
        with col1_3:
            st.markdown(BUTTON_STYLES["google"], unsafe_allow_html=True)
            st.markdown(
                '<span id="button-after-google"></span>', unsafe_allow_html=True
            )
            col1_3.button(
                "GCP - Google", on_click=go_to_google, use_container_width=True
            )
        
        # Second row of options
        col2_1, col2_2, col2_3 = st.columns([1, 1, 1], gap="medium")
        
        with col2_1:
            st.markdown(BUTTON_STYLES["sql"], unsafe_allow_html=True)
            st.markdown('<span id="button-after-sql"></span>', unsafe_allow_html=True)
            col2_1.button("SQL", on_click=go_to_sql, use_container_width=True)

    except Exception as e:
        logger.error(f"Error in main page: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def render_snowflake_page():
    """Render the Snowflake certification selection page"""
    if st.button("Back to Main", key="back-to-main-from-snowflake"):
        go_to_main()
    
    try:
        st.markdown(
            "<h1 style='text-align: center;'>❄️Snowflake❄️</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='text-align: center;'>¿Qué certificación de Snowflake quieres?</h3>",
            unsafe_allow_html=True,
        )
        
        col1_1, col1_2, col1_3 = st.columns([1, 1, 1], gap="medium")
        
        with col1_1:
            st.markdown(BUTTON_STYLES["snowflake"], unsafe_allow_html=True)
            st.markdown('<span id="button-after-sn"></span>', unsafe_allow_html=True)
            col1_1.button(
                "Snowflake Pro", on_click=go_to_snowflake_pro, use_container_width=True
            )
        
        with col1_2:
            st.markdown(BUTTON_STYLES["snowflake_2"], unsafe_allow_html=True)
            st.markdown('<span id="button-after-sn_2"></span>', unsafe_allow_html=True)
            col1_2.button(
                "Snowflake Arch", on_click=go_to_snowflake_arch, use_container_width=True
            )
    
    except Exception as e:
        logger.error(f"Error in Snowflake page: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def render_certification_page(certification_type):
    """
    Generic function to render certification study pages
    
    Args:
        certification_type (str): The type of certification (snowflake_pro, snowflake_arch, dbt, google)
    """
    # Mapping for titles
    titles = {
        "snowflake_pro": "SnowPro® Core Certification",
        "snowflake_arch": "SnowPro® Advanced: Architect",
        "dbt": "dbt",
        "google": "GCP - Google" 
    }
    
    # Initialize database connection
    conn = h.init_connection(certification_type)
    
    # Initialize data
    datos = t.get_datos(certification_type)
    
    # Get user
    user = h.get_user_none()
    
    # Title
    st.title(titles[certification_type])
    
    # Back button
    if st.button("Back to Main", key=f"back-to-main-from-{certification_type}"):
        go_to_main()
        st.rerun()
    
    # Configure pages based on certification type
    available_pages = PAGES.copy()
    if certification_type in ["dbt", "google"]:
        available_pages.remove("Parreitor-3000 🤖")
    else:
        available_pages.remove("Chatgpt")
    
    # Page selection
    current_page = st.selectbox(
        "Choose section:", 
        available_pages, 
        key=f"current_{certification_type}_page"
    )
    
    # Update session state
    st.session_state["current_page"] = current_page
    
    # Render selected page
    try:
        if current_page == "Intro 🔰":
            t.comienzo(conn, certification_type)
        elif current_page == "Practicar 🥊":
            t.practicar(conn, datos, certification_type)
        elif current_page == "Exámenes 📄":
            t.examen(conn, datos, certification_type)
        elif current_page == "Progreso 📈":
            t.progreso(conn, datos, certification_type)
        elif current_page == "Parreitor-3000 🤖":
            t.parreitor(conn, certification_type)
        elif current_page == "Chatgpt":
            st.title("No está en funcionamiento este apartado")
    except Exception as e:
        logger.error(f"Error in {certification_type} {current_page} page: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def render_sql_page():
    """Render the SQL practice page"""
    especialidad = "sql"
    engine = h.init_connection(especialidad)
    
    st.title(":bar_chart: SQL Query Comparison Tool :slot_machine:")
    
    if st.button("Back to Main", key="back-to-main-from-sql"):
        go_to_main()
        st.rerun()
    
    # Get username
    username = t.menu(engine, especialidad)
    
    # Initialize session state variables
    if "input_list" not in st.session_state:
        st.session_state["input_list"] = []
    if "counter" not in st.session_state:
        st.session_state["counter"] = 0
    if "show" not in st.session_state:
        st.session_state["show"] = 0
    
    try:
        # Display SQL exercises
        option_w, option = tsql.display_casos_exercises(tsql.date_control(engine))
        
        if option_w is not None:
            with st.expander(f"¿Cómo es el {option_w}? 🤔"):
                st.info(
                    "Recuerda que para hacer los ejercicios tienes que terminar todas las consultas en ';' sin dejar ningún espacio detrás de ese punto y coma."
                )
                st.info(
                    "Ejemplo de consulta: SELECT * FROM CASE01.MENU;  ->  Como puedes ver todos los casos se nombran como 'CASE0' y el número que sea del caso."
                )
                st.image(f"./sql_especialidad/images/{option_w}.png")
        
        if option is not None:
            st.divider()
            tsql.enunciado(engine, option)
            
            # When exercise is selected
            if option:
                tsql.do_you_need("Temporary table", engine)
                tsql.do_you_need("Function", engine)
                tsql.do_you_need("Procedure", engine)
                st.divider()
                
                query1 = st.text_area("Enter SQL SELECT Query:", height=300)
                
                col1, col2 = st.columns([1, 1], gap="medium")
                with col1:
                    # User result
                    if st.button("Show result"):
                        tsql.show_result_1()
                with col2:
                    # Compare queries
                    if st.button("Compare YOUR SOLUTION", on_click=tsql.counter_add_1):
                        tsql.show_result_2()
                
                # Only user result
                if st.session_state["show"] == 1:
                    tsql.show_tables(engine, query1, option, False, username)
                
                # Compare solution with the user
                if st.session_state["show"] == 2:
                    tsql.show_tables(engine, query1, option, True, username)
    
    except Exception as e:
        logger.error(f"Error in SQL page: {str(e)}", exc_info=True)
        st.error(str(e))

def render_admin_page():
    """Render the admin panel"""
    jtc.show_admin_panel()
    
    # Button to return to main page
    if st.button("Volver a la página principal"):
        go_to_main()
        st.rerun()

# Main application flow
if "page" not in st.session_state or st.session_state.page == "main":
    main_page()
elif st.session_state.page == "snowflake":
    render_snowflake_page()
elif st.session_state.page == "snowflake_pro":
    render_certification_page("snowflake_pro")
elif st.session_state.page == "snowflake_arch":
    render_certification_page("snowflake_arch")
elif st.session_state.page == "dbt":
    render_certification_page("dbt")
elif st.session_state.page == "google":
    render_certification_page("google")
elif st.session_state.page == "sql":
    render_sql_page()
elif st.session_state.page == "ADMIN":
    render_admin_page()