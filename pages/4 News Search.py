import streamlit as st
from serpapi.google_search import GoogleSearch
import pandas as pd
import json
from datetime import datetime

serp_api_key = st.secrets["serp_api_key"]

# Opening JSON file
with open(r'./utils/data/Scrape/google-countries.json') as f:
    # returns JSON object as a dictionary
    country_mapping_list = json.load(f)

country_mapping = {item['country_name']: item['country_code'] for item in country_mapping_list}


def search_news(selected_countries, selected_categories, time_range, country_mapping):
    query = ' OR '.join(selected_categories)
    
    params = {
        "google_domain": "google.com",
        "tbm": "nws",  # Search only in news for timely information
        "num": 100,     # Number of results to fetch
        "tbs": time_range,  # Time range for the search
        "api_key": serp_api_key,
    }

    if "Guernsey" not in selected_countries:
        params["gl"] = ','.join([country_mapping[item] for item in selected_countries if item in country_mapping])  # Set the country code for geolocation
    else:
        query = f"({' OR '.join(selected_categories)}) ' AND ' ({' OR '.join(selected_countries)})"
    params["q"] = query,
    #print(params)
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

time_ranges = {
    'Any time': '',
    'Past hour': 'qdr:h',
    'Past 24 hours': 'qdr:d',
    'Past week': 'qdr:w',
    'Past month': 'qdr:m',
    'Past year': 'qdr:y'
}

selected_countries = st.sidebar.multiselect("Select Country", list(countries), default=list(countries))
selected_categories = st.sidebar.multiselect("Select Category", list(categories), default=list(categories))
selected_time_range = st.sidebar.selectbox("Select Time Range", list(time_ranges.keys()), index=0)

if st.sidebar.button("Search"):
    time_range = time_ranges[selected_time_range]
    results = search_news(selected_countries, selected_categories, time_range, country_mapping)
    if results:
        # Download button
        df = pd.DataFrame(results)
        curr_date = datetime.today().strftime('%Y-%m-%d')
        file = df.to_csv(index = False)
        st.download_button(
            label="Download data as CSV",
            data=file,
            file_name=f'news_results_{curr_date}.csv',
            mime='text/csv'
        )

        for result in results:
            # Display article info and thumbnail side by side
            col1, col2 = st.columns([1, 5])
            
            with col1:
                if 'thumbnail' in result:
                    st.image(result['thumbnail'], use_column_width=True)
            
            with col2:
                title = result['title'].replace('$', '\$')
                source = result['source'].replace('$', '\$')
                snippet = result['snippet'].replace('$', '\$')
                st.write(f"[{title}]({result['link']})")
                st.write(f"**Source:** {source}")
                st.write(f"**Date:** {result['date']}")
                st.write(f"**Snippet:** {snippet}")
            
            st.write("---")
    else:
        st.write('No results found for selected filters!')
else:
    st.write("Search for news based on the filter in the sidebar to the left!")