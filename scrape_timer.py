import schedule
import time
import csv
import os
import shutil
from datetime import datetime, timedelta
from utils.pipeline import load_or_scrape_file

def generate_csv():
    # Define the directory and archive folder
    print("Moving files")
    directory = os.getcwd() 
    directory = os.path.join(directory, 'utils/data/Scraped News')
    archive_folder = os.path.join(directory, 'Archive')
    # Create the archive folder if it doesn't exist
    if not os.path.exists(archive_folder):
        os.makedirs(archive_folder)
    
    # Move existing CSV files to the archive folder
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            shutil.move(os.path.join(directory, filename), os.path.join(archive_folder, filename))
    print(f"Files moved to {archive_folder}")
    # Load or scrape files from sources
    for source in ['stockanalysis']:#['cnbc', 'marketinsights', 'stockanalysis']:
        print(f'Generating {source} file')
        load_or_scrape_file(source, scrape=True)
    return


if __name__ == "__main__":
    # Schedule the job every week
    schedule.every().week.do(generate_csv)

    # Run the script immediately
    generate_csv()

    while True:
        schedule.run_pending()
        now = datetime.now()
        next_run = schedule.next_run()  # Get the time of the next scheduled run
        if next_run:
            sleep_time = (next_run - now).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)