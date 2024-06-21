import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="centered",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="expanded",  # Can be "auto", "expanded", "collapsed"
	page_title='News',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)

# URL of the page to scrape
url = "https://stockanalysis.com/ipos/news/"

# Send a GET request to the webpage
response = requests.get(url)

# Parse the content with BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Extract news articles
articles = soup.find_all('div', class_='gap-4 border-gray-300 bg-white p-4 shadow last:pb-1 last:shadow-none dark:border-dark-600 dark:bg-dark-800 sm:border-b sm:px-0 sm:shadow-none sm:last:border-b-0 lg:gap-5 sm:grid sm:grid-cols-news sm:py-6')

# Lists to store the extracted information
titles = []
times = []
sources = []
descriptions = []
tickers = []
images = []

for article in articles:
    # Extract the title
    title_tag = article.find('h3', class_='mb-2 mt-3 text-xl font-bold leading-snug sm:order-2 sm:mt-0 sm:leading-tight')
    title = title_tag.get_text(strip=True) if title_tag else "No title"
    titles.append(title)
    
    # Extract the time
    time_tag = article.find('div', class_='mt-1 text-sm text-faded sm:order-1 sm:mt-0')
    time = time_tag['title'] if time_tag else "No time"
    times.append(time)
    
    # Extract the source
    source = time_tag.get_text(strip=True) if time_tag else "No source"
    sources.append(source)
    
    # Extract the description
    description_tag = article.find('p', class_='overflow-auto text-[0.95rem] text-light sm:order-3')
    description = description_tag.get_text(strip=True) if description_tag else "No description"
    descriptions.append(description)
    
    # Extract company ticker symbols if present
    stocks = article.find_all('a', class_='ticker')
    company_list = [stock.get_text(strip=True) for stock in stocks]
    tickers.append(", ".join(company_list))
    
    # Extract the image URL
    img_tag = article.find('img', class_='rounded')
    img_url = img_tag['src'] if img_tag else "No image"
    images.append(img_url)

# Create a DataFrame
news_df = pd.DataFrame({
    "Title": titles,
    "Time": times,
    "Source": sources,
    "Description": descriptions,
    "Tickers": tickers,
    "Image URL": images
})

news_df['Time'] = pd.to_datetime(news_df['Time'], errors='coerce')

# Streamlit dashboard
st.title("Latest IPO News 🗞️")
st.write("---")

st.sidebar.header("Filter News Lookback Period")
max_days = st.sidebar.slider("Select how many past days of news to display:", 1, 7, 7)
load_news_button = st.sidebar.button("Load News")

if load_news_button:
    cutoff_date = datetime.now() - timedelta(days=max_days)
    
    # Filter the DataFrame based on the selected number of days
    filtered_news_df = news_df[news_df['Time'] >= cutoff_date]

    for i, row in filtered_news_df.iterrows():
        st.write(f"{row['Time'].strftime('%b %d, %Y, %I:%M %p %Z') if not pd.isnull(row['Time']) else 'Invalid date'}")
        with st.expander(row['Title']):
            st.write(f"**Source:** {row['Source']}")
            st.write(f"**Description:** {row['Description']}")
            st.write(f"**Tickers:** {row['Tickers']}")
            
            if row['Image URL'] != "No image":
                st.image(row['Image URL'])
    
    # Display the entire filtered dataframe
    # st.write("## Full News Data")
    # st.dataframe(filtered_news_df)

else:
    st.write(f"Select a news lookback period in the sidebar to load the news!")