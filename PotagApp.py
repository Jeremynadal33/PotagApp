import pandas as pd
import streamlit as st
import numpy as np
import time
import os
from PIL import Image

from io import BytesIO
from streamlit.hashing import _CodeHasher
from utils import *
import plotly.express as px
import streamlit.components.v1 as components

from geopy.geocoders import Nominatim

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

try:
    # Before Streamlit 0.65
    from streamlit.ReportThread import get_report_ctx
    from streamlit.server.Server import Server
except ModuleNotFoundError:
    # After Streamlit 0.65
    from streamlit.report_thread import get_report_ctx
    from streamlit.server.server import Server

home_path = ["/Users/jeremynadal/Documents/potagerApp/PotagApp/","/home/ubuntu/PotagApp/"]

pd.options.plotting.backend = "plotly"
###################### FUNCTIONS #################
#@st.cache
def get_data(path):
    try:
        data = pd.read_csv(path)
        return data
    except Exception as e:
        pass
    return pd.DataFrame()

#################### FOR SESSION STATE FROM ONE PAGE TO THE OTHER ###################
class _SessionState:
    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self._state["session"].request_rerun()

    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False

        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(self._state["data"], None):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)

def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session

def _get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = _SessionState(session, hash_funcs)

    return session._custom_session_state



def menu_home(state):
    st.write("## Bienvenu à la Potag'app \n")
    st.image('data/backg.jpg')
    st.write("#")
    st.write('Ici, tu peux voir où en sont tes récoltes et tes semis !')
    st.write("Tu peux aussi regarder combien il a plu récemment et si tu vas avoir besoin d'arroser")


def menu_recoltes(state):
    st.write("## Récoltes")

    cols = st.beta_columns([1,1,1,1])
    with cols[0]:
        date_depuis = st.date_input('Depuis', date(date.today().year,1,1) )
    with cols[1]:
        date_jusqua = st.date_input("Jusqu'à", date(date.today().year,12,31) )
    with cols[2]:
        legume = st.selectbox( "Légume", ['Tout']+list(np.unique(state.recoltes['legume'] ) ))
    if legume != 'Tout':
        with cols[3]:
            variete = st.selectbox( "Variété", ['Tout']+list(np.unique(state.recoltes[state.recoltes['legume']==legume]['variete'].dropna() ) ))
    else :
        variete = 'Tout'
    #st.dataframe(state.recoltes)
    to_display = state.recoltes.copy()
    if legume != 'Tout' :
        to_display = to_display[to_display['legume']==legume]
    if variete != 'Tout' :
        to_display = to_display[to_display['variete']==variete]

    if not to_display.empty:
        st.write('Total des récoltes sur la période : '+str( to_display['poids'].sum() ))
        fig = px.bar(to_display,
                     x="date",
                     y="poids",
                     color="legume",
                     color_discrete_map=colors_to_discret_map(state.colors),
                     text="variete",
                     barmode="stack")
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label="1d",
                             step="day",
                             stepmode="backward"),
                        dict(count=7,
                             label="1s",
                             step="day",
                             stepmode="backward"),
                        dict(count=1,
                             label="1m",
                             step="month",
                             stepmode="backward"),
                        dict(count=1,
                             label="YTD",
                             step="year",
                             stepmode="todate"),
                        dict(count=1,
                             label="1y",
                             step="year",
                             stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )
        fig.update_layout(
            title_text="Récoltes en grammes"
        )
        st.plotly_chart( fig )
    else:
        st.warning('Rien ne correspond aux critères demandés ou alors la base de donnée est vide.')

    with st.beta_expander("Ajouter une récolte :") :
        #Initialisation de la variable pour éviter le bug
        new_variete = ''
        cols = st.beta_columns([1,1,1])
        with cols[0]:
            date_recolte = st.date_input('Date', date.today() )
        cols = st.beta_columns([1,1,1])
        cols_if = st.beta_columns([1,1,1])
        with cols[0]:
            new_legume = st.selectbox( "Légume", ['']+list(np.unique(state.recoltes['legume']) )+['Autre'])

        if new_legume == 'Autre':
            with cols_if[0]:
                new_legume = st.text_input("Nouveau légume")

        if new_legume != '':
            with cols[1]:
                new_variete = st.selectbox( "Variété", ['']+list(np.unique(state.recoltes[state.recoltes['legume']==new_legume]['variete'].dropna() ))+['Autre'] )
        if new_variete == 'Autre':
            with cols_if[1]:
                new_variete = st.text_input("Nouvelle variété")


        cols = st.beta_columns([1,1,1])
        with cols[0]:
            nombre = st.number_input('Nombre',0,50,1,help="Mettre 0 si l'on ne peut pas compter")
        with cols[1]:
            poids = st.number_input('Poids (g)',0,10000,0)

        photopath = st.file_uploader('Ajoutes une photo de ta récolte !', type = ['jpeg','jpg','png','pdf'])
        # if file is uploaded
        if photopath is not None:
            file_details = {'file_name ': photopath.name,
                            'file_size ': photopath.size,
                            'file_type ': photopath.type}

        recolte = Recolte(legume = new_legume, date = date_recolte, poids = poids, variete = new_variete, nombre = nombre, photopath = photopath)
        cols = st.beta_columns([1,1,1])
        if st.button("Save"):
            if ( new_legume == '' or poids == 0 ) :
                st.error("Attention, il faut spécifier un légume et le poids !")
            else:
                state.recoltes  = save_recolte(state.recoltes, recolte, state.db_path )
                st.info("Récolte ajoutée avec succès !")


