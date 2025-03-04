#!/usr/bin/env python3
"""
Combined UI and Performance Patches for Especialidades App

This script combines fixes for UI issues and performance optimizations.
"""

import streamlit as st
import logging
import os
import time
import helper
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#--------------------- UI PATCH SECTION ---------------------#

# Define the missing 'pregunta' function if it doesn't exist
if not hasattr(helper, 'pregunta'):
    def pregunta(question_number, user, mode, is_correct, is_answered, conn):
        """
        Record a user's answer to a question.
        
        Args:
            question_number (int): The question number
            user (str): Username
            mode (str): "examen" or "practicar"
            is_correct (bool): Whether the answer is correct
            is_answered (bool): Whether the question was answered
            conn: Database connection
        """
        try:
            # Insert answer into database
            query = """
            INSERT INTO [esnowflake].[dbo].Fact_Answers 
            (question_id, user_nickname, type, is_correct, is_answered, ANSWER_TIMESTAMP) 
            VALUES (:question_id, :user, :type, :is_correct, :is_answered, CURRENT_TIMESTAMP)
            """
            
            helper.execute_non_query(conn, query, {
                "question_id": question_number,
                "user": user,
                "type": mode,
                "is_correct": 1 if is_correct else 0,
                "is_answered": 1 if is_answered else 0
            })
            
            return True
        except Exception as e:
            logger.error(f"Error recording answer: {str(e)}", exc_info=True)
            return False
    
    # Add to helper module
    helper.pregunta = pregunta

# Fixed implementation of setexam() function
def fixed_setexam(question_set, datos, mode, conn, user, especialidad, exam_time=None):
    """
    Display and handle exam/practice questions.
    
    Args:
        question_set (list): List of question numbers to display
        datos (list): List of all questions with their data
        mode (str): "examen" or "practicar"
        conn: Database connection
        user (str): Username
        especialidad (str): Specialization type
        exam_time (int, optional): Exam duration in minutes
    """
    # Initialize session state for answers
    if "exam_answers" not in st.session_state:
        st.session_state["exam_answers"] = []
    
    # Handle exam timer
    if mode == "examen":
        if "exam_start_time" not in st.session_state:
            st.session_state["exam_start_time"] = time.time()
        
        elapsed_time = int(time.time() - st.session_state["exam_start_time"])
        remaining_time = exam_time * 60 - elapsed_time if exam_time else 0
        
        if remaining_time <= 0 and exam_time:
            st.error("¡Tiempo agotado!")
            st.session_state["exam_mode"] = 2
            st.rerun()
        
        if exam_time:
            mins, secs = divmod(remaining_time, 60)
            st.write(f"Tiempo restante: {mins:02d}:{secs:02d}")
    
    # Check for empty question set
    if not question_set:
        st.warning("No hay preguntas disponibles")
        return
    
    # Initialize current question index
    if "current_question" not in st.session_state:
        st.session_state["current_question"] = 0
    
    current_idx = st.session_state["current_question"]
    
    # Check if we've completed all questions
    if current_idx >= len(question_set):
        if mode == "examen":
            st.session_state["exam_mode"] = 2
            st.session_state["aux_exam_insert"] = 1
            st.rerun()
        else:
            st.success("¡Has completado todas las preguntas!")
            st.session_state["current_question"] = 0
            st.rerun()
        return
    
    # Get question data
    question_number = question_set[current_idx]
    question_data = next((q for q in datos if q["question_number"] == question_number), None)
    
    if not question_data:
        st.error(f"No se encontró la pregunta {question_number}")
        st.session_state["current_question"] += 1
        st.rerun()
        return
    
    # Display question
    st.subheader(f"Pregunta {current_idx + 1} de {len(question_set)}")
    
    # Fix for area display - ensure proper joining of area names
    if 'question_area' in question_data and isinstance(question_data['question_area'], list):
        area_text = ", ".join(question_data['question_area'])
        st.write(f"**Área:** {area_text}")
    else:
        st.write(f"**Área:** {question_data.get('question_area', 'No disponible')}")
    
    st.markdown(f"**{question_data['question']}**")
    
    # Display question image if exists
    try:
        image_path = f"static/{especialidad}/{question_number}.png"
        if os.path.exists(image_path):
            st.image(image_path)
    except Exception as e:
        logger.error(f"Error displaying image: {str(e)}")
    
    # Display answer options
    answers = question_data.get("answers", [])
    correct_answer = question_data.get("correct_answer", [])
    
    # Determine if multiple choice
    is_multiple = False
    if isinstance(correct_answer, list) and len(correct_answer) > 1:
        is_multiple = True
    
    if is_multiple:
        st.write("**Selecciona todas las opciones correctas:**")
        # Using checkboxes instead of multiselect for multiple choice
        selected_answers = []
        for idx, answer in enumerate(answers):
            if st.checkbox(answer, key=f"checkbox_{question_number}_{idx}"):
                selected_answers.append(answer)
        user_answer = selected_answers
    else:
        st.write("**Selecciona la opción correcta:**")
        user_answer = st.radio("Opciones", answers, key=f"radio_{question_number}")
    
    # Navigation buttons with unique keys and full width
    col1, col2 = st.columns([1, 1])
    with col1:
        prev_button_label = "Anterior" if current_idx > 0 else "Saltar"
        if st.button(prev_button_label, key=f"prev_button_{current_idx}", use_container_width=True):
            if current_idx > 0:
                st.session_state["current_question"] -= 1
            else:
                st.session_state["current_question"] += 1
            st.rerun()
    
    with col2:
        button_label = "Siguiente" if mode == "examen" else "Comprobar"
        if st.button(button_label, key=f"next_button_{current_idx}", use_container_width=True):
            # Record answer
            timestamp = time.time()
            st.session_state["exam_answers"].append({
                "question_number": question_number,
                "user_answer": user_answer,
                "timestamp": timestamp
            })
            
            # Check answer for practice mode
            if mode == "practicar" and user:
                is_correct = helper.comparar_respuestas(user_answer, correct_answer)
                helper.pregunta(question_number, user, mode, is_correct, True, conn)
                
                if is_correct:
                    st.success("¡Correcto!")
                else:
                    st.error("Incorrecto")
                    st.write("Respuesta(s) correcta(s):")
                    st.write(correct_answer)
                
                if "explanation" in question_data:
                    st.write("Explicación:")
                    st.markdown(question_data["explanation"])
            
            # Move to next question
            st.session_state["current_question"] += 1
            st.rerun()

