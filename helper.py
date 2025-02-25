import os
import random
import json
import streamlit as st
import uuid
import time
import threading
import datetime
import pyodbc
import ast
import logging
import constantes as c
from pathlib import Path
from sqlalchemy import create_engine, text
from docx import Document
from typing import List, Dict, Any, Tuple, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

@st.cache_resource
def init_connection(especialidad):
    """
    Initialize database connection based on the specialization type.
    
    Args:
        especialidad (str): The type of specialization (snowflake_pro, snowflake_arch, dbt, google, sql)
        
    Returns:
        Connection object: Either a pyodbc connection or SQLAlchemy engine
        
    Raises:
        Exception: If there's an error initializing the connection
    """
    try:
        if especialidad in ['snowflake_pro', 'snowflake_arch', 'dbt', 'google']:
            tipo = 'especialidades'
            return pyodbc.connect(
                "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
                + st.secrets["server"]
                + ";DATABASE="
                + st.secrets[f"database_{tipo}"]
                + ";UID="
                + st.secrets[f"username_{tipo}"]
                + ";PWD="
                + st.secrets[f"password_{tipo}"]
            )
        elif especialidad == 'sql':
            tipo = 'sql'
            connection_str = (
                "mssql+pyodbc://"
                + st.secrets[f"username_{tipo}"]
                + ":"
                + st.secrets[f"password_{tipo}"]
                + "@"
                + st.secrets["server"]
                + "/"
                + st.secrets[f"database_{tipo}"]
                + "?driver=ODBC+Driver+17+for+SQL+Server"
            )
            return create_engine(connection_str, pool_size=50, max_overflow=100)
        else:
            raise Exception(f"Unsupported specialization type: {especialidad}")
    except Exception as e:
        logger.error(f"Error initializing connection for {especialidad}: {str(e)}", exc_info=True)
        raise Exception(f"Error initializing connection: {str(e)}")

def open_file(json_file):
    """
    Open and load a JSON file.
    
    Args:
        json_file (str): Path to the JSON file
        
    Returns:
        dict: The loaded JSON data
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
        return datos
    except Exception as e:
        logger.error(f"Error opening file {json_file}: {str(e)}", exc_info=True)
        st.error(f"Error loading data: {str(e)}")
        return []

def get_session_state(key, default_value=None):
    """
    Get a value from session state, initializing it if it doesn't exist.
    
    Args:
        key (str): The session state key
        default_value: The default value if the key doesn't exist
        
    Returns:
        The value from session state
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]

def set_session_state(key, value):
    """
    Set a value in session state.
    
    Args:
        key (str): The session state key
        value: The value to set
    """
    st.session_state[key] = value

def get_user_none():
    """
    Get the current user from session state or None if not set.
    
    Returns:
        str or None: The current user
    """
    return get_session_state('user', None)

def recharge_user_list(conn, es_sql=False):
    """
    Get the list of users from the database.
    
    Args:
        conn: Database connection
        es_sql (bool): Whether this is for SQL specialization
        
    Returns:
        List[str]: List of usernames
    """
    try:
        if es_sql:
            with conn.begin() as connection:
                query = "SELECT username FROM [dbo].Dim_Users ORDER BY username"
                result = connection.execute(text(query))
                lista_plana = [row[0] for row in result.fetchall()]
        else:
            query = "SELECT name FROM [esnowflake].[dbo].Dim_Users ORDER BY name"
            user_list_v = conn.cursor().execute(query).fetchall()
            lista_plana = [item[0] for item in user_list_v]
        
        return lista_plana
    except Exception as e:
        logger.error(f"Error recharging user list: {str(e)}", exc_info=True)
        return []

