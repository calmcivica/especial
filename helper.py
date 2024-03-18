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

@st.cache_resource
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + st.secrets["server"]
        + ";DATABASE="
        + st.secrets["database"]
        + ";UID="
        + st.secrets["username"]
        + ";PWD="
        + st.secrets["password"]
    )

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

def pregunta(jason,n,mode,user,conn, especialidad):
        
        json_question = jason[n-1]
        # Extrae los datos necesarios del JSON
        numero = json_question["question_number"]
        pregunta = json_question["question"]
        respuestas = json_question["answers"]
        
        if mode == 'practicar':
            st.write(f'Pregunta {numero} de ExamTopics')
        st.write(pregunta)
        imagen = str(Path.cwd()) +'\\images\\'+'\\' + especialidad + '\\' + str(numero) + ".png"
        if imagen != None:
            try:
                st.image(imagen)
            except:
                pass
        user_respuestas= [False]*len(respuestas)

        if 'checkbox' not in st.session_state:
            st.session_state['checkbox'] = False
        for i in range(len(respuestas)):
            unique_key = f"{numero}.{i}"
            if unique_key not in st.session_state:
                st.session_state[unique_key] = False
            user_respuestas[i] = st.checkbox(f'{respuestas[i]}',value = st.session_state[unique_key],key= uuid.uuid4(),on_change=checkbox_help,args = (unique_key,))
            st.session_state[unique_key] = user_respuestas[i]
        
        true_count = user_respuestas.count(True)
        if true_count == 1:
            # Solo hay un 'True', almacenar la respuesta correspondiente en user_answer
            indice = user_respuestas.index(True)
            user_answer = respuestas[indice]
        elif true_count > 1:
            # Hay múltiples 'True', almacenar las respuestas correspondientes en user_answer
            user_answer = [respuestas[i] for i in range(len(respuestas)) if user_respuestas[i]]
        else:
            # No hay ningún 'True'
            user_answer = None
        with st.container():
            if mode == "practicar":
                s = 'show_solution'
                if 'show_solution' not in st.session_state:
                    st.session_state['show_solution'] = 0
                    
                with st.container():
                    # Botón para mostrar la solución
                    is_correct = sol(jason,n,user_answer,1)
                    is_answered = 0
                    if user_answer:
                        is_answered = 1
                    st.button('Ver solución', key=uuid.uuid4(),on_click= checkbox_help, args = (s,))

                    if st.session_state['show_solution'] == 1:
                    
                        try:
                            is_correct_int = 1 if is_correct else 0
                            is_answered_int = 1 if is_answered else 0
                            
                            query = f"INSERT INTO esnowflake.esnowflake_DEV.Fact_Answers select {n},'{user}','{mode}',null,{is_correct_int},{is_answered_int},current_timestamp"
                            conn.cursor().execute(query)
                            conn.cursor().commit()
                        except Exception as e:
                            st.write(f"An error occurred: {e} ") 


                    # Muestra la solución si la variable de estado es True
                    if st.session_state['show_solution']:
                        sol(jason, n, user_answer)  # Llama a la función sol

            elif mode == 'examen':
                
                jsoni = {
                    "question_number": numero,
                    "user_answer": user_answer,
                    "timestamp": datetime.datetime.now()
                }

                st.session_state['exam_answers'].append(jsoni)


def sol(jason,n,user_answer,getsol = False):

    json_question = jason[n-1]
    # Extrae los datos necesarios del JSON
    correcta = json_question["correct_answer"]
    explanation = json_question["explanation"]
    referencias = json_question["reference"]
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
            frase_completa += f"{correcta[i]}"
            if i != len(correcta)-1:
                frase_completa += ", "
            elif i == len(correcta)-1:
                frase_completa+="."
    elif len(correcta) == 1:
        frase_completa = f"La opción correcta era {correcta[0]}"

    st.write(frase_completa)
    st.write(explanation)
    st.write("Visita la documentación correspondiente [link](%s)" % referencias)

    

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
        if 'exam_answers' not in st.session_state:
                st.session_state['exam_answers'] = []
        if 'aux_exam_insert' not in st.session_state:
            st.session_state['aux_exam_insert'] = 0
        aux_exam_insert = st.session_state['aux_exam_insert']
        if aux_exam_insert == 0:
            conn.cursor().execute(f"insert into esnowflake.esnowflake_DEV.FACT_EXAMS select NEXT VALUE FOR dbo.SEQ_EXAMS,null,'{user}',{exam_time},null,current_timestamp,null,null,null")
            st.session_state['aux_exam_insert'] = 1
        exam_mode = 1
        st.session_state['exam_mode'] = exam_mode
        
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
            pregunta(jason, set[i], mode, user, conn, especialidad)            
        if mode == 'examen':
            pregunta(jason, set[i], mode, user, conn, especialidad)
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

    col2, col3 = st.columns([1,1], gap="small")
    with col2:
        st.markdown(order_button, unsafe_allow_html=True)
        st.markdown('<span id="button-order"></span>', unsafe_allow_html=True)
        if col2.button("Preguntas en Orden", use_container_width=True):
            st.session_state["question_set"] = sorted(question_set)
            st.warning("True")
    with col3:
        st.markdown(random_button, unsafe_allow_html=True)
        st.markdown('<span id="button-random"></span>', unsafe_allow_html=True)
        if col3.button("Orden aleatorio", on_click=random.shuffle(question_set), use_container_width=True):
            st.session_state["question_set"] = question_set
            st.warning("True")
    st.divider()