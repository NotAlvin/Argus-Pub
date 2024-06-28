import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_stockanalysis():
    """
    Scrapes the latest IPO news articles from StockAnalysis website.
    
    Returns:
        pd.DataFrame: DataFrame containing the extracted news articles.
    """
    
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

    # Iterate over each article to extract the required information
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

    # Convert 'Time' column to datetime
    news_df['Time'] = pd.to_datetime(news_df['Time'], errors='coerce')

    return news_df