import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import dateutil.parser
from datetime import datetime, timedelta
import os

def scrape_cnbc():
    """Scrape news articles from CNBC's IPO page and return them as a DataFrame."""
    
    #print('***** Beginning CNBC news scraping *****')
    
    def datetime_to_relative(dt):
        """Convert a datetime object to a human-readable relative time string."""
        now = datetime.now()
        diff = now - dt
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() // 60)} minutes ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(weeks=1):
            days = int(diff.total_seconds() // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif diff < timedelta(weeks=4):
            weeks = int(diff.total_seconds() // 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = int(diff.total_seconds() // 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"

    # URL of the news page
    url = 'https://www.cnbc.com/ipos/'
    response = requests.get(url)
    
    # Get the HTML content of the page
    html_content = urllib.parse.unquote(response.text)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all article cards
    cards = soup.find_all('div', class_='Card-card')
    
    # Extract information
    data = []
    for card in cards:
        title_tag = card.find('a', class_='Card-title')
        image_tag = card.find('img')
        date_tag = card.find('span', class_='Card-time')
        date_str = date_tag.text if date_tag else ''
        
        if title_tag and image_tag and date_tag:
            title = title_tag.text
            link = title_tag['href']
            image = image_tag['src']
            if 'min ago' in date_str:
                source = f"{date_str} - CNBC News"
                date = datetime.now() - timedelta(minutes=int(date_str.split()[0]))
            elif 'hours ago' in date_str:
                source = f"{date_str} - CNBC News"
                date = datetime.now() - timedelta(hours=int(date_str.split()[0]))
            else:
                # Parse other date formats
                date = dateutil.parser.parse(date_str)
                source = f"{datetime_to_relative(date)} - CNBC News"
            
            data.append({
                'Title': title,
                'Link': link,
                'Image': image,
                'Source': source,
                'Time': date
            })
    
    # Convert to DataFrame for tabular representation
    df = pd.DataFrame(data)
    #print(f'***** Total of: {len(df)} CNBC news articles successfully scraped! *****')
    #print('***** Beginning extraction of CNBC news article contents *****')
    
    def get_article_content(url):
        """Fetch and extract the article content from a given URL."""
        try:
            response = requests.get(url)
            html_content = urllib.parse.unquote(response.text)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all paragraphs within the specified div
            article_body = soup.find('div', class_='ArticleBody-articleBody')
            
            # Extract text from paragraphs
            if article_body:
                paragraphs = article_body.find_all('p')
                article_text = '\n'.join([para.get_text() for para in paragraphs])
                return article_text
        except:
            return 'Failed to retrieve article content'
    # Apply content extraction to each article link
    df['Article content'] = df['Link'].apply(get_article_content)
    return df
