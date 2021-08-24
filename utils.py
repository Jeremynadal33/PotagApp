import pandas as pd
from classes import *
from send_mail import *

import requests
import json

import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import os
from PIL import Image
import base64
import pymysql
from datetime import date

def load_recoltes(host, username, password, dbname):
    db, cursor = connect_to_database(host, username, password, dbname)
    data = pd.read_sql('select * from recoltes', db)
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

def save_recolte(df_recoltes, recolte, current_username, host, username, password, dbname):
    db, cursor = connect_to_database(host, username, password, dbname)

    add_recolte_to_rds(cursor = cursor,
                       legume = recolte.get_legume(),
                       poids = recolte.get_poids(),
                       date = recolte.get_date(),
                       user = current_username,
                       variete = recolte.get_variete(),
                       nombre = recolte.get_nombre())

    data = pd.read_sql('select * from recoltes', db)
    data['date'] = pd.to_datetime(data['date'])
    return data

def save_photo_recolte(photopath, date_photo, username, bucket_name = 'potagapp-bucket'):
    obj_name = username + '/' + str(date_photo.day) + '_' + str(date_photo.month) + '_' + str(date_photo.year) + '.' + photopath.type.split('/')[-1]
    save_uploadedfile(photopath)
    upload_file_to_bucket(file_name="tempDir/"+str(photopath.name), bucket=bucket_name, object_name=obj_name)


def save_uploadedfile(uploadedfile):
     with open(os.path.join("tempDir",uploadedfile.name),"wb") as f:
         f.write(uploadedfile.getbuffer())
     return st.success('File on ec2')

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

def modify_user(username, password, mail, city, df_users, file_path):
    to_append = {
        'username' : username,
        'password' : password,
        'mail' : mail,
        'city' : city
    }
    df_users = df_users.loc[ df_users['username'] != username ]
    df_users = df_users.append(to_append, ignore_index = True)
    df_users.to_csv(file_path, index = False)
    text = "Bonjour de la PotagApp " + username + ',\n'
    text += "Pour rappel, tes nouvelles informations sont :\n"
    text += "Mot de passe : " + password +"\n"
    text += "Mail : " + mail +"\n"
    text += "Ville : " + city +"\n"
    text += "Jardines bien !"
    send_mail(mail, "Modification d'informations", text)
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

######### For using boto ##########
import logging
import boto3
from botocore.exceptions import ClientError

def create_bucket(bucket_name, region=None):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def list_my_buckets():
    # Retrieve the list of existing buckets
    s3 = boto3.client('s3')
    response = s3.list_buckets()

    # Output the bucket names
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

def list_objects_in_bucket(bucket_name, username = None):
    s3 = boto3.client("s3")
    objects = s3.list_objects(Bucket = bucket_name ,Prefix=username)
    photopaths = []
    df = pd.DataFrame(columns=['file_name','date'])
    for obj in objects['Contents']:
        file = obj['Key']
        year = int(file.split('/')[-1].split('.')[0].split('_')[-1])
        month = int(file.split('/')[-1].split('.')[0].split('_')[1])
        day = int(file.split('/')[-1].split('.')[0].split('_')[0])
        to_append = {'file_name': file ,
                     'date': date(year, month, day)}
        df = df.append(to_append,ignore_index=True)

        #photopaths.append()
    df = df.sort_values('date', ascending = False).reset_index(drop=True)
    return df['file_name']


def download_objects_from_bucket(bucket_name, file_names, username):
    s3 = boto3.client('s3')
    paths = []
    # First, check if directory exists
    if os.path.exists('tempDir/' + username) :
        for file in file_names :
            paths.append('tempDir/'+file)
            if not os.path.exists('tempDir' + '/' + file):
                s3.download_file(bucket_name, file, 'tempDir/' + username + '/' +file.split('/')[-1])
    else:
        os.mkdir('tempDir/' + username)
        for file in file_names:
            s3.download_file(bucket_name, file, 'tempDir/' + username + '/' +file.split('/')[-1])
            paths.append('tempDir/'+file)
    return paths


@st.cache
def ram_objects_from_bucket(bucket_name, file_names, username):
    images = []
    s3 = boto3.resource('s3', region_name='eu-west-3')
    bucket = s3.Bucket(bucket_name)

    for file in file_names:
        object = bucket.Object(file)
        response = object.get()
        file_stream = response['Body']
        images.append(Image.open(file_stream))

    return images


def upload_file_to_bucket(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return st.error("Attention, une erreur inconnue est arrivée. L'image n'est pas en ligne.")
    return st.success("Image mise en ligne.")

def get_table_download_link(df, name):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="'+ name +'.csv">Dl ' + name +' file</a>'
    return href



### For remote database access
def read_rds_infos(path):
    file = open(path)
    identifier = file.readline().split(':')[-1][:-1]
    username = file.readline().split(':')[-1][:-1]
    password = file.readline().split(':')[-1][:-1]
    host = file.readline().split(':')[-1][:-1]
    port = file.readline().split(':')[-1][:-1]
    dbname = file.readline().split(':')[-1][:-1]
    return identifier, username, password, host, port, dbname

def connect_to_database(host, username, password, dbname):
    rds_db = pymysql.connect(host = host,
                         user = username,
                         password = password,
                         db = dbname,
                         autocommit = True)
    rds_cursor = rds_db.cursor()

    return rds_db, rds_cursor

def add_recolte_to_rds(cursor, legume, poids, date, user, variete = None, nombre = 0):
    sql = '''
    insert into recoltes (legume, poids, date, user, variete, nombre) values ('%s', '%d', '%s', '%s', '%s', '%d')
    ''' % (legume, poids, date, user, variete, nombre)

    cursor.execute(sql)
