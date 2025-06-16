# event_processing.py

import pandas as pd
import math
import requests

# --- Load S-Bahn Station Data ---
def load_stations(filepath="hannover_sbahn_with_coords.xlsx"):
    df = pd.read_excel(filepath)
    return df

# --- Fetch Events from Ticketmaster API ---
def get_big_events(api_key, city="Hannover", country="DE", size=50):
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': api_key,
        'city': city,
        'countryCode': country,
        'size': size
    }
    response = requests.get(url, params=params)
    data = response.json()
    events = []
    if '_embedded' in data:
        for event in data['_embedded']['events']:
            name = event.get('name', '')
            genre = event.get('classifications', [{}])[0].get('segment', {}).get('name', '')
            venue = event['_embedded']['venues'][0].get('name', '')
            date = event['dates']['start'].get('localDate', '')
            time_ = event['dates']['start'].get('localTime', '')
            lat = event['_embedded']['venues'][0]['location'].get('latitude')
            lon = event['_embedded']['venues'][0]['location'].get('longitude')
            if lat and lon:
                if any(keyword in genre.lower() for keyword in ['music', 'sports', 'arts']) or \
                   any(x in venue.lower() for x in ['stadion', 'arena', 'theater', 'park', 'halle']):
                    events.append({
                        'Event': name,
                        'Genre': genre,
                        'Venue': venue,
                        'Date': date,
                        'Time': time_,
                        'Latitude': float(lat),
                        'Longitude': float(lon)
                    })
    return pd.DataFrame(events)

# --- Haversine Distance Helper ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# --- Get all lines for a station ---
def get_lines_for_station(station_name, df_stations):
    lines = df_stations[df_stations['Station'] == station_name]['S-Bahn Line'].unique()
    return '; '.join(lines)

# --- Nearest Station Logic ---
def find_nearest_station(event_row, station_df):
    min_dist = float('inf')
    nearest_station = None
    for _, station_row in station_df.iterrows():
        dist = haversine(event_row['Latitude'], event_row['Longitude'],
                         station_row['Latitude'], station_row['Longitude'])
        if dist < min_dist:
            min_dist = dist
            nearest_station = station_row['Station']
    station_lines = get_lines_for_station(nearest_station, station_df)
    return nearest_station, round(min_dist, 2), station_lines

# --- Final Alert Table ---
def generate_alerts(api_key, station_df, max_distance_km=3):
    df_events = get_big_events(api_key)
    if df_events.empty:
        return pd.DataFrame()  # No events found

    matches = df_events.apply(lambda row: find_nearest_station(row, station_df), axis=1)
    df_events['Nearest Station'] = matches.apply(lambda x: x[0])
    df_events['Distance (km)'] = matches.apply(lambda x: x[1])
    df_events['Lines'] = matches.apply(lambda x: x[2])

    df_alerts = df_events[df_events['Distance (km)'] <= max_distance_km]

    def classify_impact(venue):
        venue = venue.lower()
        if any(x in venue for x in ['arena', 'stadion', 'stadium', 'messe']):
            return 'HIGH'
        elif any(x in venue for x in ['theater', 'halle', 'park']):
            return 'MEDIUM'
        else:
            return 'LOW'

    df_alerts['Impact Level'] = df_alerts['Venue'].apply(classify_impact)
    df_alerts = df_alerts.drop_duplicates(subset=['Event', 'Date', 'Time'])

    return df_alerts[['Event', 'Date', 'Time', 'Venue', 'Nearest Station', 'Lines', 'Distance (km)', 'Impact Level']]
