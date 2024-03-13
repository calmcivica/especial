import streamlit as st
import helper as h
import valores_fijos as vf
import ast
import random
import plotly.graph_objects as go
from agent import chat
import plotly.express as px
import pandas as pd

def get_datos(especialidad):
    # Get json data
    archivo = ''
    try:
        if especialidad == "snowflake":
            archivo = "sn_examtopics.json"
        elif especialidad == "dbt":
            archivo = "dbt_examtopics.json"
    except Exception as e:
        st.warning("Ha habido un error, no encuentro los json. " + str(e.args))
    datos = h.open_file(archivo)
    return datos

def menu(conn):
    # User information
    with st.container():
        h.get_user_none()
        space, login = st.columns([3, 1], gap="large")
        user_list_v = (
            conn.cursor()
            .execute(
                "select name from esnowflake.esnowflake_DEV.Dim_Users WHERE name LIKE '%civica%' AND name NOT LIKE '%alumno%' ORDER BY name"
            )
            .fetchall()
        )
        lista_plana = [item[0] for item in user_list_v]
        with space:
            if st.session_state["user"] == None:
                st.warning(
                    "Recuerda elegir tu usuario si quieres que se registren tus avances y poder ver tus progresos"
                )
            else:
                rango_v = (
                    conn.cursor()
                    .execute(
                        f"select rango from esnowflake.esnowflake_DEV.Dim_Users where name  = '{st.session_state['user']}'"
                    )
                    .fetchall()
                )
                rango = rango_v[0][0]
                st.write("")
                if rango == "Iniciado":
                    emoji = "🤓"
                elif rango == "Padawan":
                    emoji = "🤠"
                elif rango == "Maestro":
                    emoji = "🗡️"
                elif rango == "Parra":
                    emoji = "🤖"
                st.write(f"Rango : {rango} {emoji}")
        with login:
            if st.session_state["user"] == None:
                indice = None
            else:
                indice = lista_plana.index(st.session_state["user"])
            useri = st.selectbox("User name :", lista_plana, index=indice)
            st.session_state["user"] = useri
    return useri

def comienzo(conn, especialidad):
    user = h.get_user_none()
    info = ""
    if especialidad == "snowflake":
        info = vf.COMIENZO_SNOWFLAKE + vf.INFO_EXAMEN_SNOWFLAKE
    elif especialidad == "dbt":
        info = vf.COMIENZO_DBT + vf.INFO_EXAMEN_DBT
    menu(conn)
    st.markdown(info)

def practicar(conn, datos, especialidad):
    user = h.get_user_none()
    menu(conn)
    with st.expander("¿Como podría usar esta sección? 🤔"):
        if especialidad == "snowflake":
            st.markdown(vf.USO_SECCION_SNOWFLAKE)
        elif especialidad == "dbt":
            st.markdown(vf.USO_SECCION_DBT)

    Filtros, Preguntas = st.columns([1, 3], gap="large")
    with Filtros:
        st.subheader("Filtros")
        values = st.slider(
            "Seleccione rango de preguntas en el que practicar",
            0,
            len(datos),
            (0, len(datos)),
            step=1,
        )

        secciones_valor = []
        if especialidad == "snowflake":
            secciones = st.multiselect(
                "¿ Que secciones quieren tocar ?",
                vf.SECCIONES_SNOWFLAKE,
            )
        elif especialidad == "dbt":
            secciones = st.multiselect(
                "¿ Que secciones quieren tocar ?",
                vf.SECCIONES_DBT,
            )


        option = st.multiselect(
            "Otros filtros",
            ["Todas", "Sin hacer", "Falladas en exámenes", "Falladas en práctica"],
        )

        preguntas_filtradas = [
            item for item in datos if values[0] <= item["question_number"] <= values[1]
        ]
        if "Todas" not in secciones and secciones != []:
            preguntas_filtradas = [
                item
                for item in preguntas_filtradas
                if item["question_area"] in secciones
            ]

        consulta_preguntas_hechas = f"""SELECT 
        STRING_AGG(CAST(question_id AS NVARCHAR(MAX)), ',') WITHIN GROUP (ORDER BY question_id) AS Hechas, 
        STRING_AGG(CASE WHEN type = 'Examen' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(MAX)) ELSE NULL END, ',') WITHIN GROUP (ORDER BY question_id) AS Examen_falsas, 
        STRING_AGG(CASE WHEN type = 'practicar' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(MAX)) ELSE NULL END, ',') WITHIN GROUP (ORDER BY question_id) AS Practicar_falsas 
        FROM (SELECT DISTINCT question_id, type, is_correct FROM esnowflake.esnowflake_DEV.Fact_Answers WHERE user_nickname = '{user}') AS filtered_answers;"""

        aux_opcion = conn.cursor().execute(consulta_preguntas_hechas).fetchall()

        no_hechas = []
        opcion_examen_falsas = []
        opcion_practicas_falsas = []

        total_question = range(len(datos))

        if "Falladas en exámenes" in option:
            opcion_examen_falsas = ast.literal_eval(aux_opcion[0][1])

        if "Falladas en práctica" in option:
            opcion_practicas_falsas = ast.literal_eval(aux_opcion[0][2])

        if "Sin hacer" in option:
            hechas = aux_opcion[0][0]
            hechas_lista = ast.literal_eval(hechas)
            hechas_int = [int(num) for num in list(hechas_lista)]

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

        question_set = [item["question_number"] for item in preguntas_filtradas]

        if st.toggle("Order aleatorio"):
            random.shuffle(question_set)

    with Preguntas:
        if question_set:
            h.setexam(question_set, datos, "practicar", conn, user)
        else:
            st.write(
                "No hay ninguna pregunta que cuadre con los filtros que has puesto"
            )

