import pandas as pd
from classes import *
from send_mail import *

import requests
import json

import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

def load_recoltes(path):
    data = pd.read_csv(path)
    data['date'] = pd.to_datetime(data['date'])
    return data


def load_colors(path, recoltes) :
    colors = pd.read_csv(path)
    for legume in recoltes['legume']:
        to_check = legume.lower()
        if to_check[-1]=='s' : to_check = to_check[:-1]
        for index in colors.index:
            if colors['legume'][index] == to_check : colors['legume'][index] = legume

    return colors

def colors_to_discret_map(colors):
    dict = {}
    for index in colors.index :
        dict[colors['legume'][index]] = colors['color'][index]

    return dict

def save_recolte(df_recoltes, recolte, file_path, username):
    to_append = {
        'legume' : recolte.get_legume(),
        'date' : recolte.get_date(),
        'poids' : recolte.get_poids(),
        'variete' : recolte.get_variete(),
        'nombre' : recolte.get_nombre(),
        'photopath' : recolte.get_photopath(),
        'user' : username
    }
    df_recoltes = df_recoltes.append(to_append, ignore_index = True)
    df_recoltes.to_csv(file_path, index = False)
    return df_recoltes


def add_user(username, password, mail, city, df_users, file_path):
    to_append = {
        'username' : username,
        'password' : password,
        'mail' : mail,
        'city' : city
    }

    df_users = df_users.append(to_append, ignore_index = True)
    df_users.to_csv(file_path, index = False)
    text = "Bienvenu à la PotagApp " + username + ',\n'
    text += "Tu peux maintenant facilement suivre tes récoltes sur notre application.\n"
    text += "Pour rappel, ton mot de passe est le suivant : " + password + '\n'
    text += "Tu pourras modifier tes informations via l'appliation.\n\n"
    text += "Jardines bien !"
    send_mail(mail, "Bienvenu à la PotagApp", text)
    return df_users

def send_mail_retrieve_info(mail, users):
    user = users[users['mail']==mail].reset_index(drop=True)

    text = "Voici les informations reliées à cette adresse mail :\n"
    text += "Nom d'utilisateur :" + user["username"][0] + '\n'
    text += "Mot de passe :" + user["password"][0] + '\n'
    text += "Ville favorite :" + str(user["city"][0]) + '\n'
    text += "À bientôt sur la PotagApp !"
    send_mail(mail, "Informations PotagApp", text)


@st.cache
def get_weather_from_city(city, key, spec = None, addons = '&units=metric'):
    ''' Get weather using Openweathermap api from city name. An api key is mendatory and is free on their website.
    Params :
    city (str): city where one wants to see the weather.
    key (str): API key.
    spec (str, optional): specific info in json.
    addons (str, optional): add any additional str to the request.
    '''

    req = 'https://api.openweathermap.org/data/2.5/weather?q='+city+'&appid='+key+addons
    response = requests.get(req)
    return response

@st.cache
def check_api_key(key):
    '''Make a request to the Openweathermap API to check if key is valid and returns True or False.
    Params :
    key (str): API key.
    '''
    response = get_weather_from_city(city = 'London', key = key).json()
    if 'message' in response.keys(): return False
    else: return True

@st.cache
def get_weather_from_lon_lat(lon, lat, key, addons = '&units=metric'):
    ''' Get weather using Openweathermap api from longitude and latitude. An api key is mendatory and is free on their website.
    Params :
    lon (str): longitude where one wants to see the weather.
    lat (str): latitude where one wants to see the weather.
    key (str): API key.
    addons (str, optional): add any additional str to the request.
    '''
    req = 'http://api.openweathermap.org/data/2.5/onecall?lon='+lon+'&lat='+lat+'&APPID='+key+addons
    response = requests.get(req)
    return response

#@st.cache
def get_historical_weather(dt, lon, lat, key, addons = '&units=metric'):
    ''' Get historical weather using Openweathermap api from longitude and latitude. An api key is mendatory and is free on their website.
    Params :
    dt (int):
    lon (str): longitude where one wants to see the weather.
    lat (str): latitude where one wants to see the weather.
    key (str): API key.
    addons (str, optional): add any additional str to the request.
    '''

    req = 'https://api.openweathermap.org/data/2.5/onecall/timemachine?lat='+lat+'&lon='+lon+'&dt='+dt+'&appid='+key+addons
    response = requests.get(req)
    return response