def new_user(conn, new_user, message=None, es_sql=False):
    """
    Add a new user to the database.
    
    Args:
        conn: Database connection
        new_user (str): Username to add
        message (str, optional): Message to display
        es_sql (bool): Whether this is for SQL specialization
    """
    try:
        if es_sql:
            # For SQLAlchemy connection
            with conn.begin() as connection:
                connection.execute(
                    text("INSERT INTO [dbo].Dim_Users (username) VALUES (:username)"),
                    {'username': new_user}
                )
        else:
            # For pyodbc connection
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO [esnowflake].[dbo].Dim_Users (name, rango) VALUES (?, ?)",
                (new_user, 'Iniciado')
            )
            conn.commit()

        if message:
            st.success('New user added successfully!')
        
        set_session_state("user", new_user)
        set_session_state("lista_plana", recharge_user_list(conn, es_sql))
        
        time.sleep(1)
        st.rerun()
    except Exception as e:
        logger.error(f"Error adding new user: {str(e)}", exc_info=True)
        st.error(f'Error adding new user: {str(e)}')

def reset_delete_user(conn, useri, delete, es_sql=False):
    """
    Reset or delete a user from the database.
    
    Args:
        conn: Database connection
        useri (str): Username to reset or delete
        delete (bool): Whether to delete the user (True) or reset (False)
        es_sql (bool): Whether this is for SQL specialization
    """
    action = 'delete' if delete else 'reset'
    
    try:
        if es_sql:
            # For SQLAlchemy connection
            with conn.begin() as connection:
                connection.execute(
                    text("DELETE FROM [dbo].Dim_Users WHERE username = :username"),
                    {'username': useri}
                )
                connection.execute(
                    text("DELETE FROM [dbo].Fact_Answers WHERE username = :username"),
                    {'username': useri}
                )
        else:
            # For pyodbc connection
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM [esnowflake].[dbo].Dim_Users WHERE name = ?",
                (useri,)
            )
            cursor.execute(
                "DELETE FROM [esnowflake].[dbo].FACT_ANSWERS WHERE user_nickname = ?",
                (useri,)
            )
            cursor.execute(
                "DELETE FROM [esnowflake].[dbo].FACT_EXAMS WHERE user_nickname = ?",
                (useri,)
            )
            conn.commit()
        
        st.success("Action completed!")

        set_session_state("lista_plana", recharge_user_list(conn, es_sql))
        if delete:
            set_session_state("user", None)
        else:
            new_user(conn, useri, es_sql=es_sql)
        
        set_session_state("count_reset", 0)
        set_session_state("count_delete", 0)
        time.sleep(1)
        st.rerun()
    except Exception as e:
        logger.error(f"Error {action}ing user: {str(e)}", exc_info=True)
        st.error(f'Error {action}ing user: {str(e)}')

def process_qa_block(qa_block):
    """
    Process a question-answer block from a docx file.
    
    Args:
        qa_block (List[str]): Lines of text from the docx file
        
    Returns:
        dict: The processed question and answers
    """
    # Remove empty lines
    qa_block = [line for line in qa_block if line]

    # First line after 'Question #...' is the question
    # Remaining lines are the answers
    question = qa_block[1]
    answers = qa_block[2:]

    return {"question": question, "answers": answers}

def extract_questions_and_answers(docx_file_path):
    """
    Extract questions and answers from a docx file.
    
    Args:
        docx_file_path (str): Path to the docx file
        
    Returns:
        List[dict]: List of questions and answers
    """
    try:
        doc = Document(docx_file_path)
        questions_with_answers = []
        current_qa = []
        capture = False

        for para in doc.paragraphs:
            text = para.text.strip()
            if text.startswith("Question #"):
                if current_qa:
                    # Process the current question block
                    processed_qa = process_qa_block(current_qa)
                    questions_with_answers.append(processed_qa)
                    current_qa = []
                capture = True
            elif "Correct Answer:" in text:
                capture = False
            if capture and text:
                current_qa.append(text)
                
        if current_qa:
            processed_qa = process_qa_block(current_qa)
            questions_with_answers.append(processed_qa)

        return questions_with_answers
    except Exception as e:
        logger.error(f"Error extracting Q&A from {docx_file_path}: {str(e)}", exc_info=True)
        return []

