import streamlit as st

listado_1 = [
    "Ejercicio1_1",
    "Ejercicio1_2",
    "Ejercicio1_3",
    "Ejercicio1_4",
    "Ejercicio1_5"
]
listado_2 = [
    "Ejercicio2_1",
    "Ejercicio2_2",
    "Ejercicio2_3",
    "Ejercicio2_4",
    "Ejercicio2_5",
]
listado_3 = [
    "Ejercicio3_1",
    "Ejercicio3_2",
    "Ejercicio3_3",
    "Ejercicio3_4",
    "Ejercicio3_5",
]
listado_4 = [
    "Ejercicio4_1",
    "Ejercicio4_2",
    "Ejercicio4_3",
    "Ejercicio4_4",
    "Ejercicio4_5",
]

def classify_number_casos(numero):
    if numero >= 101 and numero <= 107:
        return ["Caso 1"]
    elif 108 <= numero <= 121:
        return ["Caso 1", "Caso 2"]
    elif 122 <= numero <= 136:
        return ["Caso 1", "Caso 2", "Caso 3"]
    elif 137 <= numero <= 161:
        return ["Caso 1", "Caso 2", "Caso 3", "Caso 4"]
    else:
        return ["None"]
    

def classify_number_exercises(numero):
    listados = []
    ######################
    # CASE 01 --> 101-108
    ######################   
    if  numero == 101 and numero < 110:
        list_1 = ["Ejercicio1_1"]
        listados = [list_1]
        return listados
    elif 102 <= numero < 103:
        list_1 = ["Ejercicio1_1", "Ejercicio1_2"]
        listados = [list_1]
        return listados
    elif 103 < numero < 104:
        list_1 = ["Ejercicio1_1", "Ejercicio1_2", "Ejercicio1_3"]
        listados = [list_1]
        return listados
    elif 104 <= numero < 105:
        list_1 = ["Ejercicio1_1", "Ejercicio1_2", "Ejercicio1_3", "Ejercicio1_4"]
        listados = [list_1]
        return listados
    elif 105 <= numero < 108:
        listados = [listado_1]
        return listados
    ######################
    # CASE 02 --> 108-121
    ######################
    elif 108 <= numero < 110:
        list_2 = ["Ejercicio2_1"]
        listados = [listado_1, list_2]
        return listados
    elif 110 <= numero < 112:
        list_2 = ["Ejercicio2_1", "Ejercicio2_2"]
        listados = [listado_1, list_2]
        return listados
    elif 112 <= numero < 114:
        list_2 = ["Ejercicio2_1", "Ejercicio2_2", "Ejercicio2_3"]
        listados = [listado_1, list_2]
        return listados
    elif 114 <= numero < 119:
        list_2 = ["Ejercicio2_1", "Ejercicio2_2", "Ejercicio2_3", "Ejercicio2_4"]
        listados = [listado_1, list_2]
        return listados
    elif 119 <= numero < 121:
        listados = [listado_1, listado_2]
        return listados
    ######################
    # CASE 03 --> 122-136
    ######################
    if 121 <= numero < 123:
        list_3 = [
            "Ejercicio3_1"
        ]
        listados = [listado_1, listado_2, list_3]
        return listados
    if 124 <= numero < 126:
        list_3 = [
            "Ejercicio3_1",
            "Ejercicio3_2"
        ]
        listados = [listado_1, listado_2, list_3]
        return listados
    if 126 <= numero < 129:
        list_3 = [
            "Ejercicio3_1",
            "Ejercicio3_2",
            "Ejercicio3_3"
        ]
        listados = [listado_1, listado_2, list_3]
        return listados
    if 129 <= numero < 132:
        list_3 = [
            "Ejercicio3_1",
            "Ejercicio3_2",
            "Ejercicio3_3",
            "Ejercicio3_4"
        ]
        listados = [listado_1, listado_2, list_3]
        return listados
    if 132 <= numero < 137:
        listados = [listado_1, listado_2, listado_3]
        return listados
    ######################
    # CASE 04 --> 137-161
    ######################
    if numero < 138:
        list_4 = [
            "Ejercicio4_1"
        ]
        listados = [listado_1, listado_2, listado_3, list_4]
        return listados
    if 138 <= numero < 140:
        list_4 = [
            "Ejercicio4_1",
            "Ejercicio4_2"
        ]
        listados = [listado_1, listado_2, listado_3, list_4]
        return listados
    if 140 <= numero < 144:
        list_4 = [
            "Ejercicio4_1",
            "Ejercicio4_2",
            "Ejercicio4_3"
        ]
        listados = [listado_1, listado_2, listado_3, list_4]
        return listados
    if 144 <= numero < 147:
        list_4 = [
            "Ejercicio4_1",
            "Ejercicio4_2",
            "Ejercicio4_3",
            "Ejercicio4_4"
        ]
        listados = [listado_1, listado_2, listado_3, list_4]
        return listados
    if 147 <= numero < 161:
        listados = [listado_1, listado_2, listado_3, listado_4]
        return listados
    else:
        return ["Outside Range"]