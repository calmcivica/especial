import re
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import tracemalloc
import numpy as np
from pandas import DataFrame
import sql_especialidad.cases_exercises as ce
tracemalloc.start()

# run_query function adapted for SQLAlchemy engine
def run_query(engine, query1):
    message = ""
    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                try:
                    connection.execute(text(query1))
                    message = "SQL Query executed successfully."
                    transaction.commit()
                    connection.close()
                    return message  # Return the DataFrame containing the results
                except:
                    transaction.rollback()
                    raise

    except SQLAlchemyError as e:
        return st.error("Error Run query: " + clean_error_message(str(e)))


def run_query_list(query1, engine, solution=None):
    try:
        query_list = list(set(st.session_state["input_list"]))
        with engine.connect() as connection:
            with connection.begin() as transaction:
                if len(query_list) > 1 and solution is None:
                    try:
                        for query in query_list:
                            message = connection.execute(text(query))
                            st.write(message)
                    except Exception:
                        st.error("Error al recopilar tablas temporales: " + clean_error_message(str(e)))
                    df = connection.execute(text(query1))
                    df1_1 = DataFrame(df.fetchall())
                else:
                    df = connection.execute(text(query1))
                    df1_1 = DataFrame(df.fetchall())
                transaction.commit()
        return df1_1

    except SQLAlchemyError as e:
        return st.error("Error Run query list: " + clean_error_message(str(e)))


def do_you_need(element, engine):
    # Ensure that input_list is initialized as a list in session_state
    if "input_list" not in st.session_state:
        st.session_state["input_list"] = []

    message = ""
    agree = st.checkbox(f"Do you need a {element}?")
    if agree:
        query_proc = st.text_area(f"Enter SQL {element}:", height=200)
        if st.button(f"Create {element}", key=f"{element}"):
            if query_proc.endswith(";"):
                try:
                    message = run_query(engine, query_proc[:-1])
                    if str(element) == "Temporary table":
                        # It's added to the list to prelaunch before running other queries
                        st.session_state["input_list"].append(query_proc[:-1])
                        st.session_state["input_list"] = list(set(st.session_state["input_list"]))
                    if "Ya hay un objeto con el nombre" in message:
                        st.warning("Temporary table created with that name")
                    else:
                        st.warning(message)
                except SQLAlchemyError as e:
                    st.error(f"Error generating the {element}" + clean_error_message(str(e)))
                except Exception as e:
                    pass
            else:
                st.error('You have to finish the sentence with a ";"')


def uncheck_other_weeks(current_week):
    cases = ["Case 1", "Case 2", "Case 3", "Case 4"]
    for case in cases:
        if case != current_week:
            st.session_state[case] = False
    counter_reset()

def date_control(engine):
    query1 = 'SELECT numero FROM CONTROL.DATE_CONTROL'
    df_num = run_query_list(query1,engine)
    #cogemos el primer valor de la primera columna
    number = int(df_num.iloc[0,0])
    return number

def display_cases_exercises(numero):
    try:
        st.subheader("Choose case")
        option_w, option = None, None
        # Define checkboxes for each case
        cases = ce.classify_number_cases(numero)
        listados = ce.classify_number_exercises(numero)
        week_aux = ""
        if cases != ["None"]:
            for i, case in enumerate(cases):
                if case not in st.session_state:
                    st.session_state[case] = False
                if week_aux not in st.session_state:
                    st.session_state[week_aux] = False
                agree_sem = st.checkbox(
                    case,
                    value=st.session_state[case],
                    key=case,
                    on_change=uncheck_other_weeks,
                    args=(case,),
                )
                if agree_sem:
                    option_w = case
                    option = st.selectbox(
                        "Select your exercise:",
                        listados[i],
                        key=f"{case}_select",
                        on_change=counter_reset,
                    )
                    break  # Exit loop once the selected case is processed
            return option_w, option
        else:
            st.write("No hay ejercicios disponibles!")
            return None, None
    except Exception:
        pass

