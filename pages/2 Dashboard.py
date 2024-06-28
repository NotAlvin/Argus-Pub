import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="expanded",  # Can be "auto", "expanded", "collapsed"
	page_title='Historical Dashboard 🔍',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)

def to_excel(df1, df2):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df1.to_excel(writer, index=False, sheet_name='Deals')
    df2.to_excel(writer, index=False, sheet_name='IPOs')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# Load the data
cb_deals = pd.read_csv('./utils/data/CB Insights/cleaned_cb_deals.csv')
ipo_data = pd.read_csv('./utils/data/IPO dataset/ipo_dataset.csv')

# Ensure 'Deal Date' is in datetime format
cb_deals['Deal Date'] = pd.to_datetime(cb_deals['Deal Date'])
ipo_data['IPO Date'] = pd.to_datetime(ipo_data['IPO Date'])

# Streamlit app
st.title("Historical Dashboard 🔍")

# Sidebar filters
st.sidebar.title("Filters")
st.sidebar.header("Deals")

# Multiselect with 'All' option for Industry
all_industries = ['All'] + sorted(list(map(lambda x:str(x), cb_deals['Industry'].unique())))
selected_industries = st.sidebar.multiselect("Select Industry", all_industries, default=["All"])

# Multiselect with 'All' option for Country
all_countries = ['All'] + sorted(list(map(lambda x:str(x), cb_deals['Country'].unique())))
selected_countries = st.sidebar.multiselect("Select Country", all_countries, default=["All"])

# Entry box for minimum deal size
min_deal_size = st.sidebar.number_input("Minimum Deal Size (M)", min_value=0, step=1, value=0)

# Multiselect with 'All' option for Country
investment_stage = ['All'] + sorted(list(set(map(lambda x: str(x).split('-')[0].strip(), cb_deals['Investment Stage']))))
selected_stage = st.sidebar.multiselect("Select Investment Stages", investment_stage, default=["All"])

# Sidebar filters
st.sidebar.header("IPOs")

# Multiselect with 'All' option for IPO Industry
all_ipo_industries = ['All'] + sorted(list(map(lambda x:str(x), ipo_data['Industry'].unique())))
selected_ipo_industries = st.sidebar.multiselect("Select IPO Industry", all_ipo_industries, default=["All"])

# Multiselect with 'All' option for IPO Country
all_ipo_countries = ['All'] + sorted(list(map(lambda x:str(x), ipo_data['Country'].unique())))
selected_ipo_countries = st.sidebar.multiselect("Select IPO Country", all_ipo_countries, default=["All"])

# Apply filters
filtered_deals = cb_deals.copy()
if "All" not in selected_industries:
    filtered_deals = filtered_deals[filtered_deals['Industry'].isin(selected_industries)]
if "All" not in selected_countries:
    filtered_deals = filtered_deals[filtered_deals['Country'].isin(selected_countries)]
if "All" not in selected_stage:
    filtered_deals = filtered_deals[filtered_deals['Investment Stage'].apply(lambda x: x.split('-')[0].strip()).isin(selected_stage)]

filtered_deals = filtered_deals.dropna(subset=['Deal Size (M)'])  # Drop rows where 'Deal Size (M)' is NaN
filtered_deals = filtered_deals[filtered_deals['Deal Size (M)'] >= min_deal_size]

# Filter IPOs based on selected filters
filtered_ipos = ipo_data.copy()
if "All" not in selected_ipo_industries:
    filtered_ipos = filtered_ipos[filtered_ipos['Industry'].isin(selected_ipo_industries)]
if "All" not in selected_ipo_countries:
    filtered_ipos = filtered_ipos[filtered_ipos['Country'].isin(selected_ipo_countries)]

# Date range selection
date_string = "2024-04-19"
end_date = pd.to_datetime(date_string)
start_date = (end_date - timedelta(days=365)).date()  # Default start date is one year ago
end_date = end_date.date()  # Default end date is today

# Initialize selected_date_range with None
selected_date_range = None

# Date input widget
selected_date_range = st.date_input("Select date range:", value=(start_date, end_date))

# Convert selected_date_range to datetime format
try:
    start_date_dt = datetime.combine(selected_date_range[0], datetime.min.time())
