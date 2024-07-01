import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.pipeline import load_or_scrape_file
from utils.marketinsights import safe_literal_eval

st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="centered",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="expanded",  # Can be "auto", "expanded", "collapsed"
	page_title='News',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)

# Streamlit dashboard
st.title("Latest Liquidity Event News 🗞️")
st.write("---")

st.sidebar.header("Filter News")
max_days = st.sidebar.slider("Select how many past days of news to display:", 1, 7, 7)
load_news_button = st.sidebar.button("Load News")
source = st.sidebar.radio("Choose a news source", ("CNBC", "Market Insights", "Stock Analysis"))

news_df = load_or_scrape_file(source.replace(' ', '').lower())
news_df['Time'] = pd.to_datetime(news_df['Time'])

def explode_col(col_name):
    if col_name != col_name:
        return list(safe_literal_eval(col_name).values())
    else:
        return col_name
if load_news_button:
    cutoff_date = datetime.now() - timedelta(days=max_days)
    
    # Filter the DataFrame based on the selected number of days
    if source == 'CNBC':
        filtered_news_df = news_df[news_df['Time'] >= cutoff_date][['Time', 'Title', 'Article content', 'Source', 'Link']]
    if source == 'Market Insights':
        filtered_news_df = news_df[news_df['Time'] >= cutoff_date][['Time', 'title', 'Article content', 'source', 'link', 'ticker', 'Managers', 'Members of the board', 'Shareholders']]
        filtered_news_df['Managers'] = filtered_news_df['Managers'].apply(explode_col)
        filtered_news_df['Members of the board'] = filtered_news_df['Members of the board'].apply(explode_col)
        filtered_news_df['Shareholders'] = filtered_news_df['Shareholders'].apply(explode_col)
    if source == 'Stock Analysis':
        filtered_news_df = news_df[news_df['Time'] >= cutoff_date][['Time', 'Title', 'Description', 'Source', 'Tickers']]
    # Display the entire filtered dataframe
    st.write("## Full News Data")
    st.dataframe(filtered_news_df)

else:
    st.write(f"Select a news lookback period in the sidebar to load the news!")