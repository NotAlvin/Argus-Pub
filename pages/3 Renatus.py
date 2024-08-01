import os
import glob
import re
import pandas as pd
import streamlit as st
import textwrap
import ast

from utils.renatus import scrape_newsletters
from datetime import datetime, timedelta

def extract_date_from_filename(filename):
    # Use regex to extract the date from the filename
    match = re.search(r'\d{2}-\d{2}-\d{4}', filename)
    if match:
        date_str = match.group()
        # Parse the date string into a datetime object
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        return date_obj
    else:
        return None

def get_latest_file(directory, file_pattern):
    """
    Get the latest file in the directory that matches the file pattern.
    
    :param directory: Directory where to look for files.
    :param file_pattern: Pattern to match files (e.g., 'cnbc_data_*.csv').
    :return: Path to the latest file.
    """
    files = glob.glob(os.path.join(directory, file_pattern))
    if not files:
        return None
    latest_file = max(files, key=os.path.getctime)
    return latest_file

def load_or_scrape_file():
    # Directory and file pattern
    directory = "./utils/data/Renatus Newsletter/"
    file_pattern = f"renatus_*.csv"

    # Get the latest file
    latest_file = get_latest_file(directory, file_pattern)
    if datetime.strptime(latest_file.split('_')[-1].split('.')[0], '%d-%m-%Y') + timedelta(days=7) < datetime.today():
        scrape_newsletters()
    latest_file = get_latest_file(directory, file_pattern)
    df = pd.read_csv(latest_file)
    return df, latest_file

def format_markdown(paragraphs):
    markdown_articles = []
    for i, paragraph in enumerate(paragraphs, start=1):
        title = f"#### {paragraph.split('. ')[0]}".replace('Deal Details:', '').replace('Deal Details', '')
        paragraph = '. '.join([x.strip() for x in paragraph.replace('$', '\$').replace('Source', '\n Source: ').split('.')[1:]])
        #formatted_paragraph = "\n - " + paragraph.replace(". ", ".\n\n - ")
        markdown_articles.append(f"{title}\n\n{paragraph}")
    return "\n\n---\n\n".join(markdown_articles) + "\n\n---\n\n"

def string_to_markdown_table(s):
    # Define the labels
    labels = ["Who", "What", "Why", "Adviser", "Source"]

    # Split the string by the labels, keeping the labels
    parts = re.split(r'(Who:|What:|Why:|Adviser:|Source:)', s)
    
    # Filter out empty strings and strip whitespace
    parts = [part.strip() for part in parts if part.strip()]

    # Combine labels with their corresponding text
    data = dict(zip(parts[::2], parts[1::2]))

    # Create the markdown table
    markdown_table = "| Label | Details |\n|---|---|\n"
    for label in labels:
        markdown_table += f"| {label} | {data.get(label + ':', '')} |\n"

    return markdown_table

st.set_page_config(layout="wide")

df, filename = load_or_scrape_file()

# Streamlit dashboard
st.title("Latest Renatus Newsletter")
date_obj = extract_date_from_filename(filename)
if date_obj:
    formatted_date = date_obj.strftime('%B %d, %Y')
    # Display the date in a Streamlit header
    st.header(f"Newsletter Dated: {formatted_date}")

st.write("---")

df = df.drop('Unnamed: 0', axis = 1)
for header in df.columns:
    # Display each DataFrame
    st.subheader(header)
    df_temp = df[[header]]
    df_temp = df_temp.to_dict()
    content = ast.literal_eval(df_temp[header][0])

    if header == 'M&A Activity':
        st.write(format_markdown(content))
    
    elif header == 'Deal Updates & Other News':
        for paragraphs in content:
            st.write(paragraphs.replace('Deal Details:', '').replace('$', '\$'))
            st.write("---")
    else:
        for paragraphs in content:
            st.write(string_to_markdown_table(paragraphs))
            st.write("---")

    # links = ast.literal_eval(df_temp[header][1])
    # rows = zip(content, links)
    # displayed_df = pd.DataFrame(rows, columns = ['Content', 'Links'])
    # st.table(displayed_df['Content'].apply(lambda x: x.replace(':', ':\n\n')))