except:
    st.header('Select start of date range')
try:
    end_date_dt = datetime.combine(selected_date_range[1], datetime.max.time())
    if start_date_dt <= end_date_dt:
        # Filter deals for the selected date range
        deals_in_range = filtered_deals[
            (filtered_deals['Deal Date'] >= start_date_dt) &
            (filtered_deals['Deal Date'] <= end_date_dt)
        ]
        ipos_in_range = filtered_ipos[
            (filtered_ipos['IPO Date'] >= start_date_dt) &
            (filtered_ipos['IPO Date'] <= end_date_dt)
        ]

        

        # Create a dataframe to count deals and IPOs per day
        deal_counts = deals_in_range.groupby(deals_in_range['Deal Date'].dt.date).size()
        ipo_counts = ipos_in_range.groupby(ipo_data['IPO Date'].dt.date).size()

        # Ensure all dates between start_date_dt and end_date_dt are included
        all_dates = pd.date_range(start=start_date_dt, end=end_date_dt, freq='D')
        daily_counts = pd.DataFrame({
            'Date': all_dates,
            'Number of Deals': deal_counts.reindex(all_dates, fill_value=0).values,
            'Number of IPOs': ipo_counts.reindex(all_dates, fill_value=0).values
        })

        # Plot number of deals and IPOs per day in the selected date range using plotly
        fig = go.Figure()
        fig.add_trace(go.Bar(x=daily_counts['Date'], y=daily_counts['Number of Deals'], name='Number of Deals'))
        fig.add_trace(go.Bar(x=daily_counts['Date'], y=daily_counts['Number of IPOs'], name='Number of IPOs'))
        fig.update_layout(title='Number of Deals and IPOs per Day', xaxis_title='Date', yaxis_title='Count', barmode='stack', width = 1500)
        st.plotly_chart(fig)

        selected_date = st.date_input("Select a Date to display deals:", value=daily_counts['Date'].min(), min_value=daily_counts['Date'].min(), max_value=daily_counts['Date'].max())
        selected_date = selected_date if selected_date else None

        if st.button("Display Deals"):
            if selected_date:
                deals_of_the_day = deals_in_range[
                    (deals_in_range['Deal Date'].dt.date > selected_date - timedelta(days=1)) &
                    (deals_in_range['Deal Date'].dt.date < selected_date + timedelta(days=1))
                ]
                if not deals_of_the_day.empty:
                    deals_of_the_day['Deal Size (M)'] = deals_of_the_day['Deal Size (M)'].astype(int)
                    st.write(f"Deals of the Day for {selected_date}:")
                    if 'All' in selected_industries:
                        st.table(deals_of_the_day[['Deal Size (M)', 'Companies', 'Company Status', 'Industry', 'Description', 'All People', 'All Investors']].assign(hack='').set_index('hack'))
                    else:
                        for industry in selected_industries:
                            temp = deals_of_the_day[deals_of_the_day['Industry'] == industry]
                            if len(temp) > 0:
                                st.header(f"{industry}")
                                st.table(temp[['Deal Size (M)', 'Companies', 'Company Status', 'Description', 'All People', 'All Investors']].assign(hack='').set_index('hack'))
                else:
                    st.write(f"No deals around {selected_date}.")
                # Display IPOs for the selected date
                ipos_of_the_day = ipos_in_range[
                    (ipo_data['IPO Date'].dt.date > selected_date - timedelta(days=1)) &
                    (ipo_data['IPO Date'].dt.date < selected_date + timedelta(days=1))
                ]
                if not ipos_of_the_day.empty:
                    st.write(f"IPOs on {selected_date}:")
                    st.table(ipos_of_the_day[['Company Name', 'Industry', 'Description', 'Related People']].assign(hack='').set_index('hack'))
                else:
                    st.write(f"No IPOs on {selected_date}.")
                
                # Add download button
                a = deals_of_the_day.copy()
                b = ipos_of_the_day.copy()
                a['Deal Date'] = str(selected_date)
                b['IPO Date'] = str(selected_date)
                excel_data = to_excel(a, b)
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"filtered_data_{selected_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("Select a date from the dropdown to display deal information.")
    else:
        st.write("Please select a valid date range.")
except:
    st.write('Select end of date range')