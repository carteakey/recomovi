import http, requests
import streamlit as st

API_URL = 'http://www.omdbapi.com/?apikey='
API_KEY = st.secrets['OMDB_API_KEY'] 

def getOMDBInfo(title_id):

    response = requests.get(API_URL+API_KEY+'&i='+title_id)

    if response:
        return response.json()
    else:
        print('Request returned an error.')
        

