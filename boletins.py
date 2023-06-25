import streamlit as st
import pandas as pd
from pymongo import MongoClient
from cader import normalizador


try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec4 = st.secrets["colec4"]
  colec3 = st.secrets["colec3"]
  colec1 = st.secrets["colec1"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = os.environ["db1"]
  colec4 = os.environ["colec4"]
  colec3 = os.environ["colec3"]
  colec1 = os.environ["colec1"]

cluster = MongoClient(dbcred)
db = cluster[db1]


@st.cache_data(ttl=3600)
def get_data_at_db_1():
    para_componentes = db[colec3].find_one({"_id": colec1}).get('matriz')
    return para_componentes

st.cache_resource(ttl=3600)
def find_std_grades(student_id):
    return db[colec4].find({"matrícula": student_id}, {"_id": 0})

@st.cache_resource(ttl=3600)
def get_me(colec, rm):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    std = db[colec].find_one({'matrícula': rm})
    return std

def bol(rm):
    selected_student = get_me(colec1, rm)
    turma = selected_student['turma']
    st.markdown(f"##### Estudante: {selected_student['estudante']}")
    st.markdown(f"##### Matrícula: {selected_student['matrícula']}")
    st.markdown(f"##### Turma: {turma}")
    st.markdown(f"##### Turno: {selected_student['turno']}")
    st.divider()
    st.markdown("## BOLETIM")
    my_matters = get_data_at_db_1().get(turma)
    their_grades = pd.DataFrame.from_dict(find_std_grades(rm))
    their_grades = their_grades[['componente', 'unidade', 'med', 'professor']]
    st.dataframe(their_grades, use_container_width=True)
    their_grades = their_grades[['componente', 'unidade', 'med']]
    their_grades = their_grades.replace('FV', 0)
    pivot = pd.pivot_table(their_grades, index='componente', columns='unidade', values='med')
    new_pivot = pivot[pivot.index.isin(my_matters)]
    new_pivot = new_pivot.fillna('FV')
    if 'TF' in turma or 'TJ' in turma:
        new_pivot = new_pivot.applymap(normalizador)

    st.dataframe(new_pivot, use_container_width=True)
    st.table(new_pivot)


