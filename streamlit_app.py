# streamlit_app.py

import streamlit as st
import pandas as pd
from event_processing import load_stations, generate_alerts

# --- Config ---
st.set_page_config(page_title="S-Bahn Event Alert System", layout="wide")
API_KEY = st.secrets["API_KEY"]

# --- Title ---
st.title("🚨 Hannover S-Bahn Event Impact Dashboard")
st.markdown("This dashboard shows which S-Bahn stations and lines in Hannover are likely to be impacted by upcoming public events.")

# --- Load Station Data ---
with st.spinner("Loading station data..."):
    stations_df = load_stations()

# --- Fetch & Display Events ---
if st.button("🔍 Fetch Upcoming Events"):
    with st.spinner("Fetching events from Ticketmaster..."):
        alerts_df = generate_alerts(API_KEY, stations_df)

    if not alerts_df.empty:
        st.success(f"Found {len(alerts_df)} relevant event(s) near S-Bahn stations.")
        st.dataframe(alerts_df, use_container_width=True)
    else:
        st.warning("No upcoming events found near S-Bahn stations.")
else:
    st.info("Click the button to fetch upcoming events.")

# --- Footer ---
st.markdown("---")
st.caption("Built for Transdev – powered by Streamlit, Ticketmaster API, and Hannover S-Bahn data.")
