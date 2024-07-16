import requests
import streamlit as st

def check_query(id):
    url = f'https://app.backend.inriskable.com/api/rest/search?id={id}'
    api_key = st.secrets['inriskable_api_key']
    headers = {
        'accept': 'application/json',
        'x-api-key': api_key
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    if response.status_code == 200:
        if response.json()['data']['status'] == "completed":
            return response.json()
        else:
            print('Query still queued')
            return {}
    else:
        print('Query still queued')
        return {}

def get_query_id(query): #TODO Actually code it
    if query == "Rosewoord Hotels":
        query_id = "clyo0y4rw00ey5rpu64j3ead5" #Rosewood Hotels
    else:
        query_id = "clynzuhek005y5rpux8pdwxyt" #Sonia Cheng
    return query_id

def get_sentiment_score(article_content: str) -> float:
    return 0.0