import json
import pandas as pd
import os
import streamlit as st
from io import BytesIO

# Función para crear el CSV
def create_excel(especialidad):
    if especialidad == 'snowflake_pro':
        nombre_fichero = 'sn_pro_examtopics'
    elif especialidad == 'snowflake_arch':
        nombre_fichero = 'sn_arch_examtopics'
    elif especialidad == 'dbt':
        nombre_fichero = 'dbt_examtopics'
    elif especialidad == 'google':
        nombre_fichero = 'google_examtopics'
    
    nombre_completo = nombre_fichero + '.json'

    # Leer el archivo JSON
    with open(nombre_completo, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Crear una lista para almacenar los datos transformados
    rows = []

    # Procesar cada pregunta en el archivo JSON
    for question in data:
        # Crear un diccionario para almacenar los datos de cada fila
        row = {
            "question_number": question.get("question_number"),
            "question_area": (question.get("question_area", [])),  # Usamos "; " para separar valores en vez de coma
            "question": question.get("question"),
            "question_extra_info": question.get("question_extra_info", ""),  # Campo opcional
            "answers": (question.get("answers", [])),  # Unimos las respuestas con saltos de línea
            "correct_answer": (question.get("correct_answer", [])),  # Unimos las respuestas correctas con saltos de línea
            "explanation": question.get("explanation").replace("\n", " ").replace("\r", ""),  # Limpiar saltos de línea innecesarios
            "reference": (question.get("reference", []))  # Usamos "; " para unir las referencias con comas
        }
        # Añadir la fila a la lista de filas
        rows.append(row)

    # Convertir la lista de filas en un DataFrame de pandas
    df = pd.DataFrame(rows)
    return df


@st.cache_data
def download_excel(especialidad):
    df = create_excel(especialidad)  # Llama a la función para crear el DataFrame a partir del JSON
    # Convertir el DataFrame a un buffer Excel
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_buffer.seek(0)
    
    nombre_fichero = especialidad + '.xlsx'
    return excel_buffer, nombre_fichero

def button_download(excel_buffer, nombre_fichero):
    # Botón de descarga
    st.download_button(
        label="¿Estás seguro que quieres descargar el archivo con las preguntas?",
        data=excel_buffer,
        file_name=nombre_fichero,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )