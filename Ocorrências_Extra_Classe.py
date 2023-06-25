import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
import pytz

current_year = date.today().year


def get_date_and_time():
    tz = pytz.timezone('America/Sao_Paulo')
    date = datetime.now(tz)
    formatted_date = date.strftime('%d-%m-%Y')
    time_string = date.strftime('%H:%M:%S')
    print(formatted_date, time_string)
    return formatted_date, time_string


import time
# import requests
from pymongo import MongoClient
import pandas as pd


try:
    dbcred = st.secrets["dbcred"]
    db1 = st.secrets["db1"]
    colec1 = st.secrets["colec1"]
    oc = st.secrets['oc']

except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    colec1 = os.environ["colec1"]
    oc = os.environ['oc']



@st.cache_resource(ttl=3600)
def get_me(colec, rm):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    std = db[colec].find_one({'matrícula': rm})
    return std

@st.cache_resource(ttl=3600)
def get_data_all_occurrences(oc_, rm):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    occurrences = list(
        db[oc_].find({'matrícula': rm})
    )
    return occurrences

def show_student_occurrences(rm):
    selected_student = get_me(colec1, rm)

    student_occurrences = pd.DataFrame(get_data_all_occurrences(oc, rm))
    if student_occurrences.empty:
        st.markdown("### NADA CONSTA!")
    else:
        student_occurrences['selectedDate'] = pd.to_datetime(student_occurrences['selectedDate'])
        student_occurrences['data'] = student_occurrences['selectedDate'].dt.strftime('%d/%m/%Y   %H:%M:%S')
        st.write("Lista de Ocorrências:")
        student_occurrences = student_occurrences.drop(columns=[
            '_id',
            'serie',
            'selectedDate',
            "matrícula",
            "estudante", 
            "serie",
            "turma",
            "turno"
        ])
        student_occurrences = student_occurrences.set_index('data')
        student_occurrences = student_occurrences.replace({True: "sim", False: "-", "True": "sim", "False": "-"})
        st.table(student_occurrences.T)



def occur(rm):
    st.markdown("## RELATÓRIOS DE OCORRÊNCIAS EXTRA-CLASSE")
    show_student_occurrences(rm)