def menu_meteo(state):
    st.write("## Météo")
    geolocator = Nominatim(user_agent="potagerApp")
    with open("openweather_api_key.bin", encoding="utf-8") as binary_file:
        key = binary_file.read()[:-1]
    # Check if key is valid :
    correct_key = check_api_key(key)
    if not correct_key :
        st.warning("Invalid API key for Openweathermap, please make sure the file contains a correct one or send message to developper.")

    # TODO: Check if user has favorite city

    cols = st.beta_columns([1,2])
    with cols[0]:
        city = st.text_input("Choisir une ville : ","Eysines")
    if city != '':
        weather_html = get_weather_from_city(city = city, key = key, addons = '&units=metric&mode=html&lang=fr').text
        if 'city not found' in weather_html:
            st.warning("Cette ville n'est pas disponible, essaie la vile la plus proche")
        else:
            with cols[1]:
                components.html(weather_html)
        location = geolocator.geocode(city)
        if location != None:
            # On créer un dataframe avec les KPI que l'on veut suivre

            #st.json(get_weather_from_lon_lat(lon = str(location.longitude), lat = str(location.latitude), key = key, spec = None, addons = '').text)
            #st.json(get_historical_weather(dt=str(get_time_stamp(today,-1)), lon= str(location.longitude), lat=str(location.latitude), key=key).text)

            KPIs = get_KPIs(location.longitude, location.latitude, key)
            graph = get_figs_KPIs(KPIs)
            st.plotly_chart(graph)
        else :
            st.warning("Désolé, nous ne disposons pas de plus d'informations pour cette ville.")

    #
    # st.json(get_weather_from_lon_lat(lon = str(location.longitude), lat = str(location.latitude), key = key, spec = None, addons = '&units=metric&lang=fr').text)
    # cols = st.beta_columns([1,1,1])
    # with cols[0]:
    #     seconds = st.text_input('Seconds')
    # if seconds != '':
    #     with cols[1]:
    #         st.write(get_date(int(seconds)))
    #
    # if st.button('get one call') :
    #     rep = get_weather_from_lon_lat(lon= str(location.longitude), lat=str(location.latitude), key=key).text
    #     test = json.loads(rep)
    #     st.write('Average of temp is '+str(get_spec(rep, 'temp', 8, 22)))
    #     st.write(test['hourly'])



def menu_stats(state):
    st.write('unavailable')
    # TODO: tout


def main():
    cols = st.beta_columns([1,1,1])
    with cols[1]:
        st.title("Potag'app")

    state = _get_state()
    for path in home_path:
        if os.path.exists(path):
            state.home_path = path
            state.db_path = path + 'data/recoltes.csv'
            state.recoltes = load_recoltes(state.db_path)
            state.colors = load_colors(path + 'data/colors.csv', state.recoltes)

    if state.db_path == None :
        st.error("Le chemin vers la bdd n'existe pas")
    possibilities = ["Accueil", "Récoltes", "Météo", "Stats"]
    choice = st.sidebar.selectbox("Menu",possibilities)



    if choice == 'Accueil':
        #menu_meteo(state)
        menu_home(state)
    elif choice == 'Récoltes':
        menu_recoltes(state)
    elif choice == 'Météo':
        menu_meteo(state)
    elif choice == 'Stats':
        menu_stats(state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()


if __name__ == "__main__":
    main()