def enunciado(engine, option):
    try:
        # Adjusted to use pd.read_sql_query with SQLAlchemy engine
        enunciado = f"EXEC EJERCICIOS.{option}_e"
        st.write("-- **QUESTION** --")
        with engine.begin() as conn:
            result = conn.execute(text(enunciado)).fetchone()
            message = result[0] if result else "No message returned"
            st.write(message)
    except Exception as e:
        st.write("Error exercise title: " + clean_error_message(str(e)))

def getting_parameters(query1, character):
    try:
        # Split the string into parts using commas and line breaks as delimiters.
        parts = [part.strip() for part in query1.replace("\n", ",").split(",")]

        # Extract and clean values after "=".
        sentence_list = [
            part.split(character)[1].strip().strip("'")
            for part in parts
            if character in part
        ]
        return sentence_list
    except Exception:
        pass

def especiales(option, lista, valores=False):
    try:
        if option == "Ejercicio3_3":
            if valores:
                lista = [123, 5]
            return ejercicio3_3(lista)
        if option == "Ejercicio3_4" or option == "Ejercicio3_5":
            if valores:
                lista = [1, 3, 3]
            return ejercicio3_4_5(option, lista)
        elif option == "Ejercicio4_1":
            if valores:
                lista = ["SQL_EN_LLAMAS", "CASE04", "SALES"]
            return ejercicio4_1(lista)
        elif option == "Ejercicio4_5":
            if valores:
                lista = [2, 6]
            return ejercicio4_5(lista)
    except Exception:
        pass


def ejercicio3_3(lista):
    try:
        if len(lista) > 2 or not str(lista[-1]).endswith("OUTPUT;"):
            return f"""DECLARE @OutputMessage VARCHAR(MAX);
    EXEC EJERCICIOS.EJERCICIO3_3 @customer_id = {lista[0]}, @search_month = {lista[1]}, @message = @OutputMessage OUTPUT;
    SELECT @OutputMessage AS ResultMessage;"""
        else:
            st.warning(
                f"""To make work the solution of this exercise, the solution needs these parameters:
                        * @customer_id INT
                        * @search_month INT
                        * @message = @OutputMessage OUTPUT
                        """
            )
    except Exception:
        pass


def ejercicio3_4_5(option, lista):
    try:
        if len(lista) == 4 or not str(lista[-1]).endswith("OUTPUT;"):
            return f"""DECLARE @OutputMessage VARCHAR(MAX);
    EXEC EJERCICIOS.{option} @cliente = {lista[0]}, @mes = {lista[1]}, @movimiento = {lista[2]}, @message = @OutputMessage OUTPUT;
    SELECT @OutputMessage AS ResultMessage;"""
        else:
            st.warning(
                f"""To make work the solution of this exercise, the solution needs these parameters:
                    * @cliente INT
                    * @mes INT
                    * @movimiento INT
                    * @message = @OutputMessage OUTPUT
                    """
            )
    except Exception:
        pass

def ejercicio4_1(lista):
    try:
        if len(lista) == 3 and not str(lista[-1]).endswith("OUTPUT;"):
            return f"""EXEC [EJERCICIOS].[EJERCICIO4_1] @DB = {lista[0]}, @ESQUEMA = {lista[1]}, @TABLA = {lista[2]};"""
        else:
            st.warning(
                f"""To make work the solution of this exercise, the solution needs these parameters:
                    * @DB NVARCHAR(128)
                    * @ESQUEMA NVARCHAR(128)
                    * @TABLA NVARCHAR(128)
                    """
            )
    except Exception:
        pass


def ejercicio4_5(lista):
    try:
        if len(lista) == 2 and not str(lista[-1]).endswith("OUTPUT;"):
            return f"""EXEC [EJERCICIOS].[EJERCICIO4_5] @CAT_ID = {lista[0]}, @SEG_ID = {lista[1]};"""
        else:
            st.warning(
                f"""To make work the solution of this exercise, the solution needs these parameters:
                    * @CAT_ID INT
                    * @SEG_ID INT
                    """
            )
    except Exception:
        pass


