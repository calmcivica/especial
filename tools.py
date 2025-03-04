import helper_functions as hf
import time
import logging
import streamlit as st
import helper as h
import constantes as c
import ast
import random
import plotly.graph_objects as go
from agent import chat
import plotly.express as px
import pandas as pd
import os
import json_and_excels_admin as jtc
from openai import OpenAI
import gamification as gamify
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Constants
RUTA = os.path.join(os.path.dirname(__file__), "jsons")

def get_datos(especialidad):
    """
    Get data from a JSON file based on the specialization.
    
    Args:
        especialidad (str): The specialization type
        
    Returns:
        List[Dict]: The data loaded from the JSON file
    """
    try:
        if especialidad == "snowflake_pro":
            archivo = os.path.join(RUTA, "snowflake_pro_examtopics.json")
        elif especialidad == "snowflake_arch":
            archivo = os.path.join(RUTA, "snowflake_arch_examtopics.json")
        elif especialidad == "dbt":
            archivo = os.path.join(RUTA, "dbt_examtopics.json")
        elif especialidad == "google":
            archivo = os.path.join(RUTA, "google_examtopics.json")
        else:
            raise ValueError(f"Unsupported specialization: {especialidad}")
            
        datos = h.open_file(archivo)
        return datos
    except Exception as e:
        logger.error(f"Error getting data for {especialidad}: {str(e)}", exc_info=True)
        st.warning(f"Ha habido un error, no encuentro los json: {str(e)}")
        return []

def init_users(conn, es_sql=False):
    """
    Initialize users in the session state.
    
    Args:
        conn: Database connection
        es_sql (bool): Whether this is for SQL specialization
    """
    h.get_user_none()
    if "lista_plana" not in st.session_state:
        st.session_state["lista_plana"] = h.recharge_user_list(conn, es_sql)

def menu(conn, especialidad):
    """
    Display the user menu for selection and user management.
    
    Args:
        conn: Database connection
        especialidad (str): The specialization type
        
    Returns:
        str: The selected username
    """
    es_sql = (especialidad == "sql")
    
    # User information container
    with st.container():
        init_users(conn, es_sql)
        space, login, actions = st.columns([3, 1, 1], gap="large")
        space, login, actions = st.columns([2, 2, 0.5], gap="medium")

        with space:
            try:
                if st.session_state.get("user") is None:
                    st.info(
                        "Recuerda elegir tu usuario si quieres que se registren tus avances y poder ver tus progresos."
                    )
                else:
                    if not es_sql:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT rango FROM [esnowflake].[dbo].Dim_Users WHERE name = ?",
                            (st.session_state['user'],)
                        )
                        rango_v = cursor.fetchall()
                        if rango_v:
                            rango = rango_v[0][0]
                            emoji_map = {
                                "Iniciado": "🤓",
                                "Padawan": "🤠",
                                "Maestro": "🗡️",
                                "Parra": "🤖",
                            }
                            emoji = emoji_map.get(rango, "")
                            st.write(f"Rango: {rango} {emoji}")
                        else:
                            st.error("User rank not found.")
            except Exception as e:
                logger.error(f"Error displaying user info: {str(e)}", exc_info=True)
                st.error(f"Error: {str(e)}")

        with login:
            try:
                # Update user list if needed
                if st.session_state.get("user") not in st.session_state.get("lista_plana", []):
                    st.session_state["lista_plana"] = h.recharge_user_list(conn, es_sql)
                
                # Find index of current user
                indice = None
                if st.session_state.get("user") in st.session_state.get("lista_plana", []):
                    indice = st.session_state["lista_plana"].index(st.session_state["user"])
                
                # User selection dropdown
                useri = st.selectbox(
                    "User name:", 
                    st.session_state.get("lista_plana", []), 
                    index=indice
                )
                st.session_state["user"] = useri
                
                # New user creation
                if st.session_state.get("user") is None:
                    new_user = st.text_input("Or enter a new username:")
                    if new_user:
                        if new_user not in st.session_state.get("lista_plana", []):
                            if st.button("Add new user"):
                                hf.new_user(conn, new_user, "message", es_sql)
                                useri = st.session_state["user"]
                        else:
                            st.error("Username already exists.")
            except Exception as e:
                logger.error(f"Error in user dropdown: {str(e)}", exc_info=True)
                st.error(f"Error: {str(e)}")

        with actions:
            try:
                # Initialize counters if needed
                if ("count_reset" not in st.session_state or 
                    st.session_state["count_reset"] >= 2):
                    st.session_state["count_reset"] = 0
                if ("count_delete" not in st.session_state or 
                    st.session_state["count_delete"] >= 2):
                    st.session_state["count_delete"] = 0

                if st.session_state.get("user"):
                    # Reset user button
                    reset_clicked = st.button("Reset user")
                    if reset_clicked:
                        st.session_state["count_reset"] += 1
                        st.write(
                            ":red[Are you sure? Click again if you want to reset your user]"
                        )
                        if st.session_state["count_reset"] >= 2:
                            hf.reset_delete_user(conn, useri, False, es_sql)
                            useri = st.session_state["user"]
                            st.success(f"User {useri} reset successfully.")
                            st.session_state["count_reset"] = 0
                            time.sleep(1)
                            st.rerun()

                    # Delete user button
                    delete_clicked = st.button("Delete user")
                    if delete_clicked:
                        st.session_state["count_delete"] += 1
                        st.write(
                            ":red[Are you sure? Click again if you want to delete your user]"
                        )
                        if st.session_state["count_delete"] >= 2:
                            hf.reset_delete_user(conn, useri, True, es_sql)
                            useri = None
                            time.sleep(1)
                            st.rerun()
            except Exception as e:
                logger.error(f"Error with user actions: {str(e)}", exc_info=True)
                st.error(f"Error: {str(e)}")
                
    return useri

