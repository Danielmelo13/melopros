import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- CONFIG & SECURITY ---
# This looks for the key in your Streamlit Cloud "Advanced Settings > Secrets"
if "RENTCAST_API_KEY" in st.secrets:
    API_KEY = st.secrets["RENTCAST_API_KEY"]
else:
    # Fallback for local testing
    API_KEY = "MxqmSWaOPvVaAXPEt42aXrhvP4McBq"

st.set_page_config(layout="wide", page_title="Melopros | Investor Command Center")

# --- DATA ENGINE ---
def fetch_properties(state_code, min_p, max_p):
    """Calls RentCast for active listings in a specific state."""
    url = f"https://api.rentcast.io/v1/listings/sale?state={state_code}&minPrice={min_p}&maxPrice={max_p}&limit=25&status=Active"
    headers = {"X-Api-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- CUSTOM LANDLORD-FRIENDLY STATES ---
LANDLORD_STATES = {
    "FL": "No State Income Tax | 3-Day Notice",
    "MO": "High Rent-to-Price Ratio | Landlord Friendly",
    "TX": "No State Income Tax | Fast Evictions",
    "AZ": "5-Day Non-compliance | Strong Growth",
    "OH": "Low Entry Cost | 3-Day Notice",
    "IN": "45-Day Deposit Hold | Stable Market",
    "KY": "Minimal Bureaucracy",
    "NC": "High Migration | 0.77% Prop Tax",
    "CO": "72-Hour Notice Period",
    "AL": "Lowest Prop Tax (0.38%)",
    "GA": "7-Day Notice | Informal Evictions"
}

# --- SIDEBAR: SCOUTING FILTERS ---
st.sidebar.title("🛡️ Melopros Guard")
selected_state = st.sidebar.selectbox("Target State", list(LANDLORD_STATES.keys()))
st.sidebar.success(f"Market Intel: {LANDLORD_STATES[selected_state]}")

st.sidebar.divider()
st.sidebar.subheader("💰 Investment Budget")
min_price = st.sidebar.number_input("Min Price ($)", value=10000, step=10000)
max_price = st.sidebar.number_input("Max Price ($)", value=1000000, step=50000)

st.sidebar.divider()
st.sidebar.subheader("🏦 Financing Strategy")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0, step=0.1)
closing_pct = st.sidebar.slider("Closing Costs (%)", 1, 10, 3)

st.sidebar.divider()
search_button = st.sidebar.button("🔍 Run Melopros Analysis", use_container_width=True)

# --- MAIN UI LAYOUT ---
col_map, col_ctrl = st.columns([2, 1])

with col_map:
    st.title(f"Market Scan: {selected_state}")
    
    # Logic when button is clicked
    if search_button:
        with st.spinner(f"Scouting {selected_state}..."):
            listings = fetch_properties(selected_state, min_price, max_price)
            
            if listings:
                df = pd.DataFrame(listings)
                df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                st.success(f"Found {len(listings)} active opportunities!")
                
                # Center map on results
                view_state = pdk.ViewState(
                    latitude=df['lat'].mean(), 
                    longitude=df['lon'].mean(), 
                    zoom=6, 
                    pitch=30
                )
                
                # Interactive Map
                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/light-v9',
                    initial_view_state=view_state,
                    tooltip={"text": "{address}\nPrice: ${price}\nBed/Bath: {bedrooms}/{bathrooms}"},
                    layers=[pdk.Layer(
                        'ScatterplotLayer',
                        data=df,
                        get_position='[lon, lat]',
                        get_color='[46, 204, 113, 200]',
                        get_radius=3000,
                        pickable=True,
                        auto_highlight=True
                    )]
                ))
                st.dataframe(df[['address', 'price', 'bedrooms', 'bathrooms']], use_container_width=True)
            else:
                st.warning("No listings found in this range. Try increasing your Max Price.")
    else:
        st.info("Set your budget and click 'Run Melopros Analysis' to see live deals.")
        # Default empty map
        st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=38, longitude=-95, zoom=3)))

with col_ctrl:
    st.subheader("🤝 Featured Expert")
    if selected_state == "FL":
        st.image("https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png", width=100)
        st.markdown("### **Roberta Melo**")
        st.caption("Selecta Realty | Central Florida Specialist")
        st.write("Expert in Winter Garden, Lake Nona, and Horizon West investment acquisitions.")
        st.button("Contact Roberta")
    else:
        st.write("Looking for a pro in this area?")
        st.button("Join the Melopros Network")
    
    st.divider()
    st.subheader("📊 Deal Analyzer")
    # Interactive ROI Calculator based on user input or selected property
    ana_price = st.number_input("Property Value ($)", value=max_price//2 if search_button else 150000)
    ana_rent = st.number_input("Est. Monthly Rent ($)", value=1500)
    
    # Calculations
    total_cash = (ana_price * (dp_pct/100)) + (ana_price * (closing_pct/100))
    monthly_mortgage = (ana_price * (1-(dp_pct/100))) * ((interest_rate/100)/12) # Simplified for MVP
    monthly_cf = ana_rent - monthly_mortgage - (ana_price * 0.012 / 12) # Price * 1.2% tax / 12
    roi = (monthly_cf * 12 / total_cash) * 100
    
    st.metric("Total Cash Needed", f"${total_cash:,.0f}")
    st.metric("Monthly Cashflow", f"${monthly_cf:,.2f}")
    st.subheader(f"Annualized ROI: :green[{roi:.2f}%]")
