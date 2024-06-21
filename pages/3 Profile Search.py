import streamlit as st
from serpapi import GoogleSearch

def search_person(person_name, company_name=None):
    if company_name:
        query = f'{person_name} {company_name}'
    else:
        query = f'{person_name} startup founder'
        
    params = {
        "q": query,
        "google_domain": "google.com",
        # Add more parameters as needed for better targeting
        "tbm": "nws",  # Search only in news for timely information
        "num": 10,     # Number of results to fetch
        "api_key":st.secrets["serp_api_key"],
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results

st.title("Profile Searcher 👤")
st.write("---")

# Sidebar for user input
st.sidebar.header("Search Settings")
person_name = st.sidebar.text_input("Enter person's name")
company_name = st.sidebar.text_input("Enter company's name (optional)")

if st.sidebar.button("Search"):
    if person_name:
        results = search_person(person_name, company_name)

        if "news_results" in results:
            news_results = results["news_results"]
            for result in news_results:
                # Display article info and thumbnail side by side
                col1, col2 = st.columns([1, 5])
                
                with col1:
                    st.image(result['thumbnail'], use_column_width=True)
                
                with col2:
                    st.write(f"[{result['title']}]({result['link']})")
                    st.write(f"**Source:** {result['source']}")
                    st.write(f"**Date:** {result['date']}")
                    st.write(f"**Snippet:** {result['snippet']}")
                
                st.write("---")
        else:
            st.write(f"No results for {person_name} found!")

else:
    st.write("Search for a prospect's name in the sidebar to the left!")