def comienzo(conn, especialidad):
    """
    Display the introduction page for a specialization.
    
    Args:
        conn: Database connection
        especialidad (str): The specialization type
    """
    try:
        h.get_user_none()
        
        # Get introduction info based on specialization
        info = ""
        if especialidad == "snowflake_pro":
            info = c.COMIENZO_SNOWFLAKE_PRO + c.INFO_EXAMEN_SNOWFLAKE_PRO
        elif especialidad == "snowflake_arch":
            info = c.COMIENZO_SNOWFLAKE_ARCH + c.INFO_EXAMEN_SNOWFLAKE_ARCH
        elif especialidad == "dbt":
            info = c.COMIENZO_DBT + c.INFO_EXAMEN_DBT
        elif especialidad == "google":
            info = c.COMIENZO_GOOGLE + c.INFO_EXAMEN_GOOGLE
            
        # Display user menu and info
        menu(conn, especialidad)
        st.markdown(info)
    except Exception as e:
        logger.error(f"Error in introduction page: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")

def practicar(conn, datos, especialidad):
    """
    Display the practice page for a specialization.
    
    Args:
        conn: Database connection
        datos (List[Dict]): The questions and answers
        especialidad (str): The specialization type
    """
    try:
        # Get user and display menu
        user = h.get_user_none()
        menu(conn, especialidad)
        
        # Initialize session state
        st.session_state["button_order_aleatorio"] = False
        if "exam_mode" not in st.session_state:
            st.session_state["exam_mode"] = ""
            
        # Display usage information
        with st.expander("¿Cómo podría usar esta sección? 🤔"):
            st.markdown(getattr(c, f"USO_SECCION_{especialidad.upper()}"))
            
        # Excel download option
        if user is not None:
            with st.expander("¿Quieres descargar un excel de las preguntas?"):
                # Generate Excel file and register download
                csv_buffer, nombre_fichero, numero_aleatorio = jtc.download_excel(especialidad)
                
                # Warning message
                st.warning("Se quedará registrado cuándo se generó este excel. Recuerda que no se puede compartir la información, puesto que es propiedad de Cívica.")
                
                # Download button
                st.download_button(
                    label="Download excel",
                    data=csv_buffer,
                    file_name=nombre_fichero,
                    on_click=lambda: jtc.insert_download_db(user, numero_aleatorio, especialidad),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # Filters and questions columns
        filtros, preguntas = st.columns([1, 3], gap="large")
        
        # Filters section
        with filtros:
            st.subheader("Filtros")
            
            # Question range slider
            values = st.slider(
                "Seleccione rango de preguntas en el que practicar",
                0,
                len(datos),
                (0, len(datos)),
                step=1,
            )

            # Section selection
            secciones = st.multiselect(
                "¿Qué secciones quieres tocar?",
                getattr(c, f"SECCIONES_{especialidad.upper()}"),
            )

            # Other filters
            option = st.multiselect(
                "Otros filtros",
                ["Todas", "Sin hacer", "Falladas en exámenes", "Falladas en práctica"],
            )

            # Apply range filter
            preguntas_filtradas = [
                item for item in datos if values[0] <= item["question_number"] <= values[1]
            ]
            
            # Apply section filter
            if "Todas" not in secciones and secciones:
                preguntas_filtradas = [
                    item
                    for item in preguntas_filtradas
                    if any(area in secciones for area in item["question_area"])
                ]

            # Get question history
            if user:
                cursor = conn.cursor()
                cursor.execute(
                    "EXEC GetQuestionHistory @user=?",
                    (user,)
                )
                aux_opcion = cursor.fetchall()

                no_hechas = []
                opcion_examen_falsas = []
                opcion_practicas_falsas = []

                # Process filter options
                if "Falladas en exámenes" in option and aux_opcion[0][1]:
                    opcion_examen_falsas = list(ast.literal_eval(aux_opcion[0][1]))

                if "Falladas en práctica" in option and aux_opcion[0][2]:
                    opcion_practicas_falsas = list(ast.literal_eval(aux_opcion[0][2]))

                if "Sin hacer" in option:
                    hechas = aux_opcion[0][0]
                    if hechas:
                        hechas_lista = ast.literal_eval(hechas)
                        hechas_int = [int(num) for num in list(hechas_lista)]
                        no_hechas = [
                            item["question_number"]
                            for item in preguntas_filtradas
                            if item["question_number"] not in hechas_int
                        ]

                # Combine filter options
                opcion_final = list(
                    set(no_hechas + opcion_examen_falsas + opcion_practicas_falsas)
                )

                # Apply combined filter if not "All"
                if "Todas" not in option and option:
                    preguntas_filtradas = [
                        item
                        for item in preguntas_filtradas
                        if item["question_number"] in opcion_final
                    ]

            # Get question numbers
            question_set = [item["question_number"] for item in preguntas_filtradas]

            # Initialize session state for question set
            if "question_set" not in st.session_state:
                st.session_state["question_set"] = question_set

            # Update question ordering
            h.orden_preguntas(question_set)
            
        # Questions section
        with preguntas:
            if st.session_state["question_set"]:
                h.setexam(
                    st.session_state["question_set"],
                    datos,
                    "practicar",
                    conn,
                    user,
                    especialidad,
                )
            else:
                st.write(
                    "No hay ninguna pregunta que cuadre con los filtros que has puesto"
                )
    except Exception as e:
        logger.error(f"Error in practice page: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def examen(conn, datos, especialidad):
    """
    Display the exam page for a specialization.
    
    Args:
        conn: Database connection
        datos (List[Dict]): The questions and answers
        especialidad (str): The specialization type
    """
    try:
        # Get user
        user = h.get_user_none()
        
        # Initialize exam mode
        exam_mode = 0
        if "exam_mode" not in st.session_state or st.session_state["exam_mode"] == "":
            st.session_state["exam_mode"] = exam_mode
            
        question_set = []

        # Initialize question set
        if "question_set" not in st.session_state:
            st.session_state["question_set"] = question_set

        # Exam setup mode
        if st.session_state.get("exam_mode", 0) == 0:
            with st.container():
                # Display user menu
                menu(conn, especialidad)
                
                st.title("Examen")
                st.write("Empieza ajustando los filtros y luego las opciones")
                
                with st.container():
                    filtros_col, settings_col = st.columns(2, gap="large")
                    
                    # Filters section
                    with filtros_col:
                        preguntas_filtradas = h.filtros(
                            especialidad, datos, conn, user, True
                        )
                        
                    # Settings section
                    with settings_col:
                        num_questions, exam_duration = h.exam_settings(preguntas_filtradas)
                        
                    # Exam info expander
                    with st.expander("¿Como es el examen real?"):
                        if especialidad == "snowflake_pro":
                            info = c.INFO_EXAMEN_SNOWFLAKE_PRO
                        elif especialidad == "snowflake_arch":
                            info = c.INFO_EXAMEN_SNOWFLAKE_ARCH
                        elif especialidad == "dbt":
                            info = c.INFO_EXAMEN_DBT
                        elif especialidad == "google":
                            info = c.INFO_EXAMEN_GOOGLE
                        st.markdown(info)
                        
                # Start exam button
                with st.container():
                    _, boton, _ = st.columns(3, gap="large")
                    if num_questions == 0:
                        st.warning(
                            "Tus filtros u opciones resultan en una cantidad de 0 preguntas"
                        )
                    else:
                        with boton:
                            st.button(
                                "Comenzar examen",
                                use_container_width=True,
                                on_click=h.aux_exam,
                                args=("empezar", exam_duration, None),
                            )
        
        # Exam taking mode
        elif st.session_state.get("exam_mode", 0) == 1:
            with st.container():
                exam_duration = st.session_state["exam_duration"]
                h.setexam(
                    st.session_state["question_set"],
                    datos,
                    "examen",
                    conn,
                    user,
                    especialidad,
                    exam_time=exam_duration,
                )
                
        # Exam results mode
        elif st.session_state.get("exam_mode", 0) == 2:
            try:
                # Get exam info
                exam_duration = st.session_state["exam_duration"]
                
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COALESCE(MAX(id_exam), 1) FROM [esnowflake].[dbo].FACT_EXAMS WHERE user_nickname = ?",
                    (user,)
                )
                exam_id = cursor.fetchone()[0]
                
                # Initialize review set
                st.session_state["review_set"] = []
                
                # Process user answers
                user_answers = st.session_state["exam_answers"]
                latest_answers = {}
                
                # Get latest answer for each question
                for answer in user_answers:
                    question_number = answer["question_number"]
                    timestamp = answer["timestamp"]
                    
                    if (question_number not in latest_answers or
                        timestamp > latest_answers[question_number]["timestamp"]):
                        latest_answers[question_number] = answer
                        
                # Convert to list
                filtered_answers = list(latest_answers.values())
                
                # Build SQL insert
                values_list = []
                preguntas_acertadas = 0
                preguntas_falladas = 0

                for answer in filtered_answers:
                    question_number = answer["question_number"]
                    user_answer = answer["user_answer"]

                    if isinstance(user_answer, str):
                        user_answer = [user_answer]

                    # Get correct answer
                    if question_number <= len(datos):
                        correcta = datos[question_number - 1]["correct_answer"]
                    else:
                        st.warning(f"Question number {question_number} exceeds available questions.")
                        continue
                        
                    question = datos[question_number - 1]["question"]
                    comofue = h.comparar_respuestas(user_answer, correcta)

                    answer["result"] = comofue
                    answer["correcta"] = correcta
                    answer["question"] = question

                    # Set flags based on correctness
                    if answer["result"] == 1:
                        preguntas_acertadas += 1
                        is_correct = 1
                        is_answered = 1
                    elif answer["result"] == 0:
                        preguntas_falladas += 1
                        is_correct = 0
                        is_answered = 1
                    else:
                        is_correct = 0
                        is_answered = 0

                    # Add values for SQL insert
                    values_list.append((
                        question_number, user, 'examen', exam_id, 
                        is_correct, is_answered
                    ))

                # Execute SQL inserts if needed
                try:
                    aux_exam_insert = st.session_state.get("aux_exam_insert", 0)
                    if aux_exam_insert:
                        # Update exam record
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            UPDATE [esnowflake].[dbo].FACT_EXAMS 
                            SET 
                                end_time = CURRENT_TIMESTAMP,
                                number_of_questions = ?,
                                number_of_failed_questions = ?,
                                number_of_correct_questions = ?
                            WHERE id_exam = ?
                            """,
                            (len(filtered_answers)-1, preguntas_falladas, preguntas_acertadas, exam_id)
                        )
                        
                        # Insert answer records
                        if values_list:
                            cursor.executemany(
                                """
                                INSERT INTO [esnowflake].[dbo].Fact_Answers 
                                (question_id, user_nickname, type, exam_id, is_correct, is_answered, ANSWER_TIMESTAMP) 
                                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                                """,
                                values_list
                            )
                        conn.commit()
                        
                    # Reset flag
                    if "aux_exam_insert" in st.session_state:
                        st.session_state["aux_exam_insert"] = 0
                except Exception as e:
                    logger.error(f"Error saving exam results: {str(e)}", exc_info=True)
                    st.write(f"An error occurred while saving results: {str(e)}")
                
                # Get failed questions
                failed = [answer for answer in filtered_answers if answer["result"] == 0]
                
                # Get exam time
                cursor.execute(
                    "SELECT DATEDIFF(SECOND, start_time, end_time) FROM [esnowflake].[dbo].FACT_EXAMS WHERE id_exam = ?",
                    (exam_id,)
                )
                tiempo_v = cursor.fetchone()
                
                tiempo = tiempo_v[0] if tiempo_v else 0
                minutos = tiempo // 60
                segundos = tiempo % 60
                tiempo_formato = f"{minutos} minutos y {segundos} segundos"
                
                # Calculate stats
                preguntas_no_respondidas = (
                    len(filtered_answers) - preguntas_acertadas - preguntas_falladas
                )
                
                # Display results
                result, grafi = st.columns(2, gap="large")
                with result:
                    st.write("")
                    st.write("")
                    per_acierto = preguntas_acertadas / len(filtered_answers) if filtered_answers else 0
                    st.metric("Porcentaje de Aciertos", f"{100*per_acierto:.2f}%")
                    st.metric("Número de preguntas", f"{len(filtered_answers)}")
                    st.metric("Tiempo Total", f"{tiempo_formato}")

                    # Get pass threshold
                    if especialidad == "snowflake_pro":
                        umbral = int(c.UMBRAL_APROBADO_SNOWFLAKE_PRO) / 100
                    elif especialidad == "snowflake_arch":
                        umbral = int(c.UMBRAL_APROBADO_SNOWFLAKE_ARCH) / 100
                    elif especialidad == "dbt":
                        umbral = int(c.UMBRAL_APROBADO_DBT) / 100
                    elif especialidad == "google":
                        umbral = int(c.UMBRAL_APROBADO_GOOGLE) / 100
                    else:
                        st.error("Error, no hay umbral de aprobado para especialidad")
                        umbral = 0.75

                    # Show pass/fail message
                    if per_acierto >= umbral:
                        st.success("¡Grande! Has superado el examen.")
                    else:
                        st.error("Al palo crack, sigue intentándolo. Puedes mejorar.")
                
                # Results chart
                with grafi:
                    # Chart data
                    labels = ["Acertadas", "Falladas", "No Respondidas"]
                    values = [preguntas_acertadas, preguntas_falladas, preguntas_no_respondidas]
                    colors = ["green", "red", "blue"]
                    
                    # Create donut chart
                    fig = go.Figure(
                        data=[
                            go.Pie(labels=labels, values=values, hole=0.5, marker_colors=colors)
                        ]
                    )
                    fig.update_layout(title_text="Resultados")
                    
                    # Display chart
                    st.plotly_chart(fig)
                
                # Failed questions review
                with st.expander("Revisar preguntas falladas"):
                    for answer in failed:
                        st.divider()
                        st.write(answer["question_number"])
                        st.write(answer["question"])
                        st.write("Tu has respondido:")
                        st.write(answer["user_answer"])
                        st.write("La respuesta correcta era:")
                        st.write(answer["correcta"])
                
                # Back to start button
                _, volver, _ = st.columns([2, 1, 2], gap="large")
                with volver:
                    st.button(
                        "Volver al inicio",
                        use_container_width=True,
                        on_click=h.aux_exam,
                        args=("Inicio", None, None),
                    )
            except Exception as e:
                logger.error(f"Error displaying exam results: {str(e)}", exc_info=True)
                st.error(f"Error en los resultados del examen: {str(e)}")
    except Exception as e:
        logger.error(f"Error in exam page: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def progreso(conn, datos, especialidad):
    """
    Display the progress page for a specialization.
    
    Args:
        conn: Database connection
        datos (List[Dict]): The questions and answers
        especialidad (str): The specialization type
    """
    try:
        # Display user menu
        menu(conn, especialidad)
        user = st.session_state["user"]
        
        if user is None:
            st.write("Elige tu usuario para ver tu progreso")
        else:
            # Create tabs for different progress sections
            progress_tab, gamification_tab = st.tabs(["Progreso de Estudio", "Gamificación"])
            
            with progress_tab:
                st.subheader("Avance por secciones")
            
            # Get question history
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    question_id, is_correct, is_answered, 
                    CAST(answer_timestamp AS date) AS Fecha 
                FROM [esnowflake].[dbo].FACT_ANSWERS 
                WHERE user_nickname = ? 
                ORDER BY answer_timestamp DESC
                """,
                (user,)
            )
            questions_info = cursor.fetchall()
            
            # Convert to DataFrame
            df = pd.DataFrame(
                questions_info, 
                columns=["question_id", "is_correct", "is_answered", "Fecha"]
            )
            
            # Convert date column to datetime
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.normalize()
            
            if len(df) == 0:
                st.warning("Haz al menos una pregunta para poder ver esta sección")
            else:
                # Prepare area data
                # Get question areas
                df_preguntas = pd.DataFrame(datos)
                
                # Handle multiple question areas by exploding them into separate rows
                df_preguntas = df_preguntas.explode("question_area")
                
                # Merge with answer data
                df_combinado = df.merge(
                    df_preguntas[["question_number", "question_area"]],
                    left_on="question_id",
                    right_on="question_number",
                    how="left"
                )
                
                # Get unique areas
                df_secciones_referencia = pd.DataFrame(
                    df_preguntas["question_area"].unique(), 
                    columns=["question_area"]
                )
                
                # Calculate metrics per area
                total_preguntas_por_seccion = df_preguntas["question_area"].value_counts()
                metrics_por_seccion = df_combinado.groupby("question_area")["is_correct"].agg(
                    ["sum", lambda x: len(x) - x.sum()]
                )
                metrics_por_seccion.columns = ["preguntas Correctas", "preguntas Incorrectas"]
                
                # Merge metrics
                metrics_final = df_secciones_referencia.merge(
                    metrics_por_seccion,
                    on="question_area",
                    how="left"
                ).fillna(0)
                
                # Calculate unseen questions
                metrics_final["preguntas No Vistas"] = (
                    metrics_final["question_area"].map(total_preguntas_por_seccion)
                    - metrics_final["preguntas Correctas"]
                    - metrics_final["preguntas Incorrectas"]
                )
                
                # Define colors
                colors = ["green", "red", "blue"]
                
                # Display charts
                c1, c2, c3, c4, c5, c6 = st.columns(6, gap="small")
                columns = [c1, c2, c3, c4, c5, c6]
                
                # Display one chart per area
                for i, (_, row) in enumerate(metrics_final.iterrows()):
                    col_index = i % len(columns)
                    
                    labels = [
                        "preguntas Correctas",
                        "preguntas Incorrectas",
                        "preguntas No Vistas"
                    ]
                    values = [
                        row["preguntas Correctas"],
                        row["preguntas Incorrectas"],
                        row["preguntas No Vistas"]
                    ]
                    
                    # Create donut chart
                    fig = go.Figure(
                        data=[
                            go.Pie(
                                labels=labels, 
                                values=values, 
                                hole=0.5, 
                                marker_colors=colors
                            )
                        ]
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title_text=f"{row['question_area']}",
                        showlegend=False,
                        height=350,
                        width=350,
                        margin=dict(l=10, r=10, t=30, b=10)
                    )
                    
                    # Display in appropriate column
                    with columns[col_index]:
                        st.plotly_chart(fig, use_container_width=True)
                
                # Display overall stats and timeline
                st.subheader("Estudio total")
                
                secciones, exams = st.columns([2, 1], gap="large")
                with secciones:
                    # Prepare data
                    df_resumen = (
                        df.groupby("Fecha")
                        .size()
                        .reset_index(name="Número de preguntas")
                    )
                    
                    # Calculate streak
                    racha_actual = 0
                    fecha_anterior = None
                    dates = sorted(df_resumen["Fecha"].unique(), reverse=True)
                    
                    for fecha in dates:
                        if (fecha_anterior is None or 
                            fecha_anterior - pd.Timedelta(days=1) == fecha):
                            racha_actual += 1
                            fecha_anterior = fecha
                        else:
                            break
                    
                    # Calculate overall stats
                    total_preguntas = len(df)
                    total_correctas = df["is_correct"].sum()
                    porcentaje_acierto = (total_correctas / total_preguntas) * 100 if total_preguntas > 0 else 0
                    
                    # Display metrics and timeline
                    metricas, timeline = st.columns([1, 2], gap="small")
                    
                    with metricas:
                        st.subheader("Estudio total")
                        st.write("")
                        st.metric("Racha actual de días de estudio:", racha_actual)
                        st.metric("Total de preguntas realizadas", total_preguntas)
                        st.metric("Porcentaje de acierto", f"{porcentaje_acierto:.2f}%")
                    
                    with timeline:
                        # Create bar chart
                        fig = px.bar(
                            df_resumen,
                            x="Fecha",
                            y="Número de preguntas",
                            title="preguntas Respondidas por Día"
                        )
                        
                        # Format x-axis
                        fig.update_xaxes(
                            dtick="D1",
                            tickformat="%b %d, %Y"
                        )
                        
                        # Display chart
                        st.plotly_chart(fig, use_container_width=True)
                
                # Display exam history
                with exams:
                    st.subheader("Historial de exámenes")
                    
                    # Get exam data
                    cursor.execute(
                        """
                        SELECT TOP 6 
                            id_exam, start_time, duration_minutes,
                            number_of_questions, number_of_correct_questions,
                            number_of_failed_questions
                        FROM [esnowflake].[dbo].FACT_EXAMS
                        WHERE user_nickname = ?
                        ORDER BY start_time DESC
                        """,
                        (user,)
                    )
                    exam_info = cursor.fetchall()
                    
                    # Convert to DataFrame
                    df_exams = pd.DataFrame(
                        exam_info,
                        columns=[
                            "id_exam", "start_time", "duration_minutes",
                            "number_of_questions", "number_of_correct_questions",
                            "number_of_failed_questions"
                        ]
                    )
                    
                    # Handle null values
                    for col in ["number_of_questions", "number_of_correct_questions", "number_of_failed_questions"]:
                        df_exams[col] = df_exams[col].fillna(0).astype(int)
                    
                    # Colors for chart
                    colores = ["green", "red", "blue"]
                    
                    # Chart dimensions
                    ancho, alto = 350, 350
                    
                    if len(df_exams) == 0:
                        st.write("Aún no has hecho exámenes")
                    else:
                        # Display each exam
                        for _, examen in df_exams.iterrows():
                            # Calculate unanswered questions
                            num_questions = examen["number_of_questions"] or 0
                            en_blanco = (
                                examen["number_of_questions"]
                                - (examen["number_of_correct_questions"] or 0)
                                - (examen["number_of_failed_questions"] or 0)
                            )
                            
                            # Create pie chart
                            fig = go.Figure(
                                go.Pie(
                                    labels=["Acertadas", "Falladas", "En Blanco"],
                                    values=[
                                        examen["number_of_correct_questions"],
                                        examen["number_of_failed_questions"],
                                        en_blanco,
                                    ],
                                    marker_colors=colores,
                                    hole=0.4,
                                )
                            )
                            fig.update_traces(textinfo="percent+label")
                            fig.update_layout(width=ancho, height=alto)
                            
                            # Calculate score and pass/fail
                            score = (
                                examen["number_of_correct_questions"] / examen["number_of_questions"]
                                if examen["number_of_questions"] > 0 else 0
                            )
                            
                            # Format timestamp
                            timestamp = (
                                pd.to_datetime(examen["start_time"]).strftime("%Y-%m-%d %H:%M")
                                if pd.notnull(examen["start_time"]) else "Desconocido"
                            )
                            
                            # Create message
                            mensaje = f"{'APROBADO' if score >= 0.75 else 'SUSPENSO'} {100*score:.2f}%     -----{'🟢' if score >= 0.75 else '🔴'}-----      {timestamp}"
                            
                            # Display in expander
                            with st.expander(mensaje):
                                grap, met = st.columns([2, 1], gap="medium")
                                with grap:
                                    st.plotly_chart(fig)
                                with met:
                                    st.write("")
                                    st.write("")
                                    st.metric("Porcentaje de Aciertos", f"{100*score:.2f}%")
                                    st.metric("Número de preguntas", num_questions)
                                    st.metric(
                                        "Tiempo Total", f"{examen['duration_minutes']} minutos"
                                    )
                                    if score >= 0.75:
                                        st.success("APROBADO")
                                    else:
                                        st.error("SUSPENSO")
            
            # Display gamification tab content
            with gamification_tab:
                # Display gamification features
                is_sql = (especialidad == "sql")
                gamify.gamification_tab(conn, user, is_sql)
    except Exception as e:
        logger.error(f"Error in progress page: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")

