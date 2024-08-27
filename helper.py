import os
import random
from docx import Document

import json
import streamlit as st
import uuid
from settings import Snowflake_conexion as sc
import time
import threading
from streamlit.components.v1 import html
import datetime
import pyodbc
from pathlib import Path
import ast
import constantes as c
from sqlalchemy import create_engine, text

@st.cache_resource
def init_connection(especialidad):
    if especialidad in ['snowflake','dbt','google']:
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
    elif especialidad in ['sql']:
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
        engine = create_engine(connection_str, pool_size=10000, max_overflow=2000000)
        return engine
    else:
        raise Exception("Ha habido un error al iniciar sesión en SQL Server")        


def open_file(json_file):
    # Abre el archivo JSON en modo lectura
    with open(json_file, 'r', encoding='utf-8') as archivo:
        datos = json.load(archivo)
    return datos

def get_user_none():
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    user = st.session_state['user']
    return user

def recharge_user_list(conn):
    query = "select name from [esnowflake].[dbo].Dim_Users ORDER BY name"
    user_list_v = (
    conn.cursor()
            .execute(
                query
            )
            .fetchall()
    )
    lista_plana = [item[0] for item in user_list_v]
    return lista_plana

def new_user(conn, new_user, message=None):
    try:
        query = f"INSERT INTO [esnowflake].[dbo].Dim_Users (name, rango) VALUES ('{new_user}', 'Iniciado')"
        conn.cursor().execute(query).fetchall()
        conn.commit()
        if message:
            st.success('New user added successfully!')
        st.session_state["user"] = new_user
        st.session_state['lista_plana'] = recharge_user_list(conn)
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f'Error adding new user: {e}')

def reset_delete_user(conn,useri, delete):
    action = ''
    if delete:
        action = ['delete','deleting']
    else:
        action = ['reset','reseting']
    try:
        conn.cursor().execute(f"DELETE FROM [esnowflake].[dbo].Dim_Users WHERE name = '{useri}'")
        conn.cursor().execute(f"DELETE FROM [esnowflake].[dbo].FACT_ANSWERS where user_nickname = '{useri}'") 
        conn.cursor().execute(f"DELETE FROM [esnowflake].[dbo].FACT_EXAMS where user_nickname = '{useri}'")
        conn.commit()
        
        # Tiene que estar aquí porque si no, no sale el texto
        st.success("Action completed!")
        if delete == True:
            st.session_state["user"] = None
        else:
            new_user(conn,useri)

        st.session_state['count_reset'] = 0
        st.session_state['count_delete'] = 0
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f'Error {action[1]} user: {e}')


def process_qa_block(qa_block):
    # Eliminar líneas vacías
    qa_block = [line for line in qa_block if line]

    # La primera línea después del título 'Question #...' es la pregunta
    # Las líneas restantes son las respuestas
    question = qa_block[1]
    answers = qa_block[2:]

    return {"question": question, "answers": answers}

def extract_questions_and_answers(docx_file_path):
    doc = Document(docx_file_path)
    questions_with_answers = []
    current_qa = []
    capture = False

    for para in doc.paragraphs:
        text = para.text.strip()
        if text.startswith("Question #"):
            if current_qa:
                # Procesar el bloque de pregunta actual
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

def checkbox_help(unique_key):
    if st.session_state[unique_key] == 0:
        st.session_state[unique_key] = 1
    elif st.session_state[unique_key] == 1:
        st.session_state[unique_key] = 0

def reset_counter():
    st.session_state.counter = 0

def increment_counter():
    st.session_state.counter += 1

