import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.pipeline import load_or_scrape_file
from utils.marketinsights import safe_literal_eval
from io import BytesIO

def to_excel(cutoff_date):
    for source in ("CNBC", "Market Insights", "Stock Analysis"):
    # Filter the DataFrame based on the selected number of days
        news_df = load_or_scrape_file(source.replace(' ', '').lower())
        news_df['Time'] = pd.to_datetime(news_df['Time'])
        if source == 'CNBC':
            df1 = news_df[news_df['Time'] >= cutoff_date][['Time', 'Title', 'Article content', 'Source', 'Link']]
        if source == 'Market Insights':
            df2 = news_df[news_df['Time'] >= cutoff_date][['Time', 'title', 'Article content', 'source', 'link', 'ticker', 'Executives', 'Shareholders']]
        if source == 'Stock Analysis':
            df3 = news_df[news_df['Time'] >= cutoff_date][['Time', 'Title', 'Description', 'Source', 'Tickers', 'Executives', 'Country', 'Industry','Sector']]
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df1.to_excel(writer, index=False, sheet_name='CNBC')
    df2.to_excel(writer, index=False, sheet_name='Market Insights')
    df3.to_excel(writer, index=False, sheet_name='Stock Analysis')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="centered",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="expanded",  # Can be "auto", "expanded", "collapsed"
	page_title='News',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)

# Streamlit dashboard
st.title("Latest Liquidity Event News 🗞️")
st.write("---")

st.sidebar.header("Filter News")
max_days = st.sidebar.slider("Select how many past days of news to display:", 1, 7, 7)
load_news_button = st.sidebar.button("Load News")
source = st.sidebar.radio("Choose a news source", ("CNBC", "Market Insights", "Stock Analysis"))

news_df = load_or_scrape_file(source.replace(' ', '').lower())
news_df['Time'] = pd.to_datetime(news_df['Time'])

def explode_col(col_name):
    if col_name != col_name:
        return list(safe_literal_eval(col_name).values())
    else:
        return col_name
if load_news_button:
    cutoff_date = datetime.now() - timedelta(days=max_days)
    
    # Filter the DataFrame based on the selected number of days
    if source == 'CNBC':
        filtered_news_df = news_df[news_df['Time'] >= cutoff_date][['Time', 'Title', 'Article content', 'Source', 'Link']]
    if source == 'Market Insights':
        filtered_news_df = news_df[news_df['Time'] >= cutoff_date][['Time', 'title', 'Article content', 'source', 'link', 'ticker', 'Executives', 'Shareholders']]
    if source == 'Stock Analysis':
        filtered_news_df = news_df[news_df['Time'] >= cutoff_date][['Time', 'Title', 'Description', 'Source', 'Tickers', 'Executives', 'Country', 'Industry','Sector']]
    # Display the entire filtered dataframe
    st.dataframe(filtered_news_df)

    excel_data = to_excel(cutoff_date)
    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"filtered_data_{cutoff_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.write(f"Select a news lookback period in the sidebar to load the news!")