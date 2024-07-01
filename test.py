from utils.marketinsights import scrape_marketinsights
import pandas as pd
from datetime import datetime

df = scrape_marketinsights()

selection = 'marketinsights'
directory = "./utils/data/Scraped News/"
current_date = datetime.now().strftime("%Y-%m-%d")
file_path = f"{directory}/{selection}_data_{current_date}.csv"
df.to_csv(file_path, index=False)