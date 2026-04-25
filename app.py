import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- 1. SECURE API CONFIG ---
# This looks for your key in Streamlit Cloud > Settings > Secrets
if "RENTCAST_API_KEY" in st.secrets:
    API_KEY = st.secrets["RENTCAST_API_KEY"]
else:
    API_KEY = "MxqmSWaOPvVaAXPEt42aXrhvP4McBq" # Your fallback key

st.set_page_config(layout="wide", page_title="Melopros | ROI Scout")

# --- 2. DATA ENGINE ---
def fetch_properties(state_code, min_p, max_p):
    """Fetches up to 50 active listings from RentCast."""
    url = f"https://api.rentcast.io/v1/listings/sale?state={state_code}&minPrice={min_p}&maxPrice={max_p}&limit=50&status=Active"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# --- 3. LANDLORD-FRIENDLY INTEL ---
LANDLORD_STATES = {
    "FL": "3-Day Notice | No State Income Tax",
    "MO": "High Rent-to-Price | Landlord Friendly",
    "TX": "Fast Evictions | Strong Appreciation",
    "AZ": "5-Day Non-compliance | Population Growth",
    "OH": "Low Entry Point | Stable Cashflow"
}

# --- 4. SIDEBAR FILTERS ---
st.sidebar.title("🛡️ Melopros Guard")
selected_state = st.sidebar.selectbox("Select Target State", list(LANDLORD_STATES.keys()))
st.sidebar.info(f"Market Intel: {LANDLORD_STATES[selected_state]}")

st.sidebar.divider()
st.sidebar.subheader("💰 Budget & ROI Target")
min_price = st.sidebar.number_input("Min Price ($)", value=50000, step=10000)
max_price = st.sidebar.number_input("Max Price ($)", value=400000, step=25000)
roi_target = st.sidebar.slider("ROI Target: More than (%)", 1, 20, 5)

st.sidebar.subheader("🏦 Financing")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0, step=0.1)

search_button = st.sidebar.button("🔍 Scout Market", use_container_width=True)

# --- 5. MAIN UI LAYOUT ---
col_map, col_ctrl = st.columns([2.5, 1])

with col_map:
    st.title(f"Scouting {selected_state} for >{roi_target}% ROI")
    
    if search_button:
        with st.spinner("Analyzing market data..."):
            data = fetch_properties(selected_state, min_price, max_price)
            
            if data:
                df = pd.DataFrame(data)
                
                # --- ROI CALCULATION (REAL-WORLD MODEL) ---
                # Est Rent: 0.8% of price | OpExp: 35% of Rent | ROI based on Cash Invested
                df['est_rent'] = df['price'] * 0.008
                df['op_exp'] = df['est_rent'] * 0.35
                loan_amt = df['price'] * (1 - (dp_pct/100))
                df['mortgage'] = (loan_amt * (interest_rate/100)) / 12
                df['monthly_cf'] = df['est_rent'] - df['op_exp'] - df['mortgage']
                df['roi'] = (df['monthly_cf'] * 12 / (df['price'] * (dp_pct/100))) * 100
                
                # Filter by Target
                raw_count = len(df)
                df_filtered = df[df['roi'] >= roi_target].copy()
                
                if not df_filtered.empty:
                    # RENAME FOR MAP: This ensures the pins actually appear
                    df_filtered = df_filtered.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                    
                    st.success(f"Success! Found {len(df_filtered)} properties (Scanned {raw_count} total).")
                    
                    # MAP VISUAL
                    st.pydeck_chart(pdk.Deck(
                        map_style='mapbox://styles/mapbox/dark-v9',
                        initial_view_state=pdk.ViewState(
                            latitude=df_filtered['lat'].mean(), 
                            longitude=df_filtered['lon'].mean(), 
                            zoom=6, 
                            pitch=45
                        ),
                        tooltip={"text": "{address}\nPrice: ${price}\nROI: {roi:.2f}%"},
                        layers=[pdk.Layer(
                            'ScatterplotLayer',
                            data=df_filtered,
                            get_position='[lon, lat]',
                            get_color='[0, 255, 120, 200]', # High-performance Green
                            get_radius=5000,
                            pickable=True
                        )]
                    ))
                    st.dataframe(df_filtered[['address', 'price', 'roi', 'bedrooms', 'bathrooms']], use_container_width=True)
                else:
                    st.warning(f"Analyzed {raw_count} properties, but none met the {roi_target}% ROI target. Try lowering the target or raising your Max Price.")
            else:
                st.error("No data returned from API. Check if your Max Price is too low or your API key is active.")
    else:
        st.info("Set your filters and click 'Scout Market' to start.")

with col_ctrl:
    st.subheader("🤝 Featured Expert")
    if selected_state == "FL":
        st.info("**Roberta Melo**\nInvestment REALTOR®")
        st.write("Ready to tour high-ROI picks in Winter Garden or Lake Nona?")
        st.link_button("Contact Roberta", "https://wa.me/13219007539")
    else:
        st.write("Looking for a local pro?")
        st.button("Join Melopros Network")
