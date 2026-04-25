import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- 1. CONFIG & SECURITY ---
if "RENTCAST_API_KEY" in st.secrets:
    API_KEY = st.secrets["RENTCAST_API_KEY"]
else:
    API_KEY = "MxqmSWaOPvVaAXPEt42aXrhvP4McBq"

st.set_page_config(layout="wide", page_title="Melopros | ROI Scout")

# --- 2. DATA ENGINE ---
def fetch_properties(state_code, min_p, max_p):
    # Added status=Active and increased limit to 50 for better sampling
    url = f"https://api.rentcast.io/v1/listings/sale?state={state_code}&minPrice={min_p}&maxPrice={max_p}&limit=50&status=Active"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- 3. LANDLORD-FRIENDLY INTEL ---
LANDLORD_STATES = {"FL": "No State Tax", "MO": "High Yields", "TX": "Fast Eviction", "AZ": "Growth", "OH": "Low Entry"}

# --- 4. SIDEBAR ---
st.sidebar.title("🛡️ Melopros Guard")
selected_state = st.sidebar.selectbox("Target Market", list(LANDLORD_STATES.keys()))

st.sidebar.divider()
st.sidebar.subheader("💰 Budget & ROI Target")
min_price = st.sidebar.number_input("Min Price ($)", value=50000)
max_price = st.sidebar.number_input("Max Price ($)", value=400000)
# Start with 1.0% ROI target to ensure results show up first
roi_target = st.sidebar.slider("ROI Target: More than (%)", 0.0, 15.0, 1.0)

st.sidebar.divider()
st.sidebar.subheader("🏦 Financing")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0)

search_button = st.sidebar.button("🔍 Scout Market", use_container_width=True)

# --- 5. MAIN UI ---
col_map, col_ctrl = st.columns([2.5, 1])

with col_map:
    st.title(f"Scouting {selected_state} for >{roi_target}% ROI")
    
    if search_button:
        with st.spinner(f"Requesting data for {selected_state}..."):
            data = fetch_properties(selected_state, min_price, max_price)
            
            if data:
                df = pd.DataFrame(data)
                
                # --- CALCULATION ENGINE ---
                # Est Rent (0.8%) - OpExp (35%) - Mortgage (7%)
                df['est_rent'] = df['price'] * 0.008
                df['op_exp'] = df['est_rent'] * 0.35
                loan_amt = df['price'] * (1 - (dp_pct/100))
                df['mortgage'] = (loan_amt * (interest_rate/100)) / 12
                df['monthly_cf'] = df['est_rent'] - df['op_exp'] - df['mortgage']
                df['roi'] = (df['monthly_cf'] * 12 / (df['price'] * (dp_pct/100))) * 100
                
                # Filter by ROI
                df_filtered = df[df['roi'] >= roi_target].copy()
                
                if not df_filtered.empty:
                    # FIX: Map requires 'lat' and 'lon' names
                    df_filtered = df_filtered.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                    st.success(f"Found {len(df_filtered)} deals hitting your {roi_target}% target!")
                    
                    st.pydeck_chart(pdk.Deck(
                        map_style='mapbox://styles/mapbox/dark-v9',
                        initial_view_state=pdk.ViewState(latitude=df_filtered['lat'].mean(), longitude=df_filtered['lon'].mean(), zoom=6),
                        tooltip={"text": "{address}\nROI: {roi:.2f}%"},
                        layers=[pdk.Layer(
                            'ScatterplotLayer',
                            data=df_filtered,
                            get_position='[lon, lat]',
                            get_color='[0, 255, 120, 200]',
                            get_radius=5000,
                            pickable=True
                        )]
                    ))
                    # SHOW TABLE FOR VERIFICATION
                    st.write("### Raw Data Scan")
                    st.dataframe(df_filtered[['address', 'price', 'roi']], use_container_width=True)
                else:
                    st.warning(f"API found {len(df)} houses, but 0 met your {roi_target}% ROI goal. Try lowering the ROI target.")
            else:
                st.error("API Error: No properties returned. Try increasing your Max Price to $500k.")

with col_ctrl:
    st.subheader("🤝 Featured Expert")
    if selected_state == "FL":
        st.info("**Roberta Melo**\nSelecta Realty | REALTOR®")
        st.link_button("Contact Roberta", "https://wa.me/13219007539")
    
    st.divider()
    st.subheader("📊 Instant Calc")
    calc_p = st.number_input("Analysis Price", value=max_price)
    calc_r = st.number_input("Analysis Rent", value=calc_p * 0.008)
    st.metric("Estimated Cash Required", f"${(calc_p * (dp_pct/100)):,.0f}")
