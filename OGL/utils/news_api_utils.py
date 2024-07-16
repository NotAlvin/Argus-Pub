import requests
import streamlit as st
from transformers import BartTokenizer, BartForConditionalGeneration
import json
from typing import List
from utils.news_api_template import NewsArticle

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
    if query == "Rosewood Hotels":
        query_id = "clyo0y4rw00ey5rpu64j3ead5" #Rosewood Hotels
    else:
        query_id = "clynzuhek005y5rpux8pdwxyt" #Sonia Cheng
    return query_id


# Load pre-trained BART model and tokenizer
summary_model_name = "facebook/bart-large-cnn"
summary_tokenizer = BartTokenizer.from_pretrained(summary_model_name)
summary_model = BartForConditionalGeneration.from_pretrained(summary_model_name)

def get_summary(text):
    # Tokenize and summarize the input text using BART
    inputs = summary_tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = summary_model.generate(inputs, max_length=100, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)
    # Decode and output the summary
    summary = summary_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def get_sentiment_score(article_content: str) -> float:
    return 0.0

def save_articles_to_json(articles: List[NewsArticle], filename: str):
    articles_data = [article.to_dict() for article in articles]
    with open(filename, 'w') as f:
        json.dump(articles_data, f, indent=4)