def examen(conn, datos):
    user = h.get_user_none()
    exam_mode = 0
    if "exam_mode" not in st.session_state:
        st.session_state["exam_mode"] = exam_mode
    question_set = []
    if "question_set" not in st.session_state:
        st.session_state["question_set"] = question_set

    if st.session_state.get("exam_mode", 0) == 0:
        with st.container():
            menu(conn)
            st.title("Examen")
            st.write("Empieza ajustando los filtros y luego las opciones")
            with st.container():
                Filtros, settings = st.columns(2, gap="large")
                with Filtros:
                    st.subheader("Filtros")
                    values = st.slider(
                        "Seleccione rango de preguntas que pueden caer en el examen",
                        0,
                        len(datos),
                        (0, len(datos)),
                        step=1,
                    )

                    secciones = st.multiselect(
                        "¿ Que secciones quieren tocar ? (Todas por defecto)",
                        vf.SECCIONES_SNOWFLAKE,
                    )

                    option = st.multiselect(
                        "Otros filtros",
                        [
                            "Todas",
                            "Sin hacer",
                            "Falladas en exámenes",
                            "Falladas en práctica",
                        ],
                    )

                    preguntas_filtradas = [
                        item
                        for item in datos
                        if values[0] <= item["question_number"] <= values[1]
                    ]
                    if "Todas" not in secciones and secciones != []:
                        preguntas_filtradas = [
                            item
                            for item in preguntas_filtradas
                            if item["question_area"] in secciones
                        ]

                    consulta_preguntas_hechas = f"""    SELECT
                    STRING_AGG(CASE WHEN question_id IS NOT NULL THEN CAST(question_id AS NVARCHAR(10)) END, ',') WITHIN GROUP (ORDER BY question_id) AS Hechas,
                    STRING_AGG(CASE WHEN type = 'Examen' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(10)) END, ',') WITHIN GROUP (ORDER BY question_id) AS Examen_falsas,
                    STRING_AGG(CASE WHEN type = 'practicar' AND is_correct = 0 THEN CAST(question_id AS NVARCHAR(10)) END, ',') WITHIN GROUP (ORDER BY question_id) AS Practicar_falsas
                    FROM
                    esnowflake.esnowflake_DEV.Fact_Answers where user_nickname = '{user}';"""
                    aux_opcion = (
                        conn.cursor().execute(consulta_preguntas_hechas).fetchall()
                    )

                    no_hechas = []
                    opcion_examen_falsas = []
                    opcion_practicas_falsas = []
                    total_question = range(len(datos))
                    hechas = aux_opcion[0][0]
                    if "Falladas en exámenes" in option:
                        opcion_examen_falsas = ast.literal_eval(aux_opcion[0][1])
                    if "Falladas en práctica" in option:
                        opcion_practicas_falsas = ast.literal_eval(aux_opcion[0][2])
                    if "Sin hacer" in option:
                        no_hechas = list(set(total_question) - set(hechas))
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
                    question_set = [
                        item["question_number"] for item in preguntas_filtradas
                    ]
                    random.shuffle(question_set)

                with settings:
                    st.subheader("Opciones")
                    # Número de preguntas
                    num_questions = st.number_input(
                        "Número de Preguntas",
                        min_value=0,
                        max_value=len(question_set),
                        value=len(question_set),
                        help="El valor máximo viene dictaminado por el filtrado que hagas",
                    )
                    selected_questions = random.sample(question_set, num_questions)
                    st.session_state["question_set"] = selected_questions
                    # Duración del examen
                    exam_duration = st.slider(
                        "Tiempo de Examen (minutos)",
                        min_value=5,
                        max_value=120,
                        value=60,
                    )
                    with st.expander("¿Como es el examen real?"):
                        info = vf.INFO_EXAMEN_SNOWFLAKE
                        st.markdown(info)
                with st.container():
                    espaci1, boton, espaci2 = st.columns(3, gap="large")
                    if num_questions == 0:
                        st.warning(
                            "Tus filtros u opciones resultan en una cantidad de 0 preguntas"
                        )
                    else:
                        with boton:
                            st.button(
                                "Comenzar examen",
                                use_container_width=1,
                                on_click=h.aux_exam,
                                args=("empezar", exam_duration, None),
                            )

    elif st.session_state.get("exam_mode", 0) == 1:
        with st.container():
            question_set = st.session_state["question_set"]
            exam_duration = st.session_state["exam_duration"]
            h.setexam(question_set, datos, "examen", conn, user, exam_time=exam_duration)

    elif st.session_state.get("exam_mode", 0) == 2:
        exam_duration = st.session_state["exam_duration"]
        exam_id_V = (
            conn.cursor()
            .execute(
                f"select coalesce(max(id_exam),1) from esnowflake.esnowflake_DEV.FACT_EXAMS where user_nickname = '{user}' "
            )
            .fetchall()
        )
        exam_id = exam_id_V[0][0]
        st.session_state["review_set"] = []
        user_answers = st.session_state["exam_answers"]
        latest_answers = {}
        # Iterar sobre el array de respuestas
        for answer in user_answers:
            question_number = answer["question_number"]
            timestamp = answer["timestamp"]
            # Comprobar si la pregunta ya tiene una respuesta almacenada
            if (
                question_number not in latest_answers
                or timestamp > latest_answers[question_number]["timestamp"]
            ):
                latest_answers[question_number] = answer
        # Convertir el diccionario de respuestas más recientes en una lista
        filtered_answers = list(latest_answers.values())
        insert = "INSERT INTO esnowflake.esnowflake_DEV.Fact_Answers VALUES "
        values_list = []
        preguntas_acertadas = 0
        preguntas_falladas = 0
        for i, answer in enumerate(filtered_answers):
            question_number = answer["question_number"]
            user_answer = answer["user_answer"]
            if type(user_answer) == str:
                user_answer = [user_answer]
            correcta = datos[question_number - 2]["correct_answer"]
            question = datos[question_number - 2]["question"]
            comofue = comparar_respuestas(user_answer, correcta)
            answer["result"] = comofue
            answer["correcta"] = correcta
            answer["question"] = question
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

            if i != 0:
                values_list.append(", ")
            values_list.append(
                f"({question_number}, '{user}', 'examen', {exam_id}, {int(is_correct)}, {int(is_answered)}, CURRENT_TIMESTAMP)"
            )
            insert += "".join(values_list)

        update = f"""
                update esnowflake.esnowflake_DEV.FACT_EXAMS 
                set 
                end_time = current_timestamp,
                number_of_questions = {len(filtered_answers)},
                number_of_failed_questions = {preguntas_falladas}  ,
                number_of_correct_questions = {preguntas_acertadas}

                where id_exam = {exam_id}
                """
        try:
            aux_exam_insert = st.session_state["aux_exam_insert"]
            if aux_exam_insert:
                conn.cursor().execute(update)
                conn.cursor().execute(insert)
            if "aux_exam_insert" in st.session_state:
                st.session_state["aux_exam_insert"] = 0
        except Exception as e:
            st.write(f"An error occurred: {e} ")
        failed = [answer for answer in filtered_answers if answer["result"] == 0]
        tiempo_invertido_V = (
            conn.cursor()
            .execute(
                f"select DATEDIFF(SECOND, start_time, end_time) from esnowflake.esnowflake_DEV.FACT_EXAMS where id_exam = {exam_id}"
            )
            .fetchall()
        )
        if tiempo_invertido_V:
            tiempo = tiempo_invertido_V[0][0]
        else:
            tiempo = 0
        minutos = tiempo // 60
        segundos = tiempo % 60
        tiempo_formato = f"{minutos} minutos y {segundos} segundos"
        preguntas_no_respondidas = (
            len(filtered_answers) - preguntas_acertadas - preguntas_falladas
        )
        result, grafi = st.columns(2, gap="large")
        with result:
            st.write("")
            st.write("")
            per_acierto = preguntas_acertadas / len(filtered_answers)
            st.metric("Porcentaje de Aciertos", f"{100*per_acierto:.2f}%")
            st.metric("Número de preguntas", f"{len(filtered_answers)}")
            st.metric("Tiempo Total", f"{tiempo_formato}")
            umbral = 0.75
            if per_acierto >= umbral:
                st.success("¡Grande! Has superado el examen.")
            else:
                st.error("Al palo crack, sigue intentándolo. Puedes mejorar.")
        with grafi:
            # Datos para el gráfico
            labels = "Acertadas", "Falladas", "No Respondidas"
            values = [preguntas_acertadas, preguntas_falladas, preguntas_no_respondidas]
            colors = ["green", "red", "blue"]  # Colores para cada sección
            #        Crear un gráfico de donut
            fig = go.Figure(
                data=[
                    go.Pie(labels=labels, values=values, hole=0.5, marker_colors=colors)
                ]
            )
            fig.update_layout(title_text="Resultados")
            # Mostrar el gráfico en Streamlit
            st.plotly_chart(fig)
        with st.expander("Revisar preguntas falladas"):
            for answer in failed:
                st.divider()
                st.write(answer["question_number"])
                st.write(answer["question"])
                st.write("Tu has respondido:")
                st.write(answer["user_answer"])
                st.write("La respuesta correcta era:")
                st.write(answer["correcta"])
        space1, volver, space2 = st.columns([2, 1, 2], gap="large")
        with volver:
            st.button(
                "Volver al inicio",
                use_container_width=1,
                on_click=aux_exam,
                args=(
                    "Inicio",
                    None,
                    None,
                ),
            )
    else:
        with st.container():
            "nada"

