import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
from ast import literal_eval
from datetime import datetime
from io import BytesIO

def safe_literal_eval(x):
    """
    Safely evaluate a string representation of a Python dictionary.
    """
    if x is None:
        return {}
    if pd.isna(x):
        return {}
    try:
        return literal_eval(x)
    except (ValueError, SyntaxError):
        return {}

def to_excel(df1, df2, df3):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df1.to_excel(writer, index=False, sheet_name='CNBC')
    df2.to_excel(writer, index=False, sheet_name='Market Insights')
    df3.to_excel(writer, index=False, sheet_name='Stock Analysis')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def get_country_mapping():
    url = "https://www.countrycode.org"
    response = requests.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table
    table = soup.find('table')

    # Extract the table headers
    headers = []
    for th in table.find_all('th'):
        headers.append(th.text.strip())

    # Extract the table rows
    rows = []
    for tr in table.find_all('tr'):
        cells = tr.find_all('td')
        row = [cell.text.strip() for cell in cells]
        if row:
            rows.append(row)

    # Create a DataFrame
    df = pd.DataFrame(rows, columns=headers)
    return df

def get_country(storage, mapping):
    phone_number = safe_literal_eval(storage)['Phone Number']
    extension = phone_number.split(' ')[0]
    if '+' not in extension:
        return 'Unknown'
    else:
        

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

def process_names(names):
    elements = [element for element in names.split(' ') if element]
    name = elements[:-1]
    return ' '.join(name)

def scrape_url(url):
    url = url.split('news')[0] + 'company/'
    """
    Scrapes tables of managers, members of the board, and shareholders from a given URL.
    Returns a dictionary with the extracted data.
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    html_content = urllib.parse.unquote(response.text)
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

def scrape_tables(soup):
    to_find = {'Managers': None, 'Members of the board': None, 'Name': None}
    tables = soup.find_all('div', class_='card-content')
    for table in tables:
        try:
            title = table.find('tr').find('th').get_text(strip=True)
            headers = [header.get_text(strip = True) for header in table.find_all('th')]
            if title in to_find.keys():
                temp_table = table.find('table')
                rows = temp_table.find('tbody').find_all('tr')
                data = []
                for row in rows:
                    cols = row.find_all('td')
                    data.append([col.get_text().replace('\n', '').strip() for col in cols])

                df = pd.DataFrame(data, columns=headers)
                df[title] = df[title].apply(process_names)
                if title != 'Name':
                    to_find[title] = df.to_dict()
                else:
                    if 'Valuation' in headers:
                        to_find['Shareholders'] = df.to_dict()
                        break
        except Exception:
            pass
    return to_find

def get_industry(soup):
    # Locate all card-header divs
    card_headers = soup.find_all('div', class_='card-header')

    # Iterate through each card-header div and extract the required information
    for card_header in card_headers:
        try:
            # Get the title text from the card-header div
            title_text = card_header.get_text(strip=True)
            if title_text == 'Sector':
                # Find the next sibling card-content div
                card_content = card_header.find_next_sibling('div', class_='card-content')
                
                if card_content:
                    # Get the sector details from the card-content div
                    sector_details = list(map(lambda x: x.strip(), card_content.get_text().split('\n')))
                    actual = ''
                    for sector in sector_details:
                        if sector:
                            actual = sector
        except:
            pass
    return actual

def get_contact_information(soup):
    result = {}
    # Find the div with class 'card-content'
    contact_info_div = soup.find_all('div', class_ = 'card mb-15')
    for div in contact_info_div:
        try:
        # Extract the paragraphs within this div
            contact_info_paragraphs = div.find_all('p', class_='m-0')
            if contact_info_paragraphs:
                
                company_name = contact_info_paragraphs[0].text
                address_line_1 = contact_info_paragraphs[1].text
                address_line_2 = contact_info_paragraphs[2].text
                phone_number = contact_info_paragraphs[3].text

                # Extract the website URL
                website = div.find('a', class_='m-0')['href']

            # Print the extracted information
            result['Company Name'] = company_name
            result['Address Line 1'] = address_line_1
            result['Address Line 2'] = address_line_2
            result['Phone Number'] = phone_number
            result['Website'] = website
        except:
            pass
    return result

# Add a 'Type' column to distinguish between Managers and Board members
def process_temp_df(df):
    name = df.columns[0]
    df.columns = ['Name'] + list(df.columns[1:])
    df['Executive Functions'] = name
    return df

def process_tables(data):
    data = safe_literal_eval(data)
    # Extract and flatten the nested dictionaries
    if 'Managers' in data.keys() or 'Members of the board' in data.keys():
        managers_data = data['Managers']
        board_data = data['Members of the board']
        if managers_data:
        # Convert to DataFrames
            managers_df = pd.DataFrame(managers_data)
            managers_df = process_temp_df(managers_df)
            if board_data:
                board_df = pd.DataFrame(board_data)
                board_df = process_temp_df(board_df)
        
                # Concatenate the DataFrames
                temp_df = pd.concat([managers_df, board_df], ignore_index=True)
            else:
                temp_df = board_df

            df_combined = temp_df.groupby(['Name', 'Title']).agg({
                'Age': 'first',  # Take the first non-null value for 'Age'
                'Since': 'first',  # Take the first non-null value for 'Since'
                'Executive Functions': lambda x: ', '.join(sorted(set(x)))  # Combine and sort unique 'Type' values
            }).reset_index()

            df_combined.index = df_combined['Name']

            executive_list = df_combined.to_dict(orient = 'split')['data']
        else:
            executive_list = []
    else:
        executive_list = []
        
    if 'Shareholders' in data.keys():
        shareholder_data = data['Shareholders']
        shareholder_df = pd.DataFrame(shareholder_data)
        shareholder_list = shareholder_df.to_dict(orient = 'split')['data']
    else:
        shareholder_list = []

    return executive_list, shareholder_list

def scrape_marketinsights():
    country_mapping = get_country_mapping()

    df = scrape_main_page_marketinsights()

    df['raw'] = df['link'].apply(scrape_url)
    df['Contact Info'] = df['raw'].apply(get_contact_information)
    df['Country'] = df['Contact Info']
    df['Industry'] = df['raw'].apply(get_industry)
    df['tables'] = df['raw'].apply(scrape_tables)
    df_temp = df['tables'].apply(lambda x: pd.Series(process_tables(x)))

    df_temp.columns = ['Executives', 'Shareholders']
    df = pd.concat([df, df_temp], axis = 1)

    # Function to convert time strings to datetime using the current date
    def convert_to_datetime(date_str):
        formats = ['%I:%M%p', '%b. %d', '%Y-%m-%d']
        current_year = datetime.now().year
        for fmt in formats:
            try:
                # If the date string is in time format, assume it's from the current date
                if fmt == '%I:%M%p':
                    return datetime.combine(datetime.today(), datetime.strptime(date_str, fmt).time())
                elif fmt == '%b. %d':
                # Append the current year to the date string
                    date_str_with_year = f"{date_str} {current_year}"
                    return datetime.strptime(date_str_with_year, f"{fmt} %Y")
                else:
                    return datetime.strptime(date_str, fmt)
            except ValueError:
                pass
        # If none of the formats match, return None
        return None

    # Apply the conversion functions
    df['Time'] = df['date'].apply(convert_to_datetime)
    df.drop(['date'], axis = 1)
    return df