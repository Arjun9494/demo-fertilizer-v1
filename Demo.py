#from snowflake.snowpark.context import get_active_session
#from snowflake.snowpark.functions import col
import streamlit as st
import pandas as pd
import altair as alt
import json
from snowflake.snowpark import Session
#import snowflake as sf
#from snowflake import connector
import snowflake.connector as sf

# Set page config
st.set_page_config(layout="wide")

# Get current session
#session = get_active_session()

if 'snowflake_connection' not in st.session_state:
    # connect to Snowflake
    with open('creds.json') as f:
        connection_parameters = json.load(f)
    st.session_state.snowflake_connection = Session.builder.configs(connection_parameters).create()
    session = st.session_state.snowflake_connection
else:
    session = st.session_state.snowflake_connection

@st.cache_data()
def load_data():
    # Load prediction data
    query = "SELECT CODE FROM STREAMLIT_APPS.PREDICATION.CONSUMPTION GROUP BY CODE"
    prediction_data = session.table("STREAMLIT_APPS.PREDICATION.CONSUMPTION").collect()
    prediction_df = pd.DataFrame(prediction_data)
    return prediction_df

def load_codes():
    query = "SELECT DISTINCT CODE FROM STREAMLIT_APPS.PREDICATION.CONSUMPTION"
    codes_data = session.sql(query).collect()
    codes_df = pd.DataFrame(codes_data)
    return codes_df

def consumption_page():
    st.subheader('Fertilizer Consumption')
    unique_codes = load_codes()
    available_countries = unique_codes['CODE'].tolist()

    selected_countries = st.multiselect('Select Countries', available_countries, default=available_countries[:4])  # Default first 4 countries

    selected_year = st.slider('Select Year', min_value=1970, max_value=2019, value=2019, step=1)

    st.markdown("___")

    # Load data
    df_predicationdata = load_data()

    # Extract year from datetime 'YEAR' column
    df_predicationdata['YEAR'] = pd.to_datetime(df_predicationdata['YEAR']).dt.year

    # Filter data based on selected year
    df_predicationdata_filtered = df_predicationdata[df_predicationdata['CODE'].isin(selected_countries) & (df_predicationdata['YEAR'] <= selected_year)]

    #st.write(df_predicationdata_filtered)
    
    # Display an interactive chart to visualize fertilizer consumption for the selected year and countries
    if not df_predicationdata_filtered.empty:
        with st.container():
            line_chart = alt.Chart(df_predicationdata_filtered).mark_line(color="lightblue", point=alt.OverlayMarkDef(color="red")).encode(
                x='YEAR',
                y='FERTILIZER_QUANTITY',
                color='CODE',
                tooltip=['CODE', 'YEAR', 'FERTILIZER_QUANTITY']
            )
            st.altair_chart(line_chart, use_container_width=True)
    else:
        st.write("No data available for the selected year and countries.")

def select_code_page():
    st.header('Fertilizer Quantity and Prediction Line Chart')
    unique_codes = load_codes()
    available_codes = unique_codes['CODE'].tolist()

    selected_code = st.selectbox("Select CODE", available_codes)

    selected_year = st.slider('Select Year', min_value=1970, max_value=2019, value=2019, step=1)

    # Load data for the selected code
    df_predicationdata = load_data()

    # Extract year from datetime 'YEAR' column
    df_predicationdata['YEAR'] = pd.to_datetime(df_predicationdata['YEAR'])
    df_predicationdata['YEAR'] =df_predicationdata['YEAR'].apply(lambda x:x.year)

    df_filtered = df_predicationdata[(df_predicationdata['CODE'] == selected_code) & (df_predicationdata['YEAR'] <= selected_year)]
   
 
    if 'FERTILIZER_QUANTITY' in df_filtered.columns and 'PRED_QUANTITY' in df_filtered.columns:
        st.title(f'Fertilizer Quantity and Prediction Line Chart for {selected_code}')
        st.line_chart(df_filtered[['YEAR', 'FERTILIZER_QUANTITY', 'PRED_QUANTITY']].set_index('YEAR'))
    else:
        st.write("Required columns not present in the data.")

# Display the two pages
page = st.sidebar.selectbox(
    "Select Page",
    ("Fertilizer Consumption", "Fertilizer Predication")
)

if page == "Fertilizer Predication":
    select_code_page()
else:
    consumption_page()
