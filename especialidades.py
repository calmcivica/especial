import streamlit as st

# Launching this first to avoid the calling error
# of more than one application in the same streamlit
st.set_page_config(page_title="Especialidades", layout="wide")

import tools as t
import sql_especialidad.tools_sql as tsql
import helper as h

PAGES = [
    "Intro 🔰",
    "Practicar 🥊",
    "Exámenes 📄",
    "Progreso 📈",
    "Parreitor-3000 🤖",
    "Chatgpt",
]

#############################
##  BOTONES CLARO - OSCURO
## No se puede poner en tools porque si no peta y está recargando continuamente ms
## generándose un loop continuo que peta el pc
#############################
# ms = st.session_state
# if "themes" not in ms:
#     ms.themes = {
#         "current_theme": "light",
#         "refreshed": True,
#         "dark": {
#             "theme.base": "dark",
#             "theme.backgroundColor": "#0e1117",
#             "theme.primaryColor": "#ff5a31",
#             "theme.secondaryBackgroundColor": "#f18c124f",
#             "theme.textColor": "white",
#             "button_face": "🌜- DARK",
#         },
#         "light": {
#             "theme.base": "light",
#             "theme.backgroundColor": "white",
#             "theme.primaryColor": "#ff5a31",
#             "theme.secondaryBackgroundColor": "#f18c124f",
#             "theme.textColor": "#0a1464",
#             "button_face": "🌞 - LIGHT",
#         }
#     }


# def change_theme():
#     previous_theme = ms.themes["current_theme"]
#     tdict = (
#         ms.themes["light"]
#         if ms.themes["current_theme"] == "light"
#         else ms.themes["dark"]
#     )
#     for vkey, vval in tdict.items():
#         if vkey.startswith("theme"):
#             st._config.set_option(vkey, vval)

#     ms.themes["refreshed"] = False
#     if previous_theme == "dark":
#         ms.themes["current_theme"] = "light"
#     elif previous_theme == "light":
#         ms.themes["current_theme"] = "dark"


######################################################

# Creating perzonalized buttons
sn_init_button = """
        <style>.element-container:has(#button-after-sn) + div button {"""
dbt_init_button = """
        <style>.element-container:has(#button-after-dbt) + div button {"""
google_init_button = """
        <style>.element-container:has(#button-after-google) + div button {"""
sql_init_button = """
        <style>.element-container:has(#button-after-sql) + div button {
"""
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
sql_end_button = """background-color: #12d519;
        }</style>"""


### Session_state to:
# snowflake
def go_to_snowflake():
    st.session_state.page = "snowflake"


# dbt
def go_to_dbt():
    st.session_state.page = "dbt"


# google
def go_to_google():
    st.session_state.page = "google"


# sql
def go_to_sql():
    st.session_state.page = "sql"


### Definig Main: ESPECIALIDADES
def go_to_main():
    try:
        st.session_state.page = "main"
        # # Set a title and subtitle
        st.markdown(
            "<h1 style='text-align: center;'>Especialidades</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h3 style='text-align: center;'>¿En qué especialidad quieres volverte un máquina?</h3>",
            unsafe_allow_html=True,
        )
        col1_1, col1_2, col1_3 = st.columns([1, 1, 1], gap="medium")
        with col1_1:
            sn_button_complete = str(sn_init_button + button + sn_end_button)
            st.markdown(sn_button_complete, unsafe_allow_html=True)
            st.markdown('<span id="button-after-sn"></span>', unsafe_allow_html=True)
            col1_1.button(
                "Snowflake", on_click=go_to_snowflake, use_container_width=True
            )
        with col1_2:
            dbt_button_complete = str(dbt_init_button + button + dbt_end_button)
            st.markdown(dbt_button_complete, unsafe_allow_html=True)
            st.markdown('<span id="button-after-dbt"></span>', unsafe_allow_html=True)
            col1_2.button("dbt", on_click=go_to_dbt, use_container_width=True)
        with col1_3:
            dbt_button_complete = str(google_init_button + button + google_end_button)
            st.markdown(dbt_button_complete, unsafe_allow_html=True)
            st.markdown(
                '<span id="button-after-google"></span>', unsafe_allow_html=True
            )
            col1_3.button(
                "GCP - Google", on_click=go_to_google, use_container_width=True
            )
        # Siguiente fila
        col2_1, col2_2, col2_3 = st.columns([1, 1, 1], gap="medium")
        with col2_1:
            sql_button_complete = str(sql_init_button + button + sql_end_button)
            st.markdown(sql_button_complete, unsafe_allow_html=True)
            st.markdown('<span id="button-after-sql"></span>', unsafe_allow_html=True)
            col2_1.button("SQL", on_click=go_to_sql, use_container_width=True)

    except Exception as e:
        st.warning("Error 1: " + str(e.args))


######################################################################
######### PAGES
######################################################################
## Main Page
# Initialize MAIN if session_state is not present or to return to main
if "page" not in st.session_state or st.session_state.page == "main":
    # btn_face = (
    #     ms.themes["light"]["button_face"]
    #     if ms.themes["current_theme"] == "light"
    #     else ms.themes["dark"]["button_face"]
    # )
    # st.button(btn_face, on_click=change_theme)
    # if ms.themes["refreshed"] == False:
    #     ms.themes["refreshed"] = True
    #     st.rerun()
    
    go_to_main()