def parreitor(conn, especialidad):
    """
    Display the AI assistant page.
    
    Args:
        conn: Database connection
        especialidad (str): The specialization type
    """
    try:
        # Display user menu
        menu(conn, especialidad)
        
        st.title("Parreitor-3000")
        
        # Initialize message history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Display message history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Chat input
        if prompt := st.chat_input(f"Alguna duda de la especialidad de {especialidad}?"):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            try:
                # Get response from assistant
                response = chat(prompt)
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(response)
                
                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
                with st.chat_message("assistant"):
                    st.error("Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, inténtalo de nuevo.")
    except Exception as e:
        logger.error(f"Error in Parreitor page: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")

def chatgpt(conn, especialidad):
    """
    Display the ChatGPT integration page.
    
    Args:
        conn: Database connection
        especialidad (str): The specialization type
    """
    try:
        st.title("ChatGPT-like clone")
        
        # Initialize OpenAI client with API key
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Set model
        if "openai_model" not in st.session_state:
            st.session_state["openai_model"] = "gpt-3.5-turbo"
            
        # Initialize message history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Display message history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Chat input
        if prompt := st.chat_input("What is up?"):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                try:
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                    
                    # Add assistant response to history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    logger.error(f"Error with OpenAI API: {str(e)}", exc_info=True)
                    st.error("Error connecting to OpenAI API. Please check your API key.")
    except Exception as e:
        logger.error(f"Error in ChatGPT page: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")