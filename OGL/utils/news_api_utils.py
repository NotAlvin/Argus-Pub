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

def get_summary(text):
    # Tokenize and summarize the input text using BART
    inputs = summary_tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = summary_model.generate(inputs, max_length=100, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)
    # Decode and output the summary
    summary = summary_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def get_sentiment_score(article_content: str) -> float:
    '''
    Trying out sentiment scoring for article content
    '''
    # initialize our model and tokenizer
    tokenizer = BertTokenizer.from_pretrained('ProsusAI/finbert')
    model = BertForSequenceClassification.from_pretrained('ProsusAI/finbert')

    tokens = tokenizer.encode_plus(article_content, add_special_tokens=False)
    input_ids = tokens['input_ids']
    attention_mask = tokens['attention_mask']
    # define our starting position (0) and window size (number of tokens in each chunk)
    start = 0
    window_size = 512
    
    # initialize probabilities list
    probs_list = []
    # initialize weight of chunks
    chunk_weights = []

    start = 0
    window_size = 510  # we take 2 off here so that we can fit in our [CLS] and [SEP] tokens
    total_len = len(input_ids)
    loop = True
    while loop:
        end = start + window_size
        if end >= total_len:
            loop = False
            end = total_len
        # (1) extract window from input_ids and attention_mask
        input_ids_chunk = input_ids[start:end]
        attention_mask_chunk = attention_mask[start:end]
        # (2) add [CLS] and [SEP]
        input_ids_chunk = [101] + input_ids_chunk + [102]
        attention_mask_chunk = [1] + attention_mask_chunk + [1]
        # (3) add padding upto window_size + 2 (512) tokens
        input_ids_chunk += [0] * (window_size - len(input_ids_chunk) + 2)
        attention_mask_chunk += [0] * (window_size - len(attention_mask_chunk) + 2)
        # (4) format into PyTorch tensors dictionary
        input_dict = {
            'input_ids': torch.Tensor([input_ids_chunk]).long(),
            'attention_mask': torch.Tensor([attention_mask_chunk]).int()
        }
        # (5) make logits prediction
        outputs = model(**input_dict)
        # (6) calculate softmax and append to list
        probs = torch.nn.functional.softmax(outputs[0], dim=-1)
        probs_list.append(probs)
        chunk_weight = end - start
        start = end
    stacks = torch.stack(probs_list)
    chunk_weights = torch.Tensor([window_size] * len(probs_list)).resize_(4, 1)
    chunk_weights[-1] = chunk_weight
    chunk_weights = chunk_weights / chunk_weights.sum()
    with torch.no_grad():
        # we must include our stacks operation in here too
        stacks = torch.stack(probs_list)
        # now resize
        stacks = stacks.resize_(stacks.shape[0], stacks.shape[2])
        # finally, we can calculate the mean value for each sentiment class
        # mean = stacks.mean(dim=0)
        chunk_weights = chunk_weights
        mean = (chunk_weights*stacks).sum(dim=0)
    winner = torch.argmax(mean).item()
    result = ['Positive', 'Negative', 'Neutral'][winner]
    # Converting to a score in [-1,1]
    score = mean[0].item() - mean[1].item()
    return score


def save_articles_to_json(articles: List[NewsArticle], filename: str):
    articles_data = [article.to_dict() for article in articles]
    with open(filename, 'w') as f:
        json.dump(articles_data, f, indent=4)