import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
from ast import literal_eval
from datetime import datetime

def scrape_main_page_marketinsights():
    """
    Scrapes market insights from MarketScreener and extracts article content.
    Returns a DataFrame with the extracted data.
    """
    def extract_marketscreener_article(url):
        """
        Extracts the article text from a MarketScreener article URL.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
        except:
            return 'Error with URL GET request (Could be blocked)'
        
        html_content = urllib.parse.unquote(response.text)
        soup = BeautifulSoup(html_content, 'html.parser')

        article_div = soup.find('div', class_='txt-s4 article-text')
        try:
            article_text = article_div.get_text(separator='\n', strip=True)
            return article_text
        except:
            return 'Error with extracting article text from URL'
        
    def marketinsights_table(url, headers):
        """
        Extracts table data from MarketScreener URL and returns it as a DataFrame.
        """
        response = requests.get(url, headers=headers)
        html_content = urllib.parse.unquote(response.text)
        soup = BeautifulSoup(html_content, 'html.parser') 

        table = soup.find('table')
        data = []

        for row in table.find_all('tr'):
            news_item = row.find('a', class_='link--no-underline')
            ticker_item = row.find('a', class_='link--blue')
            time_item = row.find('time')
            source_item = row.find('span', class_='badge--small')

            if news_item and ticker_item and time_item and source_item:
                data.append({
                    'title': news_item.get_text(strip=True),
                    'link': f'https://www.marketscreener.com{news_item["href"].strip()}',
                    'ticker': ticker_item.find('span', class_='txt-s1').get_text(strip=True),
                    'date': time_item.get_text(strip=True),
                    'source': source_item['title']
                })

        return pd.DataFrame(data)
    
    endpoint_list = ['IPO', 'mergers-acquisitions', 'rumors']
    df = pd.DataFrame()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
    }
    
    for endpoint in endpoint_list:
        url = f'https://www.marketscreener.com/news/companies/{endpoint}/'
        temp_df = marketinsights_table(url, headers)
        df = pd.concat([df, temp_df])
    
    df['Article content'] = df['link'].apply(extract_marketscreener_article)
    return df

def scrape_tables(url):
    """
    Scrapes tables of managers, members of the board, and shareholders from a given URL.
    Returns a dictionary with the extracted data.
    """
    def process_names(names):
        elements = [element for element in names.split(' ') if element]
        name = elements[:-1]
        role = f'({elements[-1]})'
        return ' '.join(name) + ' ' + role

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    html_content = urllib.parse.unquote(response.text)
    soup = BeautifulSoup(html_content, 'html.parser')

    to_find = {'Managers': None, 'Members of the board': None, 'Name': None}
    tables = soup.find_all('div', class_='card-content')

    for table in tables:
        try:
            title = table.find('tr').find('th').get_text(strip=True)
            if title in to_find.keys():
                temp_table = table.find('table')
                headers = [header.get_text(strip=True) for header in table.find_all('th')]
                rows = temp_table.find('tbody').find_all('tr')

                data = []
                for row in rows:
                    cols = row.find_all('td')
                    data.append([col.get_text().replace('\n', '').strip() for col in cols])

                df = pd.DataFrame(data, columns=headers)
                df[title] = df[title].apply(process_names)
                to_find[title] = df.to_dict()
        except:
            pass

    return to_find

def safe_literal_eval(x):
    """
    Safely evaluate a string representation of a Python dictionary.
    """
    if pd.isna(x) or x is None:
        return {}
    try:
        return literal_eval(x)
    except (ValueError, SyntaxError):
        return {}

def scrape_marketinsights():
    df = scrape_main_page_marketinsights()
    df['tables'] = df['link'].apply(lambda x: scrape_tables(x.split('news')[0] + 'company/'))

    # Apply the transformations with error handling
    df['Managers'] = df['tables'].apply(lambda x: safe_literal_eval(x).get('Managers', []))
    df['Members of the board'] = df['tables'].apply(lambda x: safe_literal_eval(x).get('Members of the board', []))
    df['Shareholders'] = df['tables'].apply(lambda x: safe_literal_eval(x).get('Name', []))

    current_date = datetime.now().date()

    # Function to convert time strings to datetime using the current date
    def convert_time_to_datetime(time_str):
        return datetime.strptime(f"{current_date} {time_str}", "%Y-%m-%d %I:%M%p")

    # Function to convert month-day strings to datetime
    def convert_month_day_to_datetime(date_str):
        return datetime.strptime(date_str, "%b. %d").replace(year=datetime.now().year)

    # Apply the conversion functions
    df['Time'] = df['date'].apply(
        lambda x: convert_time_to_datetime(x) if ":" in x else convert_month_day_to_datetime(x)
    )
    return df