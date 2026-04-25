import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- CONFIG & SECURITY ---
if "RENTCAST_API_KEY" in st.secrets:
    API_KEY = st.secrets["RENTCAST_API_KEY"]
else:
    API_KEY = "MxqmSWaOPvVaAXPEt42aXrhvP4McBq"

st.set_page_config(layout="wide", page_title="Melopros | ROI Scout")

# --- DATA ENGINE ---
def fetch_properties(state_code, min_p, max_p):
    url = f"https://api.rentcast.io/v1/listings/sale?state={state_code}&minPrice={min_p}&maxPrice={max_p}&limit=50&status=Active"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except:
        return []

# --- LANDLORD-FRIENDLY STATES ---
LANDLORD_STATES = {"FL": "3-Day Notice", "MO": "High Yields", "TX": "Fast Evictions", "AZ": "Strong Growth", "OH": "Low Entry", "IN": "Stable", "KY": "Easy Logic", "NC": "Migration", "CO": "72-Hr Notice", "AL": "Low Tax", "GA": "7-Day Notice"}

# --- SIDEBAR: FILTERS ---
st.sidebar.title("🛡️ Melopros Guard")
selected_state = st.sidebar.selectbox("Target State", list(LANDLORD_STATES.keys()))

st.sidebar.subheader("💰 Budget & ROI Target")
min_price = st.sidebar.number_input("Min Price ($)", value=50000)
max_price = st.sidebar.number_input("Max Price ($)", value=500000)
roi_target = st.sidebar.slider("ROI Target: More than (%)", 1, 50, 10)

st.sidebar.subheader("🏦 Financing")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0)

search_button = st.sidebar.button("🔍 Scout Market", use_container_width=True)

# --- MAIN UI ---
col_map, col_ctrl = st.columns([2, 1])

with col_map:
    st.title(f"Scouting {selected_state} for >{roi_target}% ROI")
    
    if search_button:
        with st.spinner("Analyzing market yields..."):
            data = fetch_properties(selected_state, min_price, max_price)
            if data:
                df = pd.DataFrame(data)
                # ROI Calculation Logic
                df['est_rent'] = df['price'] * 0.01 # Simple 1% rule for scouting
                df['annual_cf'] = (df['est_rent'] * 12) - (df['price'] * 0.02) # Less 2% for tax/ins
                df['roi'] = (df['annual_cf'] / (df['price'] * (dp_pct/100))) * 100
                
                # FILTER: Only show ROI higher than target
                df = df[df['roi'] >= roi_target]
                
                if not df.empty:
                    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                    st.success(f"Found {len(df)} properties hitting your {roi_target}% goal!")
                    
                    st.pydeck_chart(pdk.Deck(
                        map_style='mapbox://styles/mapbox/dark-v9',
                        initial_view_state=pdk.ViewState(latitude=df['lat'].mean(), longitude=df['lon'].mean(), zoom=6),
                        tooltip={"text": "{address}\nROI: {roi:.2f}%"},
                        layers=[pdk.Layer(
                            'ScatterplotLayer',
                            data=df,
                            get_position='[lon, lat]',
                            get_color='[0, 255, 120, 200]', # Bright Green
                            get_radius='roi * 500', # Higher ROI = Bigger Dot!
                            pickable=True
                        )]
                    ))
                else:
                    st.error(f"No properties in {selected_state} meet the {roi_target}% ROI target. try lowering the target or increasing the budget.")
            else:
                st.warning("No properties found. Try a broader budget.")

with col_ctrl:
    st.subheader("🤝 Featured Pro")
    if selected_state == "FL":
        st.info("**Roberta Melo**\n\nInvestment Specialist")
        st.write("Ready to tour these high-ROI picks?")
        st.button("Contact Roberta")
