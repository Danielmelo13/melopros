import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- 1. CONFIG & SECURITY ---
# Accesses your RentCast Key from Streamlit Secrets
if "RENTCAST_API_KEY" in st.secrets:
    API_KEY = st.secrets["RENTCAST_API_KEY"]
else:
    # Manual fallback for local development
    API_KEY = "MxqmSWaOPvVaAXPEt42aXrhvP4McBq"

st.set_page_config(layout="wide", page_title="Melopros | ROI Scout")

# --- 2. DATA ENGINE ---
def fetch_properties(state_code, min_p, max_p):
    """Fetches active listings for the selected state and budget."""
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
    "AZ": "5-Day Non-compliance | Strong Growth",
    "OH": "Low Entry Point | High Yield",
    "IN": "45-Day Deposit Hold | Stable Market",
    "KY": "Minimal Bureaucracy",
    "NC": "High Migration | Strong Rental Demand",
    "AL": "Lowest Property Tax (0.38%)",
    "GA": "7-Day Notice | Fast Possession"
}

# --- 4. SIDEBAR FILTERS ---
st.sidebar.title("🛡️ Melopros Guard")
selected_state = st.sidebar.selectbox("Target Market", list(LANDLORD_STATES.keys()))
st.sidebar.info(f"Market Intel: {LANDLORD_STATES[selected_state]}")

st.sidebar.divider()
st.sidebar.subheader("💰 Budget & ROI Target")
min_price = st.sidebar.number_input("Min Price ($)", value=50000, step=10000)
max_price = st.sidebar.number_input("Max Price ($)", value=350000, step=25000)
roi_target = st.sidebar.slider("ROI Target: More than (%)", 1.0, 20.0, 5.0)

st.sidebar.divider()
st.sidebar.subheader("🏦 Financing Strategy")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0, step=0.1)

st.sidebar.divider()
search_button = st.sidebar.button("🔍 Scout Market", use_container_width=True)

# --- 5. MAIN UI LAYOUT ---
col_map, col_ctrl = st.columns([2.5, 1])

with col_map:
    st.title(f"Scouting {selected_state} for >{roi_target}% ROI")
    
    if search_button:
        with st.spinner(f"Analyzing {selected_state} market..."):
            data = fetch_properties(selected_state, min_price, max_price)
            
            if data:
                df = pd.DataFrame(data)
                
                # --- ROI CALCULATION (REAL-WORLD MODEL) ---
                # Monthly Rent (Est 0.8%) - OpExp (35%) - Mortgage
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
                    # Rename columns for pydeck mapping
                    df_filtered = df_filtered.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                    
                    st.success(f"Found {len(df_filtered)} properties meeting your target (Scanned {raw_count}).")
                    
                    # RENDER MAP
                    st.pydeck_chart(pdk.Deck(
                        map_style='mapbox://styles/mapbox/dark-v9',
                        initial_view_state=pdk.ViewState(
                            latitude=df_filtered['lat'].mean(), 
                            longitude=df_filtered['lon'].mean(), 
                            zoom=6, 
                            pitch=45
                        ),
                        tooltip={"text": "{address}\nPrice: ${price:,.0f}\nROI: {roi:.2f}%"},
                        layers=[pdk.Layer(
                            'ScatterplotLayer',
                            data=df_filtered,
                            get_position='[lon, lat]',
                            get_color='[0, 255, 120, 200]',
                            # Radius grows with ROI to highlight the best deals
                            get_radius='roi * 500', 
                            pickable=True,
                            auto_highlight=True
                        )]
                    ))
                    
                    # Display Raw Data Table
                    st.dataframe(
                        df_filtered[['address', 'price', 'roi', 'bedrooms', 'bathrooms']], 
                        use_container_width=True
                    )
                else:
                    st.warning(f"Found {raw_count} properties, but none met your {roi_target}% ROI target.")
            else:
                st.error("No data returned. Check your API Key or try a higher Max Price.")
    else:
        st.info("Adjust your filters and click 'Scout Market' to find active deals.")

with col_ctrl:
    st.subheader("🤝 Featured Expert")
    if selected_state == "FL":
        st.info("**Roberta Melo**\nSelecta Realty | REALTOR®")
        st.write("Ready to close in Central FL? Contact the investment specialist.")
        st.link_button("Contact Roberta", "https://wa.me/13219007539")
    else:
        st.write("Looking for a professional in this area?")
        st.button("Join the Melopros Network")
    
    st.divider()
    st.subheader("📊 Calculator Refresh")
    # Quick calc for the right sidebar
    calc_val = st.number_input("Analysis Price ($)", value=max_price)
    calc_rent = st.number_input("Analysis Rent ($)", value=calc_val * 0.008)
    
    cash_in = (calc_val * (dp_pct/100))
    st.metric("Cash Required", f"${cash_in:,.0f}")