# Fixed implementation of filtros() function
def fixed_filtros(especialidad, datos, conn, user, is_exam=False):
    """
    Filter questions based on user selections.
    
    Args:
        especialidad (str): The specialization type
        datos (list): List of all questions with their data
        conn: Database connection
        user (str): Username
        is_exam (bool): Whether in exam mode
        
    Returns:
        list: Filtered questions
    """
    import constantes as c
    import ast
    
    # Get question numbers
    question_numbers = [q["question_number"] for q in datos]
    min_q = min(question_numbers) if question_numbers else 0
    max_q = max(question_numbers) if question_numbers else 100
    
    # Question range slider
    values = st.slider(
        "Seleccione rango de preguntas",
        min_value=min_q,
        max_value=max_q,
        value=(min_q, max_q),
        step=1,
        key=f"question_range_slider_{especialidad}"
    )
    
    # Apply range filter
    preguntas_filtradas = [
        item for item in datos 
        if values[0] <= item["question_number"] <= values[1]
    ]
    
    if not is_exam:
        # Section selection
        secciones = st.multiselect(
            "¿Qué secciones quieres tocar?",
            getattr(c, f"SECCIONES_{especialidad.upper()}"),
            key=f"section_selector_{especialidad}"
        )
        
        # Apply section filter
        if secciones and "Todas" not in secciones:
            preguntas_filtradas = [
                item for item in preguntas_filtradas
                if any(area in secciones for area in item["question_area"])
            ]
            
        # Other filters
        option = st.multiselect(
            "Otros filtros",
            ["Todas", "Sin hacer", "Falladas en exámenes", "Falladas en práctica"],
            key=f"other_filters_{especialidad}"
        )
        
        if user and option:
            # Get question history
            result = helper.execute_query(
                conn,
                "EXEC GetQuestionHistory @user=:user",
                {"user": user},
                fetch_all=False,
                as_dict=True
            )
            
            if result:
                no_hechas = []
                opcion_examen_falsas = []
                opcion_practicas_falsas = []
                
                # Process filter options
                if "Falladas en exámenes" in option and result.get("exam_failed"):
                    opcion_examen_falsas = ast.literal_eval(result["exam_failed"])
                    
                if "Falladas en práctica" in option and result.get("practice_failed"):
                    opcion_practicas_falsas = ast.literal_eval(result["practice_failed"])
                    
                if "Sin hacer" in option and result.get("done"):
                    hechas = ast.literal_eval(result["done"])
                    hechas_int = [int(num) for num in hechas]
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
                if "Todas" not in option:
                    preguntas_filtradas = [
                        item for item in preguntas_filtradas
                        if item["question_number"] in opcion_final
                    ]
    
    return preguntas_filtradas

#--------------------- PERFORMANCE PATCH SECTION ---------------------#

# Performance optimization for database connections
original_init_connection = helper.init_connection

@st.cache_resource(ttl=3600, show_spinner=False)  # Cache for 1 hour
def optimized_init_connection(especialidad):
    """
    Performance-optimized database connection function.
    Uses caching and avoids unnecessary reconnections.
    """
    # Use the original function without the spinner
    return original_init_connection(especialidad)

# Optimize execute_query
original_execute_query = helper.execute_query

def optimized_execute_query(conn, query, params=None, fetch_all=True, as_dict=False):
    """Optimized query execution with better error handling and performance."""
    # For read-only queries that can be cached (but not user-specific ones)
    cacheable = (
        query.strip().upper().startswith("SELECT") and 
        "GetQuestionHistory" not in query and
        "user_nickname" not in query.lower() and
        "username" not in query.lower()
    )
    
    if cacheable:
        # Use st.cache_data if appropriate
        @st.cache_data(ttl=60)  # Cache for 1 minute
        def cached_query(query_str, params_str=None):
            return original_execute_query(conn, query_str, params, fetch_all, as_dict)
        
        # Convert params to string for caching
        params_str = str(params) if params else None
        return cached_query(query, params_str)
    else:
        # Use original for updates and uncacheable queries
        return original_execute_query(conn, query, params, fetch_all, as_dict)

#--------------------- APPLY PATCHES ---------------------#

# Apply UI patches
helper.setexam = fixed_setexam
helper.filtros = fixed_filtros

# Apply performance patches
helper.init_connection = optimized_init_connection
helper.execute_query = optimized_execute_query

logger.info("✅ Combined UI and performance patches applied successfully!")

if __name__ == "__main__":
    # Log that the patch was applied
    logger.info("Combined patches executed directly")