def pregunta(jason, n, mode, user, conn, especialidad):
        if 'order' not in st.session_state:
            st.session_state["order"] = True

        json_question = jason[n-1]
        numero = json_question["question_number"]
        pregunta = json_question["question"]
        respuestas = json_question["answers"]
        question_area = json_question["question_area"]

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
            st.session_state['seen_questions']
            
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
        # Se indica el número de preguntas
        numero_info = st.session_state['question_number_internal']+1
        num_question_set = len(st.session_state["question_set"])
        st.info(f'Pregunta {str(numero_info)} de {str(num_question_set)}.')
        st.write(f'Pregunta {numero} de ExamTopics')
        # Assuming question_area might sometimes come as a string instead of list
        if isinstance(question_area, str):
            question_area = [question_area]  # Convert to a list if it's a single string

        if question_area:  # Check if the list is not empty
            areas = ', '.join(question_area)  # Join all elements of the list into a single string separated by commas
            st.write(f":orange[Question area:] {areas}")

        else:
            st.write(":orange[No question area specified]")

        # EXTRA INFORMATION
        # Verificar y mostrar información extra si está disponible
        if "question_extra_info" in json_question and json_question["question_extra_info"]:
            with st.expander(" 🔽 Información extra del caso:"):
                st.markdown(json_question["question_extra_info"])
        
        st.markdown(pregunta)
        imagen = './static/' + especialidad + '/' + str(numero) + ".png"
        if os.path.exists(imagen):
            st.image(imagen)

        # Se inicializa el array de respuestas del usuario para evitar problemas de modificación directa
        response_key = f"user_respuestas_{numero}"
        if response_key not in st.session_state:
            st.session_state[response_key] = [False] * len(respuestas)

        for i, respuesta in enumerate(respuestas):
            unique_key = f"{numero}.{i}"
            # Se crean los checkbox con el estado predefinido
            user_response = st.checkbox(f'{respuesta}', value=st.session_state[response_key][i], key=unique_key)
            st.session_state[response_key][i] = user_response

        # Logica para procesar las respuestas
        user_respuestas = st.session_state[response_key]
        # Esto recoge el testo de las respuestas donde el checkbox está marcado (True)
        user_answer = [resp for resp, checked in zip(respuestas, user_respuestas) if checked]
        
        # Determina si la respuesta es correcta
        is_correct = sol(especialidad, jason, n, user_answer, 1) if user_answer else False
        is_answered = bool(user_answer)
        # Muestra la solución
        with st.container():
            if mode == "practicar":
                s = 'show_solution'
                if 'show_solution' not in st.session_state:
                    st.session_state['show_solution'] = 0

                with st.container():
                    # Botón para mostrar la solución
                    is_correct = sol(especialidad,jason,n,user_answer,1)
                    is_answered = 0
                    if user_answer:
                        is_answered = 1
                    st.button('Ver solución', key=uuid.uuid4(),on_click= checkbox_help, args = (s,))

                    if st.session_state['show_solution'] == 1:
                        try:
                            is_correct_int = 1 if is_correct else 0
                            is_answered_int = 1 if is_answered else 0
                            
                            query = f"INSERT INTO [esnowflake].[dbo].Fact_Answers select {n},'{user}','{mode}',null,{is_correct_int},{is_answered_int},current_timestamp"
                            conn.cursor().execute(query)
                            conn.cursor().commit()
                        except Exception as e:
                            st.write(f"An error occurred in function pregunta: {e} ") 

                    # Muestra la solución si la variable de estado es True
                    if st.session_state['show_solution']:
                        sol(especialidad,jason, n, user_answer)  # Llama a la función sol

            elif mode == 'examen':
                jsoni = {
                    "question_number": numero,
                    "user_answer": user_answer,
                    "timestamp": datetime.datetime.now()
                }
                st.session_state['exam_answers'].append(jsoni)


def sol(especialidad, jason,n,user_answer,getsol = False):

    json_question = jason[n-1]
    # Extrae los datos necesarios del JSON
    correcta = json_question["correct_answer"]
    explanation = json_question["explanation"]
    referencias = json_question["reference"]
    numero = json_question["question_number"]
    
    if type(user_answer) == str:
        user_answer = [user_answer]
    comofue = comparar_respuestas(user_answer,correcta) 
    if getsol == True:
        if comofue is None:
            comofue = False
        return comofue
    if comofue == True:
        st.success("Respuesta correcta")
    elif comofue == False or comofue == None:
        st.error('Repuesta incorrecta')
    if len(correcta) > 1:
        frase_completa = "Las opciones correctas eran "
        for i in range(len(correcta)):
            frase_completa += f":green[{correcta[i]}]"
            if i != len(correcta)-1:
                frase_completa += ", "
            elif i == len(correcta)-1:
                frase_completa+="."
    elif len(correcta) == 1:
        frase_completa = f"La opción correcta era :green[{correcta[0]}]"
    imagen = './static/' + especialidad + '/' + str(numero) + "_sol.png"
    if os.path.exists(imagen):
        st.image(imagen)
    st.write(frase_completa)
    st.markdown(explanation)

    if referencias:
        # Verificar si es un string o una lista
        if isinstance(referencias, str):
            # Si es un string, asegurarse de que no esté vacío
            if referencias.strip():
                links = f"[{referencias.strip()}]({referencias.strip()})"
                st.write(f"Visita la documentación correspondiente {links}")
            else:
                st.write("No hemos encontrado una documentación como tal para este caso.")
        elif isinstance(referencias, list) and len(referencias) > 0 and referencias[0] != "":
            # Si es una lista, crear los enlaces de forma normal
            links = ", ".join([f"{ref}" for ref in enumerate(referencias)])
            st.write(f"Visita la documentación correspondiente {links}")
        else:
            st.write("No hemos encontrado una documentación como tal para este caso.")
    else:
        st.write("No hemos encontrado una documentación como tal para este caso.")

    