def checkbox_help(unique_key):
    """
    Toggle a checkbox state in session state.
    
    Args:
        unique_key (str): The session state key for the checkbox
    """
    if get_session_state(unique_key, 0) == 0:
        set_session_state(unique_key, 1)
    else:
        set_session_state(unique_key, 0)

def reset_counter():
    """Reset the counter in session state."""
    set_session_state("counter", 0)

def increment_counter():
    """Increment the counter in session state."""
    set_session_state("counter", get_session_state("counter", 0) + 1)

def pregunta(jason, n, mode, user, conn, especialidad):
    """
    Display a question and handle user responses.
    
    Args:
        jason (List[dict]): List of questions and answers
        n (int): Question number
        mode (str): Mode ('practicar' or 'examen')
        user (str): Username
        conn: Database connection
        especialidad (str): Specialization type
    """
    try:
        if 'order' not in st.session_state:
            st.session_state["order"] = True

        # Get the question data
        if st.session_state["order"]:
            json_question = jason[n-1]
        else:
            if 'seen_questions' not in st.session_state:
                st.session_state['seen_questions'] = []

            # Filter out questions already seen
            available_questions = [q for q in jason if q["question_number"] not in st.session_state['seen_questions']]

            if not available_questions:
                st.error("No more questions available.")
                return

            # Randomly select a new question from those not seen
            json_question = random.choice(available_questions)
            st.session_state['seen_questions'].append(json_question["question_number"])
            
        numero = json_question["question_number"]
        pregunta = json_question["question"]
        respuestas = json_question["answers"]
        question_area = json_question["question_area"]   

        # Ensure answers are randomized only once per question
        unique_answer_key = f"randomized_answers_{numero}"
        if unique_answer_key not in st.session_state:
            random.shuffle(respuestas)
            st.session_state[unique_answer_key] = respuestas.copy()
        else:
            respuestas = st.session_state[unique_answer_key]
            
        # Display question number info
        numero_info = st.session_state['question_number_internal']+1
        num_question_set = len(st.session_state["question_set"])
        st.info(f'Pregunta {str(numero_info)} de {str(num_question_set)}.')
        st.write(f'Pregunta {numero} de ExamTopics')
        
        # Display question area
        if isinstance(question_area, str):
            question_area = [question_area]  # Convert to a list if it's a single string

        if question_area:  # Check if the list is not empty
            areas = ', '.join(question_area)  # Join all elements of the list into a single string separated by commas
            st.write(f":orange[Question area:] {areas}")
        else:
            st.write(":orange[No question area specified]")

        # Show extra information if available
        if "question_extra_info" in json_question and json_question["question_extra_info"]:
            with st.expander(" 🔽 Información extra del caso:"):
                st.markdown(json_question["question_extra_info"])
        
        # Display the question
        st.markdown(pregunta)
        
        # Show image if available
        imagen = f'./static/{especialidad}/{str(numero)}.png'
        if os.path.exists(imagen):
            st.image(imagen)

        # Initialize user response array
        response_key = f"user_respuestas_{numero}"
        if response_key not in st.session_state:
            st.session_state[response_key] = [False] * len(respuestas)

        # Display answer checkboxes
        for i, respuesta in enumerate(respuestas):
            unique_key = f"{numero}.{i}"
            user_response = st.checkbox(f'{respuesta}', value=st.session_state[response_key][i], key=unique_key)
            st.session_state[response_key][i] = user_response

        # Process user responses
        user_respuestas = st.session_state[response_key]
        user_answer = [resp for resp, checked in zip(respuestas, user_respuestas) if checked]
        
        # Check if the answer is correct
        is_correct = sol(especialidad, jason, n, user_answer, 1) if user_answer else False
        is_answered = bool(user_answer)
        
        # Handle solution display
        with st.container():
            if mode == "practicar":
                s = 'show_solution'
                if 'show_solution' not in st.session_state:
                    st.session_state['show_solution'] = 0

                with st.container():
                    # Button to show the solution
                    is_correct = sol(especialidad, jason, n, user_answer, 1)
                    is_answered = 0
                    if user_answer:
                        is_answered = 1
                    st.button('Ver solución', key=uuid.uuid4(), on_click=checkbox_help, args=(s,))

                    if st.session_state['show_solution'] == 1:
                        try:
                            is_correct_int = 1 if is_correct else 0
                            is_answered_int = 1 if is_answered else 0
                            
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO [esnowflake].[dbo].Fact_Answers (question_id, user_nickname, type, exam_id, is_correct, is_answered, ANSWER_TIMESTAMP) VALUES (?, ?, ?, NULL, ?, ?, CURRENT_TIMESTAMP)",
                                (n, user, mode, is_correct_int, is_answered_int)
                            )
                            conn.commit()
                        except Exception as e:
                            logger.error(f"Error recording answer: {str(e)}", exc_info=True)

                    # Show the solution if requested
                    if st.session_state['show_solution']:
                        sol(especialidad, jason, n, user_answer)

            elif mode == 'examen':
                # Record answer for exam mode
                jsoni = {
                    "question_number": numero,
                    "user_answer": user_answer,
                    "timestamp": datetime.datetime.now()
                }
                st.session_state['exam_answers'].append(jsoni)
    except Exception as e:
        logger.error(f"Error displaying question: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def sol(especialidad, jason, n, user_answer, getsol=False):
    """
    Display the solution for a question or check if the answer is correct.
    
    Args:
        especialidad (str): Specialization type
        jason (List[dict]): List of questions and answers
        n (int): Question number
        user_answer (List[str]): User's answers
        getsol (bool): Whether to just get the correctness (True) or display the solution (False)
        
    Returns:
        bool or None: Whether the answer is correct (if getsol is True)
    """
    try:
        json_question = jason[n-1]
        
        # Extract the required data from the JSON
        correcta = json_question["correct_answer"]
        explanation = json_question["explanation"]
        referencias = json_question["reference"]
        numero = json_question["question_number"]
        
        if type(user_answer) == str:
            user_answer = [user_answer]
            
        comofue = comparar_respuestas(user_answer, correcta) 
        
        if getsol == True:
            if comofue is None:
                comofue = False
            return comofue
            
        if comofue == True:
            st.success("Respuesta correcta")
        elif comofue == False or comofue == None:
            st.error('Repuesta incorrecta')
            
        # Show the correct answer(s)
        if len(correcta) > 1:
            frase_completa = "Las opciones correctas eran "
            for i in range(len(correcta)):
                frase_completa += f":green[{correcta[i]}]"
                if i != len(correcta)-1:
                    frase_completa += ", "
                elif i == len(correcta)-1:
                    frase_completa += "."
        elif len(correcta) == 1:
            frase_completa = f"La opción correcta era :green[{correcta[0]}]"
            
        # Show solution image if available
        imagen = f'./static/{especialidad}/{str(numero)}_sol.png'
        if os.path.exists(imagen):
            st.image(imagen)
            
        st.write(frase_completa)
        st.markdown(explanation)

        # Show references if available
        if referencias:
            # Check if it's a string or a list
            if isinstance(referencias, str):
                # If it's a string, make sure it's not empty
                if referencias.strip():
                    links = f"[{referencias.strip()}]({referencias.strip()})"
                    st.write(f"Visita la documentación correspondiente {links}")
                else:
                    st.write("No hemos encontrado una documentación como tal para este caso.")
            elif isinstance(referencias, list) and len(referencias) > 0 and referencias[0] != "":
                # If it's a list, create the links normally
                links = ", ".join([f"[{i+1}: {ref}]({ref})" for i, ref in enumerate(referencias)])
                st.write(f"Visita la documentación correspondiente: {links}")
            else:
                st.write("No hemos encontrado una documentación como tal para este caso.")
        else:
            st.write("No hemos encontrado una documentación como tal para este caso.")
    except Exception as e:
        logger.error(f"Error showing solution: {str(e)}", exc_info=True)
        if not getsol:
            st.warning(f"Error showing solution: {str(e)}")
        return False

def comparar_respuestas(respuesta_usuario, respuesta_correcta):
    """
    Compare the user's answers with the correct answers.
    
    Args:
        respuesta_usuario (List[str]): User's answers
        respuesta_correcta (List[str]): Correct answers
        
    Returns:
        bool or None: Whether the answers match (None if no user answer)
    """
    # Check if there's no user answer
    if not respuesta_usuario:
        return None
        
    # Compare types
    if type(respuesta_usuario) != type(respuesta_correcta):
        return False

    # Compare strings
    if isinstance(respuesta_usuario, str):
        return respuesta_usuario == respuesta_correcta

    # Compare lists by converting to sets
    elif isinstance(respuesta_usuario, list):
        return set(respuesta_usuario) == set(respuesta_correcta)
        
    return False

def aux_questions(accion):
    """
    Navigate to the previous or next question.
    
    Args:
        accion (str): The action ('Anterior' for previous or 'Siguiente' for next)
    """
    set_session_state('show_solution', 0)
    
    if accion == 'Anterior':
        st.session_state['question_number_internal'] -= 1
        
    elif accion == 'Siguiente':
        st.session_state['question_number_internal'] += 1

def parse_timestamp(ts_str):
    """
    Parse a timestamp string.
    
    Args:
        ts_str (str): Timestamp string
        
    Returns:
        datetime: Parsed timestamp
    """
    return datetime.datetime.strptime(ts_str, "datetime.datetime(%Y, %m, %d, %H, %M, %S, %f)")

def clear_cache(exclude_keys=None):
    """
    Clear the session state cache, optionally preserving some keys.
    
    Args:
        exclude_keys (List[str], optional): Keys to preserve
    """
    exclude_keys = exclude_keys or []
    keys = list(st.session_state.keys())

    for key in keys:
        if key not in exclude_keys:
            st.session_state.pop(key)

def aux_exam(accion, exam_duration, users_answers):
    """
    Handle exam-related actions.
    
    Args:
        accion (str): The action ('empezar', 'acabar', or 'Inicio')
        exam_duration (int, optional): Exam duration in minutes
        users_answers (List[dict], optional): User's answers
    """
    if accion == 'empezar':
        set_session_state('exam_mode', 1)
        set_session_state('exam_duration', exam_duration)
        
        # Show temporary message
        mensaje_temporal = st.empty()
        mensaje_temporal.write('El examen ha comenzado, si cierras la aplicación sin terminar el examen no podrás ver tus resultados, estos se perderan y no serán registrados. ¡Suerte!')
        
        # Wait for a few seconds
        time.sleep(4)
        
        # Clear the message
        mensaje_temporal.empty()
    elif accion == 'acabar':
        set_session_state('exam_mode', 2)
    elif accion == 'Inicio':
        set_session_state('exam_mode', 0)
        clear_cache(['current_page', 'user'])

def review():
    """Set the review mode to True."""
    set_session_state('review_mode', True)

def setexam(set, jason, mode, conn, user, especialidad, exam_time=None):
    """
    Set up and display an exam.
    
    Args:
        set (List[int]): List of question numbers
        jason (List[dict]): List of questions and answers
        mode (str): Mode ('practicar' or 'examen')
        conn: Database connection
        user (str): Username
        especialidad (str): Specialization type
        exam_time (int, optional): Exam time in minutes
    """
    try:
        if mode == "examen":
            # Initialize session variables
            if 'exam_answers' not in st.session_state:
                st.session_state['exam_answers'] = []
            if 'aux_exam_insert' not in st.session_state:
                st.session_state['aux_exam_insert'] = 0
            aux_exam_insert = st.session_state['aux_exam_insert']
            
            # Insert exam record if not already done
            if aux_exam_insert == 0:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO [esnowflake].[dbo].FACT_EXAMS "
                    "(id_exam, user_nickname, duration_minutes, start_time) "
                    "VALUES ((NEXT VALUE FOR dbo.SEQ_EXAMS - 2), ?, ?, CURRENT_TIMESTAMP)",
                    (user, exam_time)
                )
                conn.commit()
                st.session_state['aux_exam_insert'] = 1
            
            exam_mode = 1  # To avoid returning to state 0 (exam filter state)
            st.session_state['exam_mode'] = exam_mode
            
            # Configure exam timer
            if 'start_time' not in st.session_state:
                st.session_state['start_time'] = datetime.datetime.now()
            current_time = datetime.datetime.now()
            elapsed_time = (current_time - st.session_state['start_time']).total_seconds()
            remaining_time = max(0, (exam_time * 60) - elapsed_time)
            mm, ss = divmod(remaining_time, 60)
            
            # Display timer and exit button
            with st.container():
                crono, space, marca = st.columns([1, 2, 1], gap="large")
                with crono:
                    st.metric(
                        "Tiempo restante", 
                        f"{int(mm):02d}:{int(ss):02d}",
                        help="Este tiempo restante es a título informativo, no finalizará el examen si se te acaba, luego podrás ver cuanto has tardado en hacerlo. El contador se irá actualizando cuando avances o retrocedas una pregunta, también si haces un RERUN de la app"
                    )
                with marca:
                    st.button(
                        'Salir sin guardar',
                        use_container_width=True,
                        on_click=aux_exam,
                        args=('Inicio', None, None)
                    )
        
        # Initialize review mode if not set
        if 'review_mode' not in st.session_state:
            st.session_state['review_mode'] = 0
        review_mode = st.session_state['review_mode']
        
        # Handle review mode
        if review_mode:
            set = st.session_state['review_set']
            io = st.session_state['question_number_internal']
            if io > len(set)-1:
                st.session_state['question_number_internal'] = 0

        # Navigation buttons
        ant, sig = st.columns(2, gap="medium")

        if 'question_number_internal' not in st.session_state:
            st.session_state['question_number_internal'] = 0
        i = st.session_state['question_number_internal']

        if i > len(set)-1:
            st.session_state['question_number_internal'] = 0

        with ant:
            if i != 0:
                st.button(
                    'Anterior',
                    use_container_width=True,
                    on_click=aux_questions,
                    args=('Anterior',)
                )
        with sig:           
            if i != len(set)-1:
                st.button(
                    'Siguiente',
                    use_container_width=True,
                    on_click=aux_questions,
                    args=('Siguiente',)
                )
            if i == len(set)-1:
                if 'review_set' not in st.session_state:
                    st.session_state['review_set'] = []
                review_set = st.session_state['review_set']
                if review_mode or len(review_set) == 0:
                    if mode == "examen":
                        user_answers = st.session_state['exam_answers']
                        st.button(
                            'Finalizar',
                            use_container_width=True,
                            on_click=aux_exam,
                            args=('acabar', None, user_answers)
                        )
                else:
                    st.button(
                        'Revisar preguntas y finalizar',
                        use_container_width=True,
                        on_click=review
                    )

        # Display the current question
        with st.container():
            i = st.session_state['question_number_internal']
            if mode == 'examen':
                if 'exam_answers' not in st.session_state:
                    st.session_state['exam_answers'] = []
                if 'review_set' not in st.session_state:
                    st.session_state['review_set'] = []
            
            # Display the question
            if mode == 'practicar':
                try:
                    st.session_state.counter = 0
                    pregunta(jason, set[i], mode, user, conn, especialidad)
                except Exception as e:
                    logger.error(f"Error displaying question: {str(e)}", exc_info=True)
                    st.warning(f"Error: {str(e)}")
            
            # Handle exam mode questions
            if mode == 'examen':
                try:
                    st.session_state.counter = 0
                    pregunta(jason, set[i]['question_number'], mode, user, conn, especialidad)
                except Exception as e:
                    logger.error(f"Error displaying exam question: {str(e)}", exc_info=True)
                    st.warning(f"Error: {str(e)}")
                
                # Show mark for review button
                st.write("")
                space, marca = st.columns([3.5, 1], gap="large")
                with space:
                    review_set = st.session_state['review_set']
                    st.write(f"Has marcado {len(review_set)} preguntas para revisar")
                with marca:
                    if st.button("Marcar para revisión", use_container_width=True):
                        review_seti = st.session_state['review_set']
                        review_seti.append(set[i])
                        review_set = []
                        for elemento in review_seti:
                            if elemento not in review_set:
                                review_set.append(elemento)
                        st.session_state['review_set'] = review_set
    except Exception as e:
        logger.error(f"Error in exam setup: {str(e)}", exc_info=True)
        st.warning(f"Error: {str(e)}")