def clean_error_message(error_message):
    try:
        # Broadly remove leading technical details, including error codes and SQL Server mentions
        cleaned_message = re.sub(r"^.*?\[SQL Server\]", "", error_message)

        # Remove leading and trailing characters that are not part of the main error message
        # This includes parentheses, quotes, and any SQL-related suffixes that may follow
        cleaned_message = re.sub(r"^\s*['\"]|['\"],?\s*$", "", cleaned_message)

        # Attempt to isolate the main error message by removing any trailing SQL execution details or URLs
        cleaned_message = re.split(r" \(", cleaned_message, 1)[
            0
        ]  # Split at the first occurrence of " ("

        return cleaned_message.strip()
    except Exception:
        pass


def counter_reset():
    st.session_state["counter"] = 0
    st.session_state["input_list"] = []


def counter_add_1():
    st.session_state["counter"] += 1


def show_result():
    st.session_state["show"] = 0


def show_result_1():
    st.session_state["show"] = 1


def show_result_2():
    st.session_state["show"] = 2


def show_tables(engine, query1, option, comparation):
    try:
        if query1.endswith(";"):
            query1 = query1[:-1].upper()
            df1_1 = None
            df1_2 = None
            df2_1 = None
            query2 = None
            error = ""

            try:
                # ESPECIALES
                listado_especiales = [
                    "Ejercicio3_3",
                    "Ejercicio3_4",
                    "Ejercicio3_5",
                    "Ejercicio4_1",
                    "Ejercicio4_5",
                ]
                if option in listado_especiales and comparation:
                    lista = getting_parameters(query1, "=")
                    query2 = especiales(option, lista)
                # ########################################################################
                # ## PROCEDURES:
                if query1.startswith("EXEC") or query1.startswith("DECLARE"):
                    with engine.connect() as connection:
                        with connection.begin() as transaction:
                            query1 = query1 + ";"
                            df = connection.execute(text(query1))
                            try:
                                df1_2 = pd.DataFrame(df.fetchall())
                            except Exception as e:
                                error = str(e)
                                if error == ("list index out of range"):
                                    error = "Check your result, because it seems that [SQL SERVER] doesn`t like your query :tired_face:"
                                st.error(clean_error_message("Error user: " + error))
                            transaction.commit()
                            connection.close()
                ########################################################################
                ## NO PROCEDURES:
                if query2 is None:
                    query2 = "EXEC EJERCICIOS." + option
                df1_1 = run_query_list(query1, engine)
            except Exception as e:
                error = str(e)
                if error == ("list index out of range"):
                    error = "Check your result, because it seems that [SQL SERVER] doesn`t like your query :tired_face:"
                st.error(clean_error_message("Error user: " + error))
            try:
                # Show the DataFrames
                if df1_1 is not None:
                    st.write(":blue[User table:]")
                    # replacing the None for nulls
                    df1_1 = df1_1.where((pd.notna(df1_1)), "null")
                    # if table columns with same name replace
                    df1_1 = rename_duplicate_columns(df1_1)
                    st.write(df1_2 if df1_2 is not None else df1_1)  # User's result
                if comparation:
                    with engine.connect() as connection:
                        with connection.begin() as transaction:
                            df = connection.execute(text(query2))
                            df2_1 = pd.DataFrame(df.fetchall())
                            transaction.commit()
                            connection.close()
            except Exception as e:
                if df1_1 is None and query2 is None:
                    st.error("There is an error in the SOLUTION table: " + str(e))
                # else:
                # st.error(clean_error_message("Error user: " + error))
            finally:
                if df2_1 is None and option in listado_especiales:
                    # default solution
                    try:
                        if st.session_state["counter"] > 3:
                            query2 = especiales(option, [], True)
                            st.warning(str(query2))
                            with engine.connect() as connection:
                                with connection.begin() as transaction:
                                    df = connection.execute(text(query2))
                                    df2_1 = pd.DataFrame(df.fetchall())
                                    transaction.commit()
                                    connection.close()
                    except Exception as e:
                        error = str(e)
                        if error == ("list index out of range"):
                            error = "Check your result, because it seems that [SQL SERVER] doesn`t like your query :tired_face:"
                        st.error(clean_error_message("Error user: " + error))
                if df2_1 is not None and df1_1 is not None:
                    if st.session_state["counter"] > 3:
                        st.write("Do you need some help? :angel:")
                        st.write("-> :green[Solution table:]")
                        st.write(df2_1)  # Solution
                    # Check if the DataFrames have the same number of rows
                    if len(df1_1) != len(df2_1):
                        st.warning(" --- COMMENTS --- ")
                        st.write("The tables have a :red[DIFFERENT number of rows].")
                    else:
                        st.write("The tables have the :green[SAME number of rows].")
                        # Check if the DataFrames have the same number of columns
                        if len(df1_1.columns) != len(df2_1.columns):
                            st.write("The tables have :red[DIFFERENT number of columns].")
                        else:
                            st.write("The tables have :green[SAME number of columns].")
                            # Clean the data of whitespace
                            df1_1 = trim_normalize_and_sentence_case_all_columns(df1_1)
                            df2_1 = trim_normalize_and_sentence_case_all_columns(df2_1)
                            # Compare ignoring column names
                            arr1 = df1_1.to_numpy()
                            arr2 = df2_1.to_numpy()
                            # Perform the comparison
                            differences = np.not_equal(arr1, arr2)
                            diff_index = np.any(differences, axis=1)
                            # Extract rows from the original DataFrame (df1_1 or df2_1) where differences are found
                            diff_values = df1_1.iloc[diff_index]
                            # Process and output the differences
                            if not diff_values.empty:
                                st.write(":red[The tables have some differences].")
                                if len(diff_values) > 1:
                                    st.write("  -> These are the rows that diverge:")
                                else:
                                    st.write("  -> This is the row that differs:")
                                # You can now work with `diff_values` DataFrame to highlight or process differences
                                st.write(diff_values)
                            else:
                                st.write(":green[The tables are identical.]")
                                st.success("EXERCISE CORRECT!")
                st.session_state["input_list"] = []
                show_result()
        else:
            st.error('You have to finish the sentence with a ";"')
            show_result()
    except Exception:
        pass