def get_time_stamp(date, days = 0):
    if days > 0 :
        return int(datetime.datetime.timestamp( date + datetime.timedelta(  int(abs(days)) )))
    elif days < 0 :
        return int(datetime.datetime.timestamp( date - datetime.timedelta(  int(abs(days)) )))
    else:
        return datetime.datetime.timestamp(date)
def get_date(seconds):
    return datetime.datetime.fromtimestamp(seconds)#.strftime("%A, %B %d, %Y %I:%M:%S")

#@st.cache
def get_spec(response, spec, start, end, t = False):
    '''
    Getting the average value of spec over a https://openweathermap.org/api/one-call-api#history call.
    Params :
    response (str): text of the response of the API call must be in humidity, temp, feels_like, clouds, wind_speed.
    spec (str): particular spec one wants to follow. May not be present (rain for example).
    start (int): start hour for the average. Must be smaller than end.
    end (int): end hour for the average. Must be higher than start.

    Warning : response contains list of hours, for predictions, it has 48 hours so start and end can be > 24.
    '''

    assert start <= end , "Check hours, seems wrong"


    response = json.loads(response)
    if t :
        st.write(response)
    if spec == 'weather'  :
        pass
    elif spec == 'rain' :
        sum = 0
        for hour in range(start, end+1):
            try :
                sum += response['hourly'][hour][spec]['1h']
            except:
                sum += 0
        return sum
    else:
        sum = 0
        for hour in range(start, end+1):
            try :
                sum += response['hourly'][hour][spec]
            except:
                sum += 0
        return sum


# @st.cache
def get_KPIs(lon, lat, key):
    today = datetime.datetime.today()

    KPIs = pd.DataFrame(columns=['Date', 'Humidité', 'Pluie', 'Température', 'Ressentie', 'Vent'])

    #3 days ago :
    dt = get_time_stamp(today,-3)
    rep = get_historical_weather(dt=str(dt), lon= str(lon), lat=str(lat), key=key).text
    # TODO : start and end hours should be chosen depending on the hours of light
    to_append = {'Date': get_date(dt).date() ,
                 'Humidité': get_spec(rep, 'humidity', 8, 22)/(22-8+1),
                 'Pluie': get_spec(rep, 'rain', 0, 23),
                 'Température': get_spec(rep, 'temp', 8, 22)/(22-8+1),
                 'Ressentie': get_spec(rep, 'feels_like', 8, 22)/(22-8+1),
                 'Vent': get_spec(rep, 'wind_speed', 8, 22)/(22-8+1) }
    KPIs = KPIs.append(to_append, ignore_index = True)

    #2 days ago :
    dt = get_time_stamp(today,-2)
    rep = get_historical_weather(dt=str(dt), lon= str(lon), lat=str(lat), key=key).text
    # TODO : start and end hours should be chosen depending on the hours of light
    to_append = {'Date': get_date(dt).date() ,
                 'Humidité': get_spec(rep, 'humidity', 8, 22)/(22-8+1),
                 'Pluie': get_spec(rep, 'rain', 0, 23),
                 'Température': get_spec(rep, 'temp', 8, 22)/(22-8+1),
                 'Ressentie': get_spec(rep, 'feels_like', 8, 22)/(22-8+1),
                 'Vent': get_spec(rep, 'wind_speed', 8, 22)/(22-8+1) }
    KPIs = KPIs.append(to_append, ignore_index = True)
    #1 days ago :
    dt = get_time_stamp(today,-1)
    rep = get_historical_weather(dt=str(dt), lon= str(lon), lat=str(lat), key=key).text
    # TODO : start and end hours should be chosen depending on the hours of light
    to_append = {'Date': get_date(dt).date() ,
                 'Humidité': get_spec(rep, 'humidity', 8, 22)/(22-8+1),
                 'Pluie': get_spec(rep, 'rain', 0, 23),
                 'Température': get_spec(rep, 'temp', 8, 22)/(22-8+1),
                 'Ressentie': get_spec(rep, 'feels_like', 8, 22)/(22-8+1),
                 'Vent': get_spec(rep, 'wind_speed', 8, 22)/(22-8+1) }
    KPIs = KPIs.append(to_append, ignore_index = True)

    #Today & tomorrow :
    # Gets weather from today.hour until 48 hours afterwards
    today_rain = 0
    today_humidity = 0
    today_temp = 0
    today_feels = 0
    today_wind = 0
    forward = get_weather_from_lon_lat(lon = str(lon), lat = str(lat), key= key ).text
    hour = today.hour

    if hour > 2 :
        dt = get_time_stamp(today,0)
        past = get_historical_weather(dt=str(dt), lon= str(lon), lat=str(lat), key=key).text
        today_rain += get_spec(past, 'rain', 0, hour - 3) # Starting at 2 oclock and exclund current hour
        today_humidity += get_spec(rep, 'humidity', 0, hour - 3)
        today_temp += get_spec(rep, 'temp', 0, hour - 3)
        today_feels += get_spec(rep, 'feels_like', 0, hour - 3)
        today_wind += get_spec(rep, 'wind_speed', 0, hour - 3)

        today_rain += get_spec(forward, 'rain', 0, 24 - hour - 1 ) # Starting at hour and ending at 23 h
        today_humidity += get_spec(forward, 'humidity', 0, 24 - hour - 1)
        today_temp += get_spec(forward, 'temp', 0, 24 - hour - 1)
        today_feels += get_spec(forward, 'feels_like', 0, 24 - hour - 1)
        today_wind += get_spec(forward, 'wind_speed', 0, 24 - hour - 1)

        today_humidity /= 22  # Starting at 2 oclock till 23 => 22 hours of specs
        today_temp /= 22
        today_feels /= 22
        today_wind /= 22

    else :
        today_rain += get_spec(forward, 'rain', 0, 24 - hour - 1) # Starting at 2 oclock and exclund current hour
        today_humidity += get_spec(forward, 'humidity', 0, 24 - hour - 1)
        today_temp += get_spec(forward, 'temp', 0, 24 - hour - 1)
        today_feels += get_spec(forward, 'feels_like', 0, 24 - hour - 1)
        today_wind += get_spec(forward, 'wind_speed', 0, 24 - hour - 1)

        today_humidity /= 24 - hour # Starting at hour oclock till 23 => 24 - hour hours
        today_temp /= 24 - hour
        today_feels /= 24 - hour
        today_wind /= 24 - hour


    # TODO : start and end hours should be chosen depending on the hours of light

    #TODAY :
    to_append = {'Date': get_date(dt).date() ,
                 'Humidité': today_humidity,
                 'Pluie': today_rain,
                 'Température': today_temp,
                 'Ressentie': today_feels,
                 'Vent':  today_wind}
    KPIs = KPIs.append(to_append, ignore_index = True)

    # 1 day ahead
    to_append = {'Date': get_date( get_time_stamp(today, 1) ).date() ,
                 'Humidité': get_spec(forward, 'humidity', 24 - hour, 24 - hour + 23)/24,
                 'Pluie': get_spec(forward, 'rain', 24 - hour, 24 - hour + 23),
                 'Température': get_spec(forward, 'temp', 24 - hour, 24 - hour + 23)/24,
                 'Ressentie': get_spec(forward, 'feels_like',24 - hour , 24 - hour + 23)/ 24,
                 'Vent': get_spec(forward, 'wind_speed', 24 - hour, 24 - hour + 23)/ 24 }


    KPIs = KPIs.append(to_append, ignore_index = True)

    return KPIs


