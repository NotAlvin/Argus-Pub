import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime
from utils.cnbc import scrape_cnbc
from utils.marketinsights import scrape_marketinsights
from utils.stockanalysis import scrape_stockanalysis

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

def load_or_scrape_file(selection, scrape = False):
    # Directory and file pattern
    directory = "./utils/data/Scraped News/"
    file_pattern = f"{selection}_data_*.csv"
    
    # Get the latest file
    latest_file = get_latest_file(directory, file_pattern)
    if latest_file and not scrape:
        df = pd.read_csv(latest_file)
    else:
        if selection == 'cnbc':
            df = scrape_cnbc()
        if selection == 'marketinsights':
            df = scrape_marketinsights()
        if selection == 'stockanalysis':
            df = scrape_stockanalysis()
        # Save the dataframe to a CSV file with the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_path = f"{directory}/{selection}_data_{current_date}.csv"
        df.to_csv(file_path, index=False)
    return df
