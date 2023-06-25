#  a code for open 2023frequencia.json utf-8 file and convert it to python dict
import json 
from datetime import datetime, timedelta
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import numpy as np



try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec1 = st.secrets["colec1"]
  colec5 = st.secrets["colec5"]
  colec6 = st.secrets["colec6"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = os.environ["db1"]
  colec1 = os.environ["colec1"]
  colec5 = os.environ["colec5"]
  colec6 = os.environ["colec6"]

cluster = MongoClient(dbcred)
db = cluster[db1]

# with open('2023frequencia.json', encoding='utf-8') as f:
#     data = json.load(f)
# with open('2023@jus.json', encoding='utf-8') as f:
#     data = json.load(f)
# with open('2023@1124856.json', encoding='utf-8') as f:
#     data = json.load(f)

unidades = {
    'I': {
        'inicio': '06-02-2023',
        'fim': '05-05-2023'
    },
    'II': {
        'inicio': '08-05-2023',
        'fim': '31-08-2023'
    },
    'III': {
        'inicio': '01-09-2023',
        'fim': '15-12-2023'
    },
}
def faltas(rm):
    unidades_dr = eval(str(unidades))
    for unidade, datas in unidades.items():
        inicio = datetime.strptime(datas['inicio'], '%d-%m-%Y')
        fim = datetime.strptime(datas['fim'], '%d-%m-%Y')
        fim += timedelta(days=1)
        daterange = pd.date_range(start=inicio, end=fim, inclusive='both')
        unidades_dr[unidade] = daterange

    
    def get_who_miss(c_row):
        to_return = {}
        try:
            par = ~pd.DataFrame(c_row['frequência']).set_index('matrícula')['isPresent']
        except KeyError:
            return np.nan
        middle = (par[par]*len(c_row['horários'])).to_dict()
        for rm, nfaltas in middle.items():
            inner = {}
            inner['matrícula'] = rm
            inner['faltas'] = nfaltas
            inner['componente'] = c_row['componente']
            inner['date'] = c_row['date']

            to_return.update({str(rm)+'_'+c_row['created_at']:inner})
        return to_return if to_return else np.nan

    @st.cache_data(ttl=86_400)
    def get_data_at_db():
        collection1 = db[colec1] 
        all_stds = pd.DataFrame(list(collection1.find()))
        collection2 = db[colec5]
        freq_all = pd.DataFrame(list(collection2.find()))
        collection3 = db[colec6]
        all_jus = pd.DataFrame(list(collection3.find()))
        return all_stds, freq_all, all_jus

    @st.cache_data(ttl=86_400)
    def make_big_df(with_who_missed_):
        for_df  = {}
        for item in with_who_missed_.apply(get_who_miss, axis=1).dropna().values:
            for_df.update(item)
        df = pd.DataFrame(for_df).T
        return df

    all_stds, freq_all, all_jus = get_data_at_db()
    st.markdown("## MINHAS JUSTIFICATIVAS")
    jus_df =all_jus[all_jus['matrícula'].isin([rm])]
    if jus_df.empty:
        st.markdown("### NADA CONSTA!")
    else:
        jus_df = jus_df[['data_init', 'data_end', 'num_dias_justificados', 'tem_atestado', 'justificativa']]
        jus_df["Nº de dias justificados"] = jus_df["num_dias_justificados"].astype(int)
        jus_df["Possui atestado?"] = jus_df["tem_atestado"].astype(bool).apply(lambda x: 'Sim' if x else 'Não')
        jus_df["data incial"] = jus_df["data_init"].astype(str)
        jus_df["data final"] = jus_df["data_end"].astype(str)
        jus_df.index = jus_df.reset_index().index + 1
        st.dataframe(jus_df[['data incial', 'data final', 'Nº de dias justificados', 'Possui atestado?', 'justificativa']])
    st.divider()
    st.markdown('## FALTÔMETRO')
    unidade_selected = st.selectbox('Selecione a unidade', ['ESCOLHA A UND.:', 'I', 'II', 'III'])
    if "I" in unidade_selected:
        daterange = pd.DatetimeIndex(unidades_dr[unidade_selected])

        def date_convert(date):
            date = date.split('/')
            date = datetime(int(date[2]), int(date[1]), int(date[0]))
            return date

        freq_all['date'] = freq_all['data'].apply(date_convert)
        mask = freq_all['date'].dt.date.isin(daterange.date)
        df_filtered = freq_all[mask]



        with_who_missed = df_filtered
        amostra_nome = all_stds[all_stds['matrícula'].isin([rm])]
        d_mat_nome = {
            matrícula: nome for matrícula, nome in zip(amostra_nome.matrícula, amostra_nome.estudante)
        }
        df = make_big_df(with_who_missed)
        class_jus = all_jus[all_jus['matrícula'].isin(df.matrícula)]
        def classificar_justificativa(row_, class_jus_):
            df_ = class_jus_[class_jus_["matrícula"] == row_["matrícula"]]
            if df_.empty:
                return 'NÃO'
            else:
                for j, row in df_.iterrows():
                    data_inicio = datetime.strptime(row["data_init"], '%d/%m/%Y')
                    data_fim = datetime.strptime(row["data_end"], '%d/%m/%Y')
                    verdade = data_inicio.date() <= row_.date.to_pydatetime().date() <= data_fim.date()
                    if verdade:
                        if row.tem_atestado:
                            return "SIM, COM ATESTADO MÉDICO"
                        return 'SIM'
                return 'NÃO'
        df = df[df['matrícula'].isin([rm])]
        df['JUSTIFICATIVA'] = df.apply(
            lambda row: classificar_justificativa(row, class_jus),
            axis=1
        )
        minhas_datas = unidades[unidade_selected]
        inicio_ = minhas_datas['inicio']
        fim_ = minhas_datas['fim']
        st.markdown(f'### UNIDADE: {unidade_selected}')
        st.markdown(f'### PERÍODO: {inicio_} à {fim_} ')
        pivot = pd.pivot_table(df, index='matrícula', columns='componente', values='faltas', aggfunc='sum')
        pivot['TOTAL_DE_FALTAS'] = pivot.sum(axis=1)
        pivot = pivot.sort_values(by='TOTAL_DE_FALTAS', ascending=False)
        pivot = pivot.fillna(0.0)
        pivot = pivot.astype(int)
        pivot = pivot.replace(0, '-')
        pivot['NOME'] = pivot.index.map(d_mat_nome)
        cols = pivot.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        pivot = pivot.loc[:, cols]
        # pivot = pivot.set_index('NOME')
        st.markdown('#### faltas por componente **SEM** abondo de atestado médico')
        pivot = pivot.drop('NOME', axis=1)
        trans = pivot.T
        trans2 = trans.rename(columns={rm: f'FALTAS DE {d_mat_nome.get(rm)}'})
        st.dataframe(trans2)
        sel_turma_current_ = df.copy()
        sel_turma_current = sel_turma_current_.drop(sel_turma_current_[sel_turma_current_['JUSTIFICATIVA'] == 'SIM, COM ATESTADO MÉDICO'].index)
        pivot = pd.pivot_table(sel_turma_current, index='matrícula', columns='componente', values='faltas', aggfunc='sum')
        pivot['TOTAL_DE_FALTAS'] = pivot.sum(axis=1)
        pivot = pivot.sort_values(by='TOTAL_DE_FALTAS', ascending=False)
        pivot = pivot.fillna(0.0)
        pivot = pivot.astype(int)
        pivot = pivot.replace(0, '-')
        pivot['NOME'] = pivot.index.map(d_mat_nome)
        cols = pivot.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        pivot = pivot.loc[:, cols]
        pivot = pivot.drop('NOME', axis=1)
        st.markdown('#### faltas por componente **COM** abondo de atestado médico')
        trans = pivot.T
        trans2 = trans.rename(columns={rm: f'FALTAS DE {d_mat_nome.get(rm)}'})
        st.dataframe(trans2)
    else:
        st.write('selecione uma unidade para ver o faltômetro')
