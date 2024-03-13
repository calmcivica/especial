import random
import string
import streamlit as st

# You must launch this first to avoid the calling error
# of more than one application in the same streamlit
st.set_page_config(page_title="Especialidades", layout="wide")

import dbt_questions as dbt
import snow_questions as sn

PAGES = ["Intro 🔰", "Practicar 🥊", "Exámenes 📄", "Progreso 📈", "Parreitor-3000 🤖"]

# Creating perzonalized buttons
sn_init_button = """
        <style>.element-container:has(#button-after-sn) + div button {"""
dbt_init_button = """
        <style>.element-container:has(#button-after-dbt) + div button {"""
button = """
            border: none;
            color: white;
            padding: 20px 60px;
            text-align: center;
            justify-content: center;
            align-content:center;
            text-decoration: none;
            display: inline-block;
            font-size: 30px;
            margin: 10px;
            cursor: pointer;
            border-radius: 5px;
            min-width: 60%;
            """
sn_end_button = """background-color: #1e88e5;
        }</style>"""
dbt_end_button = """background-color: #f4511e;
        }</style>"""

### Session_state to:
# snowflake
def go_to_snowflake():
    st.session_state.page = 'snowflake'
# dbt
def go_to_dbt():
    st.session_state.page = 'dbt'

### Definig Main: ESPECIALIDADES
def go_to_main():
    st.session_state.page = 'main'
    # Set a title and subtitle
    st.markdown("<h1 style='text-align: center; color: white;'>Especialidades</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white;'>¿En qué especialidad quieres volverte un máquina?</h3>", unsafe_allow_html=True)

    # Center the buttons within a container
    st.markdown('<div class="container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="small")
    with col1:
        sn_button_complete = str(sn_init_button+button+sn_end_button)
        st.markdown(sn_button_complete, unsafe_allow_html=True)
        st.markdown('<span id="button-after-sn"></span>', unsafe_allow_html=True)
        st.button('Snowflake',on_click=go_to_snowflake)
    with col2:
        dbt_button_complete = str(dbt_init_button+button+dbt_end_button)
        st.markdown(dbt_button_complete, unsafe_allow_html=True)
        st.markdown('<span id="button-after-dbt"></span>', unsafe_allow_html=True)
        st.button('dbt',on_click=go_to_dbt)
    st.markdown('</div>', unsafe_allow_html=True)  # End of container div

######### SESSION_STATE to change between files:
## Main Page
# Initialize MAIN if session_state is not present or to return to main
if 'page' not in st.session_state or st.session_state.page == 'main':
    go_to_main()

## Snowflake Page
elif st.session_state.page == 'snowflake':
    st.title('Snowflake')
    if st.button('Back to Main', key='back-to-main-from-snowflake'):
        go_to_main()
        st.rerun()
    
    # Add a way to navigate within the Snowflake page
    current_page = st.selectbox("Choose section:", PAGES, key='current_snowflake_page')
    
    # Update the session state for the current page in Snowflake
    st.session_state['current_page'] = current_page
    
    # Execute the function based on the current_page
    if st.session_state['current_page'] == "Intro 🔰":
        sn.Comienzo()
    elif st.session_state['current_page'] == "Practicar 🥊":
        sn.practicar()
    elif st.session_state['current_page'] == "Exámenes 📄":
        sn.examen()
    elif st.session_state['current_page'] == "Progreso 📈":
        sn.progreso()
    elif st.session_state['current_page'] == "Parreitor-3000 🤖":
        sn.parreitor()

## dbt Page
elif st.session_state.page == 'dbt':
    st.title('dbt')
    if st.button('Back to Main', key="back-to-main-from-dbt"):
            go_to_main()
            st.rerun()
    
    # Add a way to navigate within the dbt page    
    current_page = st.selectbox("Choose section:", PAGES, key="current_dbt_page")
    
    # Update the session state for the current page in Snowflake
    st.session_state['current_page'] = current_page
    
    # Execute the function based on the current_page
    if st.session_state['current_page'] == "Intro 🔰":
        dbt.Comienzo()
    elif st.session_state['current_page'] == "Practicar 🥊":
        dbt.practicar()
    elif st.session_state['current_page'] == "Exámenes 📄":
        dbt.examen()
    elif st.session_state['current_page'] == "Progreso 📈":
        dbt.progreso()
    elif st.session_state['current_page'] == "Parreitor-3000 🤖":
        dbt.parreitor()