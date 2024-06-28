import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.pipeline import load_or_scrape_file

st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="centered",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="expanded",  # Can be "auto", "expanded", "collapsed"
	page_title='News',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)

# Streamlit dashboard
st.title("Latest IPO News 🗞️")
st.write("---")

st.sidebar.header("Filter News")
max_days = st.sidebar.slider("Select how many past days of news to display:", 1, 7, 7)
load_news_button = st.sidebar.button("Load News")
source = st.sidebar.radio("Choose a news source", ("CNBC", "Market Insights", "Stock Analysis"))

news_df = load_or_scrape_file(source.replace(' ', '').lower())

if load_news_button:
    cutoff_date = datetime.now() - timedelta(days=max_days)
    
    # Filter the DataFrame based on the selected number of days
    # filtered_news_df = news_df[news_df['Time'] >= cutoff_date]

    # for i, row in filtered_news_df.iterrows():
    #     st.write(f"{row['Time'].strftime('%b %d, %Y, %I:%M %p %Z') if not pd.isnull(row['Time']) else 'Invalid date'}")
    #     with st.expander(row['Title']):
    #         st.write(f"**Source:** {row['Source']}")
    #         st.write(f"**Description:** {row['Description']}")
    #         st.write(f"**Tickers:** {row['Tickers']}")
            
    #         if row['Image URL'] != "No image":
    #             st.image(row['Image URL'])
    
    # Display the entire filtered dataframe
    st.write("## Full News Data")
    st.dataframe(news_df)

else:
    st.write(f"Select a news lookback period in the sidebar to load the news!")