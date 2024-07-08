import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.pipeline import load_or_scrape_file
from utils.marketinsights import safe_literal_eval
from xlsxwriter import Workbook
from io import BytesIO

def to_excel(df1, df2, df3):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df1.to_excel(writer, index=False, sheet_name='CNBC')
    df2.to_excel(writer, index=False, sheet_name='Market Insights')
    df3.to_excel(writer, index=False, sheet_name='Stock Analysis')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="expanded",  # Can be "auto", "expanded", "collapsed"
	page_title='News',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)


# Streamlit dashboard
st.title("Latest Liquidity Event News 🗞️")
st.write("---")

st.sidebar.header("Filter News")
max_days = st.sidebar.slider("Select how many past days of news to display:", 1, 7, 7)
cutoff_date = datetime.now() - timedelta(days=max_days)

load_news_button = st.sidebar.button("Load News")
source = st.sidebar.radio("Choose a news source", ("CNBC", "Market Insights", "Stock Analysis"))

for source2 in ("CNBC", "Market Insights", "Stock Analysis"):
    # Filter the DataFrame based on the selected number of days
    if source2 == 'CNBC':
        df1 = load_or_scrape_file(source2.replace(' ', '').lower())
        df1['Time'] = pd.to_datetime(df1['Time'])
        df1 = df1[df1['Time'] >= cutoff_date][['Time', 'Title', 'Article content', 'Link']]
    if source2 == 'Market Insights':
        df2 = load_or_scrape_file(source2.replace(' ', '').lower())
        df2['Time'] = pd.to_datetime(df2['Time'])
        df2 = df2[df2['Time'] >= cutoff_date][['Time', 'title', 'Article content', 'ticker', 'Executives', 'Shareholders', 'Country', 'Industry', 'link']]
    if source2 == 'Stock Analysis':
        df3 = load_or_scrape_file(source2.replace(' ', '').lower())
        df3['Time'] = pd.to_datetime(df3['Time'])
        df3 = df3[df3['Time'] >= cutoff_date][['Time', 'Title', 'Description', 'Tickers', 'Executives', 'Country', 'Industry', 'Image URL']]
# Filter dataframes
# Get unique industries and countries from both dataframes
unique_industries = pd.concat([df2['Industry'], df3['Industry']]).unique()
unique_countries = pd.concat([df2['Country'], df3['Country']]).unique()

default = {'Ireland', 'United Kingdom', 'Turkey', 'Sweden', 'Guernsey', 'Switzerland', 'Luxembourg', 'Monaco', 'Hong Kong', 'Singapore', 'Unknown'}

selected_industries = st.sidebar.multiselect("Select Industry", ["All"] + list(unique_industries), default=["All"])
selected_countries = st.sidebar.multiselect("Select Country", ["All", "Default"] + list(unique_countries), default=["All"])

def explode_col(col_name):
    if col_name != col_name:
        return list(safe_literal_eval(col_name).values())
    else:
        return col_name
    
if load_news_button:
        # Apply filters
    if "All" not in selected_industries:
        df2 = df2[df2['Industry'].isin(selected_industries)]
        df3 = df3[df3['Industry'].isin(selected_industries)]
    if "All" not in selected_countries:
        if "Default" in selected_countries:
            df2 = df2[df2['Country'].isin(set(selected_countries) | default)]
            df3 = df3[df3['Country'].isin(set(selected_countries) | default)]
        else:
            df2 = df2[df2['Country'].isin(selected_countries)]
            df3 = df3[df3['Country'].isin(selected_countries)]

    # Filter the DataFrame based on the selected number of days
    if source == 'CNBC':
        filtered_news_df = df1
    if source == 'Market Insights':
        filtered_news_df = df2
    if source == 'Stock Analysis':
        filtered_news_df = df3
    # Display the entire filtered dataframe
    st.dataframe(filtered_news_df)

    excel_data = to_excel(df1,df2,df3)
    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"filtered_data_{cutoff_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.write(f"Select a news lookback period in the sidebar to load the news!")