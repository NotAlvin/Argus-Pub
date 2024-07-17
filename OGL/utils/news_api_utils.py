import requests
import streamlit as st
import torch
from transformers import BartTokenizer, BartForConditionalGeneration, BertForSequenceClassification, BertTokenizer
import json
from typing import List
from utils.news_api_template import NewsArticle
import time
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


# Define the path for the JSON storage file
SEARCH_HISTORY_FILE = 'OGL/utils/search_history.json'

def load_search_history():
    if os.path.exists(SEARCH_HISTORY_FILE):
        with open(SEARCH_HISTORY_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_search_history(search_history):
    with open(SEARCH_HISTORY_FILE, 'w') as file:
        json.dump(search_history, file, indent=4)

def get_query_id(query: str):
    search_history = load_search_history()
    current_time = datetime.now()

    # Check if the query exists in the search history and if it was searched within the last month
    if query in search_history:
        query_data = search_history[query]
        last_searched = datetime.strptime(query_data['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        if current_time - last_searched < timedelta(days=30):
            print('Using cached query ID')
            return query_data['query_id']

    # If the query is not found or is older than a month, make a new API request
    url = 'https://app.backend.inriskable.com/api/rest/search'
    api_key = st.secrets['inriskable_api_key']  # Replace with your actual API key
    headers = {
        'accept': 'application/json',
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }

    data = {
        "entity_name_en": query,
        "entity_type": "company"
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    if response.status_code == 201:
        query_id = response.json()['data']['id']
        
        # Update the search history with the new query ID and timestamp
        search_history[query] = {
            'query_id': query_id,
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        save_search_history(search_history)
        
        return query_id
    else:
        print('Failed to retrieve query ID')
        return None

def check_query(id: str):
    url = f'https://app.backend.inriskable.com/api/rest/search?id={id}'
    api_key = st.secrets['inriskable_api_key']
    headers = {
        'accept': 'application/json',
        'x-api-key': api_key
    }

    start_time = time.time()
    timeout = 7 * 60  # 7 minutes in seconds
    time.sleep(10)
    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        if response.status_code == 200:
            status = response.json()['data']['status']
            if status == "completed":
                return response.json()
            else:
                print('Query still queued, waiting for ~2 minutes...')
                time.sleep(100)  # Wait for 100 seconds
        else:
            print('Query still queued, waiting for ~2 minutes...')
            time.sleep(100)  # Wait for 100 seconds

        # Check if the timeout has been exceeded
        if time.time() - start_time > timeout:
            print('Error: Query not completed within 7 minutes')
            return {'error': 'Query not completed within 7 minutes'}


# Load pre-trained BART model and tokenizer
summary_model_name = "facebook/bart-large-cnn"
summary_tokenizer = BartTokenizer.from_pretrained(summary_model_name)
summary_model = BartForConditionalGeneration.from_pretrained(summary_model_name)

def get_summary(article_content: str) -> str:
    # Tokenize and summarize the input text using BART
    inputs = summary_tokenizer.encode("summarize: " + article_content, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = summary_model.generate(inputs, max_length=100, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)
    # Decode and output the summary
    summary = summary_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# initialize pre-trained BERT model and tokenizer
sentiment_tokenizer = BertTokenizer.from_pretrained('ProsusAI/finbert')
sentiment_model = BertForSequenceClassification.from_pretrained('ProsusAI/finbert')

def get_sentiment_score(article_content: str) -> float:
    tokens = sentiment_tokenizer.encode_plus(article_content, add_special_tokens=False)
    input_ids = tokens['input_ids']
    attention_mask = tokens['attention_mask']
    
    start = 0
    window_size = 510  # Adjust window size to fit [CLS] and [SEP] tokens
    total_len = len(input_ids)
    loop = True
    
    probs_list = []
    chunk_weights = []
    
    while loop:
        end = start + window_size
        if end >= total_len:
            loop = False
            end = total_len
        
        # Extract chunk and add [CLS] and [SEP]
        input_ids_chunk = [101] + input_ids[start:end] + [102]
        attention_mask_chunk = [1] + attention_mask[start:end] + [1]
        
        # Pad to window_size + 2
        input_ids_chunk += [0] * (window_size - len(input_ids_chunk) + 2)
        attention_mask_chunk += [0] * (window_size - len(attention_mask_chunk) + 2)
        
        # Create input dictionary for model
        input_dict = {
            'input_ids': torch.Tensor([input_ids_chunk]).long(),
            'attention_mask': torch.Tensor([attention_mask_chunk]).int()
        }
        
        # Get model outputs
        outputs = sentiment_model(**input_dict)
        
        # Calculate probabilities and append to list
        probs = torch.nn.functional.softmax(outputs[0], dim=-1)
        probs_list.append(probs)
        
        chunk_weight = end - start
        chunk_weights.append(chunk_weight)
        
        start = end
    
    # Stack probabilities
    stacks = torch.stack(probs_list)
    
    # Create and normalize chunk_weights tensor
    chunk_weights = torch.Tensor(chunk_weights).unsqueeze(1)
    chunk_weights = chunk_weights / chunk_weights.sum()
    
    with torch.no_grad():
        # Ensure stacks is in correct shape
        stacks = stacks.squeeze(1)  # Assuming outputs[0] has shape [batch_size, num_classes]
        
        # Calculate weighted mean
        mean = (chunk_weights * stacks).sum(dim=0)
    
    # Determine sentiment class - Not needed
    #winner = torch.argmax(mean).item()
    #result = ['Positive', 'Negative', 'Neutral'][winner]
    
    # Convert to score in [-1, 1]
    score = mean[0].item() - mean[1].item()
    return score

def get_image_from_link(link: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54'}

    try:
        response = requests.get(link, headers = headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image['content']:
            return og_image['content']
        img = soup.find('img')
        if img and img['src']:
            return img['src']
    except Exception as e:
        print(f"Error fetching image from {link}: {e}")
    return None


def save_articles_to_json(articles: List[NewsArticle], filename: str):
    articles_data = [article.to_dict() for article in articles]
    with open(filename, 'w') as f:
        json.dump(articles_data, f, indent=4)