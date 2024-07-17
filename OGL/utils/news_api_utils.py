import requests
import streamlit as st
from transformers import BartTokenizer, BartForConditionalGeneration, BertForSequenceClassification, BertTokenizer
import json
from typing import List
from utils.news_api_template import NewsArticle
import torch


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
    
    # Determine sentiment class
    winner = torch.argmax(mean).item()
    result = ['Positive', 'Negative', 'Neutral'][winner]
    
    # Convert to score in [-1, 1]
    score = mean[0].item() - mean[1].item()
    return score


def save_articles_to_json(articles: List[NewsArticle], filename: str):
    articles_data = [article.to_dict() for article in articles]
    with open(filename, 'w') as f:
        json.dump(articles_data, f, indent=4)