def comparar_respuestas(respuesta_usuario, respuesta_correcta):
    # Comparar tipos
    if not respuesta_usuario:
        return None
    if type(respuesta_usuario) != type(respuesta_correcta):
        return False

    # Comparación de cadenas de texto
    if isinstance(respuesta_usuario, str):
        return respuesta_usuario == respuesta_correcta

    # Comparación de listas
    elif isinstance(respuesta_usuario, list):
        # Convertir a conjuntos y comparar
        return set(respuesta_usuario) == set(respuesta_correcta)

def aux_questions(accion):
    st.session_state['show_solution'] = 0
    
    if accion == 'Anterior':
        st.session_state['question_number_internal'] += -1
        
    elif accion == 'Siguiente':
        st.session_state['question_number_internal'] += 1

def parse_timestamp(ts_str):
    return datetime.datetime.strptime(ts_str, "datetime.datetime(%Y, %m, %d, %H, %M, %S, %f)")

def clear_cache(exclude_keys=None):
    exclude_keys = exclude_keys or []
    keys = list(st.session_state.keys())

    for key in keys:
        if key not in exclude_keys:
            st.session_state.pop(key)

def aux_exam(accion,exam_duration,users_answers):
    if accion == 'empezar':
        exam_mode = 1
        if 'exam_duration' not in st.session_state:
            st.session_state['exam_duration'] = exam_duration

        st.session_state['exam_mode'] = exam_mode
        # Muestra el mensaje
        mensaje_temporal = st.empty()
        mensaje_temporal.write('El examen ha comenzado, si cierras la aplicación sin terminar el examen no podrás ver tus resultados, estos se perderan y no serán registrados. ¡Suerte!')
        
        # Espera durante los segundos especificados
        time.sleep(4)
        
        # Borra el mensaje
        mensaje_temporal.empty()
    elif accion == 'acabar':
        exam_mode = 2
        st.session_state['exam_mode'] = exam_mode
    elif accion == 'Inicio':
        exam_mode = 0
        clear_cache(['current_page','user'])


def review():
    if 'review_mode' not in st.session_state:
        st.session_state['review_mode'] = True
    else:
        st.session_state['review_mode'] = True