def trim_normalize_and_sentence_case_all_columns(df):
    """
    Trim whitespace, replace carriage returns with newlines, remove consecutive newlines,
    and convert to sentence case from each value across all series in dataframe.
    """

    def to_sentence_case(s):
        # Split into sentences, then strip and lowercase each sentence,
        # finally capitalize the first letter of each.
        return ". ".join(sentence.strip().capitalize() for sentence in s.split("."))

    def trim_replace_and_sentence_case(x):
        if isinstance(x, str):
            # Trim whitespace at both ends
            x = x.strip()
            # Replace carriage returns (\r) with newlines (\n), then remove consecutive newlines
            x = x.replace("\r", "\n").replace("\n\n", "\n")
            # Convert to sentence case
            x = to_sentence_case(x)
        return x

    # Use applymap to apply the function to each element of the dataframe
    return df.map(trim_replace_and_sentence_case)


def rename_duplicate_columns(df):
    # Keep track of the count of duplicate column names
    col_counts = {}
    # List to hold the new column names
    new_columns = []

    for col in df.columns:
        if col in col_counts:
            # If the column name is already in our count dict, increment its count
            col_counts[col] += 1
            # Rename the column with its count value appended
            new_col_name = f"{col}_{col_counts[col]}"
        else:
            # If it's the first time we've seen this column name, add it to the dict
            col_counts[col] = 1
            new_col_name = col  # The first occurrence keeps its name

        new_columns.append(new_col_name)

    # Assign the new column names to the DataFrame
    df.columns = new_columns
    return df
