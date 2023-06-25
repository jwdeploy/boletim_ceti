import streamlit as st
import time
import jwt
from Ocorrências_Extra_Classe import occur
from boletins import bol
from faltômetro import faltas


def logador(external_fucntion=lambda x: None, data=None):
    series_data = data['access_token'][0]
    std_data = eval(data['std'][0])
    full_name = std_data['nome_civil']
    rm = std_data['matrícula']
    login_data = series_data
    decoded_token = jwt.decode(
        login_data,
        algorithms=["HS256"],
        options={"verify_signature": False}
    )
    if decoded_token['exp'] < time.time():
        st.write("falha na autenticação. Por favor, faça login novamente.")
        st.write("[login](https://cetibol-edabcdbe191e.herokuapp.com/)")
        st.stop()
    external_fucntion(full_name, rm)


def main(full_name, rm):
    st.markdown("# BOLETIM, FALTÔMETRO, JUSTIFICATIVAS E OCORRÊNCIAS EXTRA-CLASSE")
    st.markdown(
        f'### {full_name}, bem vind@ AOS SEUS RELATÓRIOS!'
    )
    if st.experimental_get_query_params():
        st.divider()
        bol(rm)
        st.divider()
        occur(rm)
        st.divider()
        faltas(rm)

logador(external_fucntion=main, data=st.experimental_get_query_params())