def setexam(set,jason,mode,conn,user,especialidad,exam_time = None):
    if mode == "examen":
        ##################################
        ###    INICIALIZANDO VARIABLES SESIÓN
        ##################################
        if 'exam_answers' not in st.session_state:
                st.session_state['exam_answers'] = []
        if 'aux_exam_insert' not in st.session_state:
            st.session_state['aux_exam_insert'] = 0
        aux_exam_insert = st.session_state['aux_exam_insert']
        
        if aux_exam_insert == 0:
            conn.cursor().execute(f"insert into [esnowflake].[dbo].FACT_EXAMS select (NEXT VALUE FOR dbo.SEQ_EXAMS - 2),null,'{user}',{exam_time},null,current_timestamp,null,null,null")
            st.session_state['aux_exam_insert'] = 1
        
        exam_mode = 1 # Para no volver al estado 0 que era el de filtros de examen
        st.session_state['exam_mode'] = exam_mode
        
        ## Configuramos el tiempo del examen
        if 'start_time' not in st.session_state:
            st.session_state['start_time'] = datetime.datetime.now()
        current_time = datetime.datetime.now()
        elapsed_time = (current_time - st.session_state['start_time']).total_seconds()
        remaining_time = max(0, (exam_time * 60) - elapsed_time)  # Asegúrate de que exam_time esté en minutos
        mm, ss = divmod(remaining_time, 60)
        with st.container():
            crono,space,marca = st.columns([1,2,1], gap = "large")
            with crono:
                st.metric("Tiempo restante", f"{int(mm):02d}:{int(ss):02d}",help = "Este tiempo restante es a título informativo, no finalizará el examen si se te acaba, luego podrás ver cuanto has tardado en hacerlo. El contador se irá actualizando cuando avances o retrocedas una pregunta, también si haces un RERUN de la app")
            with marca:
                st.button('Salir sin guardar',use_container_width=True,on_click = aux_exam , args = ('Inicio',None,None,))
        ##########################################
    if 'review_mode' not in st.session_state:
            st.session_state['review_mode'] = 0
    review_mode = st.session_state['review_mode']
    
    if review_mode:
        set = st.session_state['review_set']
        io = st.session_state['question_number_internal']
        if io > len(set)-1:
            st.session_state['question_number_internal'] = 0

    ant,sig = st.columns(2, gap = "medium")

    if 'question_number_internal' not in st.session_state:
        st.session_state['question_number_internal'] = 0
    i = st.session_state['question_number_internal']

    if i > len(set)-1:
        st.session_state['question_number_internal'] = 0

    with ant:
        if i != 0:
            st.button('Anterior',use_container_width=1,on_click = aux_questions , args = ('Anterior',))
    with sig:           
        if i != len(set)-1:
            st.button('Siguiente',use_container_width=1,on_click = aux_questions , args = ('Siguiente',))
        if i == len(set)-1:
            review_set = st.session_state['review_set'] = []
            if review_mode or len(review_set) == 0:
                if mode == "examen":
                    user_answers = st.session_state['exam_answers']
                    st.button('Finalizar',use_container_width=1,on_click = aux_exam, args = ('acabar',None,user_answers,))
            else:
                st.button('Revisar preguntas y finalizar',use_container_width=1,on_click = review)

    with st.container():
        i = st.session_state['question_number_internal']
        if mode == 'examen':
            if 'exam_answers' not in st.session_state:
                st.session_state['exam_answers'] = []
            if 'review_set' not in st.session_state:
                    st.session_state['review_set'] = []
        #pregunta_container = st.empty()
        #with pregunta_container.container():
        if mode == 'practicar':
            try:
                st.session_state.counter = 0
                pregunta(jason, set[i], mode, user, conn, especialidad)
            except Exception as e:
                st.warning("Error: " + str(e.args))
        if mode == 'examen':
            try:
                st.session_state.counter = 0
                pregunta(jason, set[i]['question_number'], mode, user, conn, especialidad)
            except Exception as e:
                st.warning("Error: " + str(e.args))
            st.write("")
            space,marca = st.columns([3.5,1], gap = "large")
            with space:
                review_set = st.session_state['review_set']
                st.write(f"Has marcado {len(review_set)} preguntas para revisar")
            with marca:
                if st.button("Marcar para revisión ",use_container_width=True):
                    review_seti = st.session_state['review_set']
                    review_seti.append(set[i])
                    review_set = []
                    for elemento in review_seti:
                        if elemento not in review_set:
                            review_set.append(elemento)

                    st.session_state['review_set'] = review_set

def orden_preguntas(question_set):
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

    col2, col3 = st.columns([1,1], gap="small")
    with col2:
        st.markdown(order_button, unsafe_allow_html=True)
        st.markdown('<span id="button-order"></span>', unsafe_allow_html=True)
        if col2.button("Preguntas en Orden", use_container_width=True):
            st.session_state["question_set"] = sorted(question_set)
            st.rerun()
    with col3:
        st.markdown(random_button, unsafe_allow_html=True)
        st.markdown('<span id="button-random"></span>', unsafe_allow_html=True)
        if col3.button("Orden aleatorio", on_click=random.shuffle(question_set), use_container_width=True):
            st.session_state["question_set"] = question_set
            st.rerun()
    st.divider()