def progreso(conn, datos):
    menu(conn)
    user = st.session_state["user"]
    if user == None:
        st.write("Elige tu usuario para ver tu progreso")
    else:
        st.subheader("Avance por secciones")
        questions_info = f"select question_id,is_correct,is_answered,cast(answer_timestamp as date) as Fecha from esnowflake.esnowflake_DEV.FACT_ANSWERS where user_nickname = '{user}' order by answer_timestamp desc"
        questions_info_snow = conn.cursor().execute(questions_info).fetchall()
        questions_info_snow_list = [list(row) for row in questions_info_snow]

        # Define 'columns' antes de usarla para crear el DataFrame
        columns = ["question_id", "is_correct", "is_answered", "Fecha"]

        # Crea el DataFrame una sola vez
        df = pd.DataFrame(questions_info_snow_list, columns=columns)

        # Asegurarse de que la columna 'Fecha' sea de tipo datetime
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.normalize()

        if len(df) == 0:
            st.warning("Haz al menos una pregunta para poder ver esta sección")
        else:
            # Calcular el número de preguntas respondidas por día
            df_resumen = (
                df.groupby("Fecha").size().reset_index(name="Número de Preguntas")
            )
            racha_actual = 0
            fecha_anterior = None
            total_preguntas = len(df)
            total_correctas = df["is_correct"].sum()
            porcentaje_acierto = (total_correctas / total_preguntas) * 100
            df_preguntas = pd.DataFrame(datos)
            total_preguntas_por_seccion = df_preguntas["question_area"].value_counts()
            df_combinado = df.merge(
                df_preguntas[["question_number", "question_area"]],
                left_on="question_id",
                right_on="question_number",
                how="left",
            )
            #   Convertir la lista de preguntas en un DataFrame
            df_preguntas_totales = pd.DataFrame(datos)
            # Crear DataFrame de referencia para todas las secciones
            # Crear DataFrame de referencia para todas las secciones
            df_secciones_referencia = pd.DataFrame(
                df_preguntas_totales["question_area"].unique(),
                columns=["question_area"],
            )
            # Contar el total de preguntas por sección
            total_preguntas_por_seccion = df_preguntas_totales[
                "question_area"
            ].value_counts()
            # Agrupar por 'question_area' en df_combinado y calcular preguntas correctas e incorrectas
            metrics_por_seccion = df_combinado.groupby("question_area")[
                "is_correct"
            ].agg(["sum", lambda x: len(x) - x.sum()])
            metrics_por_seccion.columns = [
                "Preguntas Correctas",
                "Preguntas Incorrectas",
            ]
            # Realizar un merge con el DataFrame de referencia para incluir todas las secciones
            metrics_final = df_secciones_referencia.merge(
                metrics_por_seccion, on="question_area", how="left"
            )
            # Rellenar valores NaN con 0
            metrics_final.fillna(0, inplace=True)
            # Calcular preguntas no vistas correctamente
            metrics_final["Preguntas No Vistas"] = (
                metrics_final["question_area"].map(total_preguntas_por_seccion)
                - metrics_final["Preguntas Correctas"]
                - metrics_final["Preguntas Incorrectas"]
            )
            # Mostrar el resultado en Streamlit sin índice
            # st.write(metrics_final.set_index('question_area'))
            # Definir colores personalizados
            colors = ["green", "red", "blue"]
            # Crear un donut chart para cada 'question_area'
            c1, c2, c3, c4, c5, c6 = st.columns(6, gap="small")
            column_counter = 0
            # Mostrar leyendas una sola vez arriba de las columnas
            for index, row in metrics_final.iterrows():
                labels = [
                    "Preguntas Correctas",
                    "Preguntas Incorrectas",
                    "Preguntas No Vistas",
                ]
                values = [
                    row["Preguntas Correctas"],
                    row["Preguntas Incorrectas"],
                    row["Preguntas No Vistas"],
                ]
                # Crear la gráfica de donut
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=labels, values=values, hole=0.5, marker_colors=colors
                        )
                    ]
                )
                # Actualizar el diseño para mejorar la presentación
                fig.update_layout(
                    title_text=f" {row['question_area']}",
                    showlegend=False,
                    # Eliminar la anotación para quitar el título del medio del donut
                    # annotations=[dict(text=row['question_area'], x=0.5, y=0.5, font_size=20, showarrow=0)]
                )
                # Determinar en qué columna mostrar la gráfica
                if column_counter == 0:
                    with c1:
                        st.plotly_chart(fig, use_container_width=1)
                elif column_counter == 1:
                    with c2:
                        st.plotly_chart(fig, use_container_width=1)
                elif column_counter == 2:
                    with c3:
                        st.plotly_chart(fig, use_container_width=1)

                elif column_counter == 3:
                    with c4:
                        st.plotly_chart(fig, use_container_width=1)

                elif column_counter == 4:
                    with c5:
                        st.plotly_chart(fig, use_container_width=1)
                else:
                    with c6:
                        st.plotly_chart(fig, use_container_width=1)
                # Actualizar el contador de columnas y resetear si es necesario
                column_counter = column_counter + 1

            secciones, exams = st.columns([2, 1], gap="large")
            with secciones:
                questions_info = f"select question_id,is_correct,is_answered,cast(answer_timestamp as date) as Fecha from esnowflake.esnowflake_DEV.FACT_ANSWERS where user_nickname = '{user}' order by answer_timestamp desc"
                questions_info_snow = conn.cursor().execute(questions_info).fetchall()
                questions_info_snow_list = [list(row) for row in questions_info_snow]
                columns = ["question_id", "is_correct", "is_answered", "Fecha"]
                df = pd.DataFrame(questions_info_snow_list, columns=columns)
                # Asegurarse de que la columna 'Fecha' sea de tipo datetime
                df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.normalize()
                # Crear un DataFrame de pandas
                # Calcular el número de preguntas respondidas por día
                df_resumen = (
                    df.groupby("Fecha").size().reset_index(name="Número de Preguntas")
                )
                racha_actual = 0
                fecha_anterior = None
                total_preguntas = len(df)
                total_correctas = df["is_correct"].sum()
                porcentaje_acierto = (total_correctas / total_preguntas) * 100

                for fecha in reversed(df_resumen["Fecha"]):
                    if (
                        fecha_anterior is None
                        or fecha_anterior - pd.Timedelta(days=1) == fecha
                    ):
                        racha_actual += 1
                        fecha_anterior = fecha
                    else:
                        break
                metricas, timeline = st.columns([1, 2], gap="small")

                with metricas:
                    st.subheader("Estudio total")
                    st.write("")
                    st.metric("Racha actual de días de estudio:", racha_actual)
                    st.metric("Total de preguntas realizadas", total_preguntas)
                    st.metric("Porcentaje de acierto", f"{porcentaje_acierto:.2f}%")

                with timeline:
                    # Crear el gráfico de barras con Plotly
                    fig = px.bar(
                        df_resumen,
                        x="Fecha",
                        y="Número de Preguntas",
                        title="Preguntas Respondidas por Día",
                    )
                    # Formatear el eje x para mostrar solo las fechas (sin horas)
                    fig.update_xaxes(
                        dtick="D1",  # Establece los intervalos de las marcas en un día
                        tickformat="%b %d, %Y",  # Formato de la fecha: 'Mes día, Año'
                    )
                    # Mostrar el gráfico en Streamlit
                    st.plotly_chart(fig, use_container_width=1)

            with exams:
                st.subheader("Historial de exámenes")
                # Datos ficticios para los tres últimos exámenes
                exam_info = f"select top 6 id_exam,start_time,duration_minutes,number_of_questions,number_of_correct_questions,number_of_failed_questions from esnowflake.esnowflake_DEV.FACT_EXAMS where user_nickname = '{user}' order by start_time desc"
                exam_info_snow = conn.cursor().execute(exam_info).fetchall()
                exam_info_snow_list = [list(row) for row in exam_info_snow]
                columns = [
                    "id_exam",
                    "start_time",
                    "duration_minutes",
                    "number_of_questions",
                    "number_of_correct_questions",
                    "number_of_failed_questions",
                ]
                df = pd.DataFrame(exam_info_snow_list, columns=columns)

                # Replace None with 0 in relevant columns
                df["number_of_questions"] = df["number_of_questions"].fillna(0)
                df["number_of_correct_questions"] = df[
                    "number_of_correct_questions"
                ].fillna(0)
                df["number_of_failed_questions"] = df[
                    "number_of_failed_questions"
                ].fillna(0)

                # Colores para las categorías
                colores = ["green", "red", "blue"]

                # Tamaño del gráfico
                ancho, alto = (
                    350,
                    350,
                )  # Puedes ajustar estos valores según tus necesidades
                if len(df) == 0:
                    st.write("Aún no has hecho exámenes")
                for i, examen in df.iterrows():
                    # Calcular el número de preguntas en blanco
                    num_questions = (
                        examen["number_of_questions"]
                        if pd.notnull(examen["number_of_questions"])
                        else 0
                    )
                    en_blanco = (
                        examen["number_of_questions"]
                        - (examen["number_of_correct_questions"] or 0)
                        - (examen["number_of_failed_questions"] or 0)
                    )
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

                    # Calcular el score y el mensaje a mostrar
                    if examen["number_of_questions"] == 0:
                        score = 0
                    else:
                        score = (
                            examen["number_of_correct_questions"]
                            / examen["number_of_questions"]
                        )
                    examen["start_time"] = pd.to_datetime(examen["start_time"])
                    timestamp = (
                        examen["start_time"].strftime("%Y-%m-%d %H:%M")
                        if pd.notnull(examen["start_time"])
                        else "Desconocido"
                    )
                    mensaje = f"{'APROBADO' if score >= 0.75 else 'SUSPENSO'} {100*score:.2f}%     -----{'🟢' if score >= 0.75 else '🔴'}-----      {timestamp}"

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

def parreitor(conn):
    menu(conn)
    st.title("Parreitor-3000")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Alguna duda de Snowflake ? "):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Obtener la respuesta del asistente utilizando la función 'chat'
        response = chat(prompt)

        # Mostrar la respuesta del asistente
        with st.chat_message("assistant"):
            st.markdown(response)

        # Añadir respuesta del asistente a la sesión
        st.session_state.messages.append({"role": "assistant", "content": response})
