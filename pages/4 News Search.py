import streamlit as st
from serpapi import GoogleSearch
import json

# Opening JSON file 
f = open(r'./utils/data/Scrape/google-countries.json') 

# returns JSON object as a dictionary 
country_mapping_list = json.load(f)
country_mapping = {}
for item in country_mapping_list:
    country_mapping[item['country_name']] = item['country_code']

def search_news(selected_countries, selected_categories, country_mapping):
    query = ' OR '.join(selected_categories)
    
    params = {
        "q": query,
        "google_domain": "google.com",
        "tbm": "nws",  # Search only in news for timely information
        "num": 100,     # Number of results to fetch
        "api_key": st.secrets["serp_api_key"],
    }

    if "Guernsey" not in selected_countries:
        params["gl"] = [country_mapping[item] for item in selected_countries]  # Set the country code for geolocation
    else:
        query = ' OR '.join(selected_categories) + ' AND '.join(selected_countries)

    search = GoogleSearch(params)
    results = search.get_dict()
    if "news_results" in results:
        return results["news_results"]
    else:
        st.write('No news results found')
        return []

# Sidebar for user input
st.sidebar.header("Search Settings")
countries = {'Ireland', 'United Kingdom', 'Turkey', 'Sweden', 'Guernsey', 'Switzerland', 'Luxembourg', 'Monaco', 'Hong Kong', 'Singapore'}
categories = categories = {
    'IPO',
    'Initial Public Offering',
    'M&A',
    'Merger and Acquisition',
    'Merger',
    'Acquisition',
    'Private Equity Buyout',
    'Secondary Sale',
    'Strategic Investment',
    'SPAC Merger',
    'Special Purpose Acquisition Company Merger',
    'Tender Offer',
    'Special Dividend',
    'Asset Sale'
}

selected_countries = st.sidebar.multiselect("Select Country", list(countries), default=list(countries))
selected_categories = st.sidebar.multiselect("Select Category", list(categories), default=list(categories))

if st.sidebar.button("Search"):
    results = search_news(selected_countries, selected_categories, country_mapping)

    for result in results:
        # Display article info and thumbnail side by side
        col1, col2 = st.columns([1, 5])
        
        with col1:
            if 'thumbnail' in result:
                st.image(result['thumbnail'], use_column_width=True)
        
        with col2:
            st.write(f"[{result['title']}]({result['link']})")
            st.write(f"**Source:** {result['source']}")
            st.write(f"**Date:** {result['date']}")
            st.write(f"**Snippet:** {result['snippet']}")
        
        st.write("---")
else:
    st.write("Search for news based on the filter in the sidebar to the left!")