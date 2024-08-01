import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def extract_heading(section):
        heading = section.find('h2', class_='elementor-heading-title')
        return heading.get_text(strip=True) if heading else None

def extract_paragraphs(section):
    paragraphs = section.find_all('p')
    return [p.get_text(strip=True) for p in paragraphs]

def extract_lists(section):
    lists = section.find_all('ul')
    list_items = []
    for ul in lists:
        items = ul.find_all('li')
        list_items.append([item.get_text(strip=True) for item in items])
    return list_items

def extract_links(section):
    links = section.find_all('a')
    return [(link.get_text(strip=True), link.get('href')) for link in links]

def format_content(paragraphs, lists):
    content = "\n".join(paragraphs)
    for idx, list_items in enumerate(lists):
        content += f"\n\nList {idx + 1}:\n" + "\n".join([f"  - {item}" for item in list_items])
    return content

def process_section(section):
    heading = extract_heading(section)
    paragraphs = extract_paragraphs(section)
    lists = extract_lists(section)
    links = extract_links(section)
    content = format_content(paragraphs, lists)
    return {
        'Heading': heading,
        'Content': content,
        'Links': ", ".join([f"{text} ({url})" for text, url in links])
    }

def extract_relevant_sections(data, headings_of_interest):
    extracted_data = {}
    select = False
    current_heading = ""
    for entry in data:
        heading = entry.get('Heading')
        if heading in headings_of_interest:
            extracted_data[heading] = {'Content': [], 'Links': []}
            current_heading = heading
            select = True
            continue
        if select:
            if entry.get('Heading') is None:
                content = entry.get('Content', '')
                if content:
                    extracted_data[current_heading]['Content'].append(entry.get('Content', ''))
                    extracted_data[current_heading]['Links'].append(entry.get('Links', ''))
            else:
                select = False
    return extracted_data

# Function to fetch the latest newsletter content
def get_latest_newsletter(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f'Request failed with status code: {response.status_code}')
    
    soup = BeautifulSoup(response.text, 'html.parser')
    sections = soup.find_all('section')
    
    # Process sections

    data = [process_section(section) for section in sections]

    headings_of_interest = ['M&A Activity', 'Deal Updates & Other News', 'Fundraisings']
    extracted_data = extract_relevant_sections(data, headings_of_interest)

    df = pd.DataFrame(extracted_data)
    return soup, df

# Function to format the date for the URL
def get_formatted_dates(start_date):
    today = datetime.today()
    storage = [start_date.strftime('%d-%m-%Y')]
    while start_date < today:
        start_date = start_date + timedelta(days=7)
        storage.append(start_date.strftime('%d-%m-%Y'))
    return storage

# Function to generate the URL based on the formatted date
def generate_url(date_str):
    base_url = 'https://renatus.ie/renatus-private-equity-mampa-newsletter-'
    url = f'{base_url}{date_str}/'
    return url

def scrape_newsletters():
    print('test')
    start_date = datetime.strptime('16-06-2024', '%d-%m-%Y')
    formatted_dates = get_formatted_dates(start_date)
    print(formatted_dates)
    generated = False
    curr = -1
    while not generated:
        try:
            url = generate_url(formatted_dates[curr])
            print(f"Fetching newsletter from URL: {url}")
            soup, df = get_latest_newsletter(url)
            df.to_csv(f'./data/Renatus Newsletter/renatus_{formatted_dates[curr]}.csv')
            generated = True
        except Exception as e:
            curr -= 1
            print(e)
    

# Main block to fetch and print the latest newsletter
if __name__ == "__main__":
    scrape_newsletters()