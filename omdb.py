import http, requests

API_URL = 'http://www.omdbapi.com/?apikey='
API_KEY = '521f6ba3' # Steal it, its free :D 

def getOMDBInfo(title_id):

    response = requests.get(API_URL+API_KEY+'&i='+title_id)

    if response:
        return response.json()
    else:
        print('Request returned an error.')
        

