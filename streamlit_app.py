# streamlit_app.py

import streamlit as st
import pandas as pd
import pydeck as pdk
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

        # --- Add Map ---
        st.subheader("🗺️ Event Impact Map (Stations)")
        alerts_df['Latitude'] = alerts_df['Latitude'].astype(float)
        alerts_df['Longitude'] = alerts_df['Longitude'].astype(float)

        # Map color based on impact
        def impact_color(level):
            if level == 'HIGH':
                return [255, 0, 0]
            elif level == 'MEDIUM':
                return [255, 165, 0]
            else:
                return [0, 128, 0]

        alerts_df['Color'] = alerts_df['Impact Level'].apply(impact_color)

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=alerts_df,
            get_position='[Longitude, Latitude]',
            get_color='Color',
            get_radius=300,
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=alerts_df['Latitude'].mean(),
            longitude=alerts_df['Longitude'].mean(),
            zoom=11,
            pitch=0
        )

        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"text": "{Event} @ {Venue}\nImpact: {Impact Level}"}
        ))

    else:
        st.warning("No upcoming events found near S-Bahn stations.")
else:
    st.info("Click the button to fetch upcoming events.")

# --- Footer ---
st.markdown("---")
st.caption("Built for Transdev – powered by Streamlit, Ticketmaster API, and Hannover S-Bahn data.")