def reset_question_set():
    if "question_set" in st.session_state:
        del st.session_state["question_set"]

def filtros(especialidad, datos, conn, user, examen=None):
    """
    Sirve solamente para el filtro de examen, no para el de práctica --> TENER CUIDADO!
    """
    st.subheader("Filtros")
    values = st.slider(
        "Seleccione rango de preguntas en el que practicar",
        0,
        len(datos),
        (0, len(datos)),
        step=1,
    )
    if especialidad == "snowflake":
        secciones = st.multiselect(
            "¿ Qué secciones quieres tocar ?",
            c.SECCIONES_SNOWFLAKE,
        )
    elif especialidad == "dbt":
        secciones = st.multiselect(
            "¿ Qué secciones quieres tocar ?",
            c.SECCIONES_DBT,
        )
    elif especialidad == "google":
        secciones = st.multiselect(
            "¿ Qué secciones quieres tocar ?",
            c.SECCIONES_GOOGLE,
    )
    option = st.multiselect(
        "Otros filtros",
        ["Todas", "Sin hacer", "Falladas en exámenes", "Falladas en práctica"],
    )
    preguntas_filtradas = [
        item for item in datos if values[0] <= item["question_number"] <= values[1]
    ]
    
    if examen:
        consulta_preguntas_hechas = f"""SELECT 
        STRING_AGG(CAST(question_id AS NVARCHAR(MAX)), ',') WITHIN GROUP (ORDER BY question_id) AS Hechas, 
        STRING_AGG(CASE WHEN type = 'Examen' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(MAX)) ELSE NULL END, ',') WITHIN GROUP (ORDER BY question_id) AS Examen_falsas, 
        STRING_AGG(CASE WHEN type = 'practicar' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(MAX)) ELSE NULL END, ',') WITHIN GROUP (ORDER BY question_id) AS Practicar_falsas 
        FROM (SELECT DISTINCT question_id, type, is_correct FROM [esnowflake].[dbo].Fact_Answers WHERE user_nickname = '{user}') AS filtered_answers;"""
        
        aux_opcion = conn.cursor().execute(consulta_preguntas_hechas).fetchall()
        no_hechas = []
        opcion_examen_falsas = []
        opcion_practicas_falsas = []
        if st.session_state["exam_mode"] == 0:
            total_question = range(len(datos))

        if "Falladas en exámenes" in option:
            opcion_examen_falsas = ast.literal_eval(aux_opcion[0][1])
        if "Falladas en práctica" in option:
            opcion_practicas_falsas = ast.literal_eval(aux_opcion[0][2])
        if "Sin hacer" in option:
            hechas = aux_opcion[0][0]
            hechas_lista = ast.literal_eval(hechas)
            hechas_int = [int(num) for num in list(hechas_lista)]
            if st.session_state["exam_mode"] == 0:
                no_hechas = list(set(total_question) - set(hechas))
            else:
                no_hechas = [
                    item["question_number"]
                    for item in preguntas_filtradas
                    if item["question_number"] not in hechas_int
                ]
        opcion_final = list(
            set(no_hechas + opcion_examen_falsas + opcion_practicas_falsas)
        )
        # AÑADIR FILTRO OTROS
        if "Todas" not in option and option != []:
            preguntas_filtradas = [
                item
                for item in preguntas_filtradas
                if item["question_number"] in opcion_final
            ]
    if "Todas" not in secciones and secciones != []:
        preguntas_filtradas = [
            item
            for item in preguntas_filtradas
            if any(area in secciones for area in item["question_area"])
        ]
    return preguntas_filtradas


def exam_settings(question_set):
    st.subheader("Opciones")
    # Número de preguntas
    num_questions = st.number_input(
        "Número de preguntas",
        min_value=0,
        max_value=len(question_set),
        value=len(question_set),
        help="El valor máximo viene dictaminado por el filtrado que hagas",
    )
    selected_questions = random.sample(question_set, num_questions)
    # Duración del examen
    exam_duration = st.slider(
        "Tiempo de Examen (minutos)",
        min_value=5,
        max_value=120,
        value=60,
    )

    st.session_state["question_set"] = selected_questions
    st.session_state["exam_duration"] = exam_duration
    
    return num_questions, exam_duration
