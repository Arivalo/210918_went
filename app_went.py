import streamlit as st
import requests
import pandas as pd
import datetime as dt
import base64
from PIL import Image

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# to do
# - wybór daty
# - formatowanie tabeli
# - zamiast 0 i 1 - "OK" i "brak sygnału"
# - index - urządzenie zamiast 0-6
# - rozróżnienie brak danych/sygnału



def download_data(url, haslo=st.secrets['password'], login=st.secrets['username'], retry=5):

    i = 0

    while i < retry:
        r = requests.get(url,auth=(login, haslo))

        try:
            j = r.json()
            break
        except:
            i += 1
            print(f"Try no.{i} failed")

    if i == retry:
        print(f"Failed to fetch data for: {url}")
        return pd.DataFrame()
        
    df = pd.DataFrame.from_dict(j['entities'])
    if not df.empty:
        try:
            df['longtitude'] = [x['coordinates']['x'] for x in df['_meta']]
            df['latitude'] = [y['coordinates']['y'] for y in df['_meta']]
            df.pop('_meta')   
            
        except KeyError:
            print(f'Url error: {url}')
            
        df.ffill(inplace=True)
        df['updatedAt'] = pd.to_datetime(df['updatedAt']).dt.tz_localize(None)         
            
    return df
    
    
def utworz_url(data_od, data_do, id):
    str_base = st.secrets['url']
    data_do_parted = str(data_do).split("-")
    str_out = f"{str_base}?from={data_od}T04:00:00Z&to={data_do}T11:00:00Z&monitoredId={id}&limit=10000000"
    return str_out
    
    
def get_table_download_link(df, nazwa_pliku):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{nazwa_pliku}.csv">Download stats table</a>'
    
    return href
    
    
from diagnostyka_czujnikow import czujnik
from diagnostyka_czujnikow import system

class Czujnik_w(czujnik.Czujnik):

    def sprawdz_CAN_min(self):

        if self.CAN_series.max() < self.CAN_min:
            return False
        else:
            return True

#@st.cache(suppress_st_warning=True)
def create_data(data):

    id_dict = {
        20093:2,
        20112:3,
        20178:9,
        20189:16,
        20190:17,
        20192:19,
        20194:21,
    }

    tabele_diag = []
    lokalizacje = []
    
    df_out = pd.DataFrame()
    df_out["urządzenie"] = [f'XT_UAIN_0{x}' for x in range(7)]
    
    for id in list(id_dict.keys()):
        dane = download_data(utworz_url(data, data, id_dict[id]))
        
        try:
            lokalizacje.append(dane['location'].value_counts().index[0])
        except KeyError:
            lokalizacje.append("brak danych")
        
        diagnostyka = system.SystemDiagnozy()
        
        for col in [f'XT_UAIN_0{x}' for x in range(7)]:
            try:
                if len(dane[col].values) > 0:
                    diagnostyka.dodaj_czujnik(Czujnik_w(dane[col], nazwa=col, zakres_CAN=(15, 32768)))
                else:
                    diagnostyka.dodaj_czujnik(Czujnik_w(None, nazwa=col))
                    #print(col)
            except KeyError:
                diagnostyka.dodaj_czujnik(czujnik.Czujnik(None, nazwa=col))
        
        temp = diagnostyka.diagnostyka()
        df_out[id] = [max(2*x,y) for x,y in zip(temp['CAN_no_data'], temp['CAN_min'])]
        
    return df_out, lokalizacje
    #return temp
    
def service_available(num_retry=5):
    for i in range(num_retry):
        r = requests.get(st.secrets['url'][:23])
        status = (r.status_code != 503) or status
        
        if status:
            break
    
    return status
    
def tabela(df):

    def mapowanie(x):
        if x == "brak danych":
            return "lemonchiffon"
        if x == "brak sygnału":
            return "lightcoral"
        return "floralwhite"
    
    df = df.reset_index().rename(columns={'index':""})
    df[""] = [f"<b>{val}</b>" for val in df[""]]
    
    fill_colors = [df[col].map(mapowanie) for col in df.columns]
    
    #malfunctioning_devices = []
    for i, row_id in enumerate(df.T.columns):
        row = df.T[row_id].values
        if "brak sygnału" in row:
            fill_colors[0][i] = "lightcoral"
        elif "brak danych" in row:
            fill_colors[0][i] = "lemonchiffon"
    
    fig = go.Figure(data=[go.Table(
        columnwidth=[10,20,20,20,20,20,20,25,20],
        header=dict(
            values=list([f"<b>{col}</b>" for col in df.columns]),
            fill_color='gray',
            line_color='darkslategray',
            align='center',
            font=dict(color="white", size=15),
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            align='center',
            line_color='darkslategray',
            fill_color=fill_colors,
            font=dict(size=15),
        ),
    )])
    
    fig.update_layout(height=800)
    
    return fig


    
#############################################################################################################

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center; color: black;'>dashboard wentylatory</h1>", unsafe_allow_html=True)



col1, col2 = st.columns((2,13))

data = col1.date_input("Wybór daty", value=dt.date.today(), min_value=dt.date(2021,7,1), max_value=dt.date.today(), help="Choose day you want to analyze")

if service_available():
    
    df, locs = create_data(data)
    
    df = df.set_index("urządzenie").T
    
    df['lokalizacja'] = locs

    lista_urz = [f"XT_UAIN_0{x}" for x in range(7)]
    nazwy = ["temp na ssaniu (IN_00)", "temp na tłoczeniu (IN_01)", "ciśnienie na ssaniu (IN_02)",
             "przepływ (IN_03)", "pobór prądu (IN_04)", "prędkość obrotowa (IN_05)",
             "wilgotność/ciśnienie tł. (IN_06)"]

    df[lista_urz] = df[lista_urz].applymap(lambda x: {0:"OK", 2:"brak danych", 1:"brak sygnału"}[x])
    
    df.rename(columns={x:y for x,y in zip(lista_urz, nazwy)}, inplace=True)

    #col2.table(df)
    
    col2.plotly_chart(tabela(df) , use_container_width=True)
    
    
else:
    col2.header("brak połączenia")
    
col2.write("* 'brak sygnału' - sygnał na wejsciu analogowym < 15 jednostek traktowany jako brak sygnału (w godzinach x-x)")
col2.write("* 'brak danych' - brak danych w danym dniu odebranych z serwera")
col2.write("* 'brak połączenia' - chwilowy brak połączenia z serwerem")