def get_figs_KPIs(KPIs):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=KPIs['Date'], y=KPIs['Température'], name="Température")
    )


    fig.add_trace(go.Scatter(x=KPIs['Date'], y=KPIs['Ressentie'], name="Ressentie"))

    fig.add_trace(go.Bar(x=KPIs['Date'], y=KPIs['Pluie'], name="Pluie", marker_color = "#2ca02c",opacity=0.5, yaxis="y2",offsetgroup=1))

    fig.add_trace(go.Bar(x=KPIs['Date'], y=KPIs['Vent'], name="Vent", marker_color = "#9467bd", opacity=0.5, yaxis="y3",offsetgroup=2))


    # Create axis objects
    fig.update_layout(

        xaxis=dict(
        domain=[0, 0.8]
        ),
        yaxis=dict(
            title="<b>Température (C)</b>",
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )
        ),
        yaxis2=dict(
            title="<b>Pluie (mm/m^2)</b>",
            titlefont=dict(
                color="#2ca02c"
            ),
            tickfont=dict(
                color="#2ca02c"
            ),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        yaxis3=dict(
            title="<b>Vent (m/s)</b>",
            titlefont=dict(
                color="#9467bd"
            ),
            tickfont=dict(
                color="#9467bd"
            ),
            anchor="free",
            overlaying="y",
            side="right",
            #range = [0,100],
            position = 0.9
        ),
        barmode='group'
    )

    # Update layout properties
    fig.update_layout(
        title_text="Météo par jours",
        width=800,
    )

    return fig