## Snowflake Page
elif st.session_state.page == "snowflake":
    especialidad = "snowflake"
    # Init connection
    conn = h.init_connection(especialidad)
    # Init json
    datos = t.get_datos(especialidad)
    # Init user
    user = h.get_user_none()

    st.title("Snowflake")
    if st.button("Back to Main", key="back-to-main-from-snowflake"):
        go_to_main()
        st.rerun()

    PAGES.remove("Chatgpt")
    # Add a way to navigate within the Snowflake page
    current_page = st.selectbox("Choose section:", PAGES, key="current_snowflake_page")

    # Update the session state for the current page in Snowflake
    st.session_state["current_page"] = current_page

    # Execute the function based on the current_page
    if st.session_state["current_page"] == "Intro 🔰":
        t.comienzo(conn, especialidad)
    elif st.session_state["current_page"] == "Practicar 🥊":
        try:
            t.practicar(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error 2:  " + str(e.args))
    elif st.session_state["current_page"] == "Exámenes 📄":
        try:
            t.examen(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error 3: " + str(e.args))
    elif st.session_state["current_page"] == "Progreso 📈":
        t.progreso(conn, datos, especialidad)
    elif st.session_state["current_page"] == "Parreitor-3000 🤖":
        t.parreitor(conn, especialidad)

## dbt Page
elif st.session_state.page == "dbt":
    especialidad = "dbt"
    # Init connection
    conn = h.init_connection(especialidad)
    # Init json
    datos = t.get_datos(especialidad)
    # Init user
    user = h.get_user_none()

    st.title("dbt")
    if st.button("Back to Main", key="back-to-main-from-dbt"):
        go_to_main()
        st.rerun()

    PAGES.remove("Parreitor-3000 🤖")
    # Add a way to navigate within the dbt page
    current_page = st.selectbox("Choose section:", PAGES, key="current_dbt_page")

    # Update the session state for the current page in dbt
    st.session_state["current_page"] = current_page

    # Execute the function based on the current_page
    if st.session_state["current_page"] == "Intro 🔰":
        t.comienzo(conn, especialidad)
    elif st.session_state["current_page"] == "Practicar 🥊":
        try:
            t.practicar(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error 4: " + str(e.args))
    elif st.session_state["current_page"] == "Exámenes 📄":
        try:
            t.examen(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error 5: " + str(e.args))
    elif st.session_state["current_page"] == "Progreso 📈":
        t.progreso(conn, datos, especialidad)
    elif st.session_state["current_page"] == "Chatgpt":
        st.title("No está en funcionamiento este apartado")
        # t.chatgpt(conn, especialidad)


## Google Page
elif st.session_state.page == "google":
    especialidad = "google"
    # Init connection
    conn = h.init_connection(especialidad)
    # Init json
    datos = t.get_datos(especialidad)
    # Init user
    user = h.get_user_none()

    st.title("GCP - Google")
    if st.button("Back to Main", key="back-to-main-from-google"):
        go_to_main()
        st.rerun()

    PAGES.remove("Parreitor-3000 🤖")
    # Add a way to navigate within the dbt page
    current_page = st.selectbox("Choose section:", PAGES, key="current_google_page")

    # Update the session state for the current page in dbt
    st.session_state["current_page"] = current_page

    # Execute the function based on the current_page
    if st.session_state["current_page"] == "Intro 🔰":
        t.comienzo(conn, especialidad)
    elif st.session_state["current_page"] == "Practicar 🥊":
        try:
            t.practicar(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error 6: " + str(e.args))
    elif st.session_state["current_page"] == "Exámenes 📄":
        try:
            t.examen(conn, datos, especialidad)
        except Exception as e:
            st.warning("Error 7: " + str(e.args))
    elif st.session_state["current_page"] == "Progreso 📈":
        t.progreso(conn, datos, especialidad)
    elif st.session_state["current_page"] == "Chatgpt":
        st.title("No está en funcionamiento este apartado")
        # t.chatgpt(conn, especialidad)

## SQL Page
elif st.session_state.page == "sql":
    especialidad = "sql"
    # Init connection
    engine = h.init_connection(especialidad)

    ################################################################################
    # Create the title of the website
    st.title(":bar_chart: SQL Query Comparison Tool :slot_machine:")
    # ----------------------------------------
    if st.button("Back to Main", key="back-to-main-from-dbt"):
        go_to_main()
        st.rerun()

    username = t.menu(engine, especialidad)

    query_temp = ""
    if "input_list" not in st.session_state:
        st.session_state["input_list"] = []
    if "counter" not in st.session_state:
        st.session_state["counter"] = 0
    if "show" not in st.session_state:
        st.session_state["show"] = 0
    option_w = "Caso_0"
    option = "Caso 0"
    error = ""
    # SELECT consult from user
    try:
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

        # When exercise is select:
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
        st.error(str(e.args))