def orden_preguntas(question_set):
    """
    Display buttons to order questions randomly or sequentially.
    
    Args:
        question_set (List[int]): List of question numbers
    """
    try:
        order_init_button = """
            <style>.element-container:has(#button-order) + div button {"""
        random_init_button = """
            <style>.element-container:has(#button-random) + div button {"""    
        button = """
                    border: none;
                    color: white;
                    padding: 5px 5px;
                    cursor: pointer;
                    border-radius: 5px;
                    min-width: 10%;
                    background-color: Tomato;
                }</style>"""
        
        order_button = str(order_init_button+button)
        random_button = str(random_init_button+button)

        if "order" not in st.session_state:
            st.session_state["order"] = True

        col2, col3 = st.columns([1, 1], gap="small")
        with col2:
            st.markdown(order_button, unsafe_allow_html=True)
            st.markdown('<span id="button-order"></span>', unsafe_allow_html=True)
            if col2.button("Preguntas en Orden", use_container_width=True):
                st.session_state["question_set"] = sorted(question_set)
                st.rerun()
        with col3:
            st.markdown(random_button, unsafe_allow_html=True)
            st.markdown('<span id="button-random"></span>', unsafe_allow_html=True)
            
            # Shuffle the questions
            shuffled = question_set.copy()
            random.shuffle(shuffled)
            
            if col3.button("Orden aleatorio", use_container_width=True):
                st.session_state["question_set"] = shuffled
                st.rerun()
        st.divider()
    except Exception as e:
        logger.error(f"Error ordering questions: {str(e)}", exc_info=True)

