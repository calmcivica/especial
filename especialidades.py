
import streamlit as st

# Launching this first to avoid the calling error
# of more than one application in the same streamlit
st.set_page_config(page_title="Especialidades", layout="wide")

import tools as t
import helper as h

PAGES = ["Intro 🔰", "Practicar 🥊", "Exámenes 📄", "Progreso 📈", "Parreitor-3000 🤖", "Chatpgt"]

# Creating perzonalized buttons
sn_init_button = """
        <style>.element-container:has(#button-after-sn) + div button {"""
dbt_init_button = """
        <style>.element-container:has(#button-after-dbt) + div button {"""
google_init_button = """
        <style>.element-container:has(#button-after-google) + div button {"""
button = """
            border: none;
            color: white;
            padding: 60px 60px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            """
sn_end_button = """background-color: #1e88e5;
        }</style>"""
dbt_end_button = """background-color: #f4511e;
        }</style>"""
google_end_button = """background-color: #ffba03;
        }</style>"""

### Session_state to:
# snowflake
def go_to_snowflake():
    st.session_state.page = 'snowflake'
# dbt
def go_to_dbt():
    st.session_state.page = 'dbt'
# google
def go_to_google():
    st.session_state.page = 'google'


### Definig Main: ESPECIALIDADES
def go_to_main():
    try:
        st.session_state.page = 'main'
        # # Set a title and subtitle
        st.markdown("<h1 style='text-align: center; color: white;'>Especialidades</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: white;'>¿En qué especialidad quieres volverte un máquina?</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1], gap="medium")
        with col1:
            sn_button_complete = str(sn_init_button+button+sn_end_button)
            st.markdown(sn_button_complete, unsafe_allow_html=True)
            st.markdown('<span id="button-after-sn"></span>', unsafe_allow_html=True)
            col1.button('Snowflake',on_click=go_to_snowflake, use_container_width=True)
        with col2:
            dbt_button_complete = str(dbt_init_button+button+dbt_end_button)
            st.markdown(dbt_button_complete, unsafe_allow_html=True)
            st.markdown('<span id="button-after-dbt"></span>', unsafe_allow_html=True)
            col2.button('dbt',on_click=go_to_dbt, use_container_width=True)
        with col3:
            dbt_button_complete = str(google_init_button+button+google_end_button)
            st.markdown(dbt_button_complete, unsafe_allow_html=True)
            st.markdown('<span id="button-after-google"></span>', unsafe_allow_html=True)
            col3.button('GCP - Google',on_click=go_to_google, use_container_width=True)
    except Exception as e:
        st.warning("Error: " + str(e.args))

######################################################################       
######### PAGES
######################################################################
## Main Page
# Initialize MAIN if session_state is not present or to return to main
if 'page' not in st.session_state or st.session_state.page == 'main':
    go_to_main()

## Snowflake Page
elif st.session_state.page == 'snowflake':
    # Initializations
    conn = h.init_connection()
    especialidad = "snowflake"
    datos = t.get_datos(especialidad)
    user = h.get_user_none()

    st.title('Snowflake')
    if st.button('Back to Main', key='back-to-main-from-snowflake'):
        go_to_main()
        st.rerun()
    
    PAGES.remove("Chatpgt")
    # Add a way to navigate within the Snowflake page
    current_page = st.selectbox("Choose section:", PAGES, key='current_snowflake_page')
    
    # Update the session state for the current page in Snowflake
    st.session_state['current_page'] = current_page
    
    # Execute the function based on the current_page
    if st.session_state['current_page'] == "Intro 🔰":
        try:
            t.comienzo(conn, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Practicar 🥊":
        try:
            t.practicar(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Exámenes 📄":
        try:
            t.examen(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Progreso 📈":
        try:
            t.progreso(conn,datos)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Parreitor-3000 🤖":
        t.parreitor(conn, especialidad)

## dbt Page
elif st.session_state.page == 'dbt':
    # Init connection
    conn = h.init_connection()
    # Init json
    especialidad = "dbt"
    datos = t.get_datos(especialidad)
    # Init user
    user = h.get_user_none()

    st.title('dbt')
    if st.button('Back to Main', key='back-to-main-from-dbt'):
        go_to_main()
        st.rerun()
    
    PAGES.remove("Parreitor-3000 🤖")
    # Add a way to navigate within the dbt page
    current_page = st.selectbox("Choose section:", PAGES, key='current_dbt_page')
    
    # Update the session state for the current page in dbt
    st.session_state['current_page'] = current_page
    
    # Execute the function based on the current_page
    if st.session_state['current_page'] == "Intro 🔰":
        t.comienzo(conn, especialidad)
    elif st.session_state['current_page'] == "Practicar 🥊":
        try:
            t.practicar(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Exámenes 📄":
        try:
            t.examen(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Progreso 📈":
        t.progreso(conn,datos)
    elif st.session_state['current_page'] == "Chatpgt":
        st.title("No está en funcionamiento este apartado")
        # t.chatgpt(conn, especialidad)


## Google Page
elif st.session_state.page == 'google':
    # Init connection
    conn = h.init_connection()
    # Init json
    especialidad = "google"
    datos = t.get_datos(especialidad)
    # Init user
    user = h.get_user_none()

    st.title('GCP - Google')
    if st.button('Back to Main', key='back-to-main-from-google'):
        go_to_main()
        st.rerun()
    
    PAGES.remove("Parreitor-3000 🤖")
    # Add a way to navigate within the dbt page
    current_page = st.selectbox("Choose section:", PAGES, key='current_google_page')
    
    # Update the session state for the current page in dbt
    st.session_state['current_page'] = current_page
    
    # Execute the function based on the current_page
    if st.session_state['current_page'] == "Intro 🔰":
        t.comienzo(conn, especialidad)
    elif st.session_state['current_page'] == "Practicar 🥊":
        try:
            t.practicar(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Exámenes 📄":
        try:
            t.examen(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error: " + str(e.args))
    elif st.session_state['current_page'] == "Progreso 📈":
        t.progreso(conn,datos)
    elif st.session_state['current_page'] == "Chatpgt":
        st.title("No está en funcionamiento este apartado")
        # t.chatgpt(conn, especialidad)