def reset_question_set():
    """Remove the question set from session state."""
    if "question_set" in st.session_state:
        del st.session_state["question_set"]

def filtros(especialidad, datos, conn, user, examen=None):
    """
    Display filters for questions.
    
    Args:
        especialidad (str): Specialization type
        datos (List[dict]): List of questions and answers
        conn: Database connection
        user (str): Username
        examen (bool, optional): Whether this is for exams
        
    Returns:
        List[dict]: Filtered questions
    """
    try:
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
        if especialidad == "snowflake_pro":
            secciones = st.multiselect(
                "¿Qué secciones quieres tocar?",
                c.SECCIONES_SNOWFLAKE_PRO,
            )
        elif especialidad == "snowflake_arch":
            secciones = st.multiselect(
                "¿Qué secciones quieres tocar?",
                c.SECCIONES_SNOWFLAKE_ARCH,
            )
        elif especialidad == "dbt":
            secciones = st.multiselect(
                "¿Qué secciones quieres tocar?",
                c.SECCIONES_DBT,
            )
        elif especialidad == "google":
            secciones = st.multiselect(
                "¿Qué secciones quieres tocar?",
                c.SECCIONES_GOOGLE,
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
        
        # Apply additional filters for exams
        if examen:
            # SQL query to get question history
            consulta_preguntas_hechas = f"""
            SELECT 
                STRING_AGG(CAST(question_id AS NVARCHAR(MAX)), ',') WITHIN GROUP (ORDER BY question_id) AS Hechas, 
                STRING_AGG(CASE WHEN type = 'Examen' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(MAX)) ELSE NULL END, ',') WITHIN GROUP (ORDER BY question_id) AS Examen_falsas, 
                STRING_AGG(CASE WHEN type = 'practicar' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(MAX)) ELSE NULL END, ',') WITHIN GROUP (ORDER BY question_id) AS Practicar_falsas 
            FROM (
                SELECT DISTINCT question_id, type, is_correct 
                FROM [esnowflake].[dbo].Fact_Answers 
                WHERE user_nickname = ?
            ) AS filtered_answers;
            """
            
            cursor = conn.cursor()
            cursor.execute(consulta_preguntas_hechas, (user,))
            aux_opcion = cursor.fetchall()
            
            no_hechas = []
            opcion_examen_falsas = []
            opcion_practicas_falsas = []
            
            if get_session_state("exam_mode", 0) == 0:
                total_question = list(range(len(datos)))

            # Process filter options
            if "Falladas en exámenes" in option and aux_opcion[0][1]:
                opcion_examen_falsas = ast.literal_eval(aux_opcion[0][1])
                
            if "Falladas en práctica" in option and aux_opcion[0][2]:
                opcion_practicas_falsas = ast.literal_eval(aux_opcion[0][2])
                
            if "Sin hacer" in option and aux_opcion[0][0]:
                hechas = aux_opcion[0][0]
                hechas_lista = ast.literal_eval(hechas)
                hechas_int = [int(num) for num in list(hechas_lista)]
                
                if get_session_state("exam_mode", 0) == 0:
                    no_hechas = list(set(total_question) - set(hechas_int))
                else:
                    no_hechas = [
                        item["question_number"]
                        for item in preguntas_filtradas
                        if item["question_number"] not in hechas_int
                    ]
                    
            # Combine all filtered options
            opcion_final = list(
                set(no_hechas + opcion_examen_falsas + opcion_practicas_falsas)
            )
            
            # Apply the combined filter if not "All"
            if "Todas" not in option and option:
                preguntas_filtradas = [
                    item
                    for item in preguntas_filtradas
                    if item["question_number"] in opcion_final
                ]
        
        # Apply section filter
        if "Todas" not in secciones and secciones:
            preguntas_filtradas = [
                item
                for item in preguntas_filtradas
                if any(area in secciones for area in item["question_area"])
            ]
            
        return preguntas_filtradas
    except Exception as e:
        logger.error(f"Error applying filters: {str(e)}", exc_info=True)
        return []

def exam_settings(question_set):
    """
    Display and handle exam settings.
    
    Args:
        question_set (List[dict]): List of filtered questions
        
    Returns:
        Tuple[int, int]: Number of questions and exam duration
    """
    try:
        st.subheader("Opciones")
        
        # Number of questions
        num_questions = st.number_input(
            "Número de preguntas",
            min_value=0,
            max_value=len(question_set),
            value=min(len(question_set), 25),  # Default to 25 or max available
            help="El valor máximo viene dictaminado por el filtrado que hagas",
        )
        
        # Randomly select questions
        selected_questions = random.sample(
            question_set, 
            num_questions if num_questions <= len(question_set) else len(question_set)
        )
        
        # Exam duration
        exam_duration = st.slider(
            "Tiempo de Examen (minutos)",
            min_value=5,
            max_value=120,
            value=60,
        )

        # Update session state
        set_session_state("question_set", selected_questions)
        set_session_state("exam_duration", exam_duration)
        
        return num_questions, exam_duration
    except Exception as e:
        logger.error(f"Error setting up exam: {str(e)}", exc_info=True)
        return 0, 60