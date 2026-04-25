import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

def fetch_properties(state_code, min_p, max_p):
    # We switched zipCode={zip_code} to state={state_code}
    url = f"https://api.rentcast.io/v1/listings/sale?state={state_code}&minPrice={min_p}&maxPrice={max_p}&limit=25&status=Active"
    headers = {"X-Api-Key": API_KEY}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

# --- CONFIG & SECRETS ---
# Once deployed, you will move the key to Streamlit's Secret Manager
API_KEY = "MxqmSWaOPvVaAXPEt42aXrhvP4McBq" 

st.set_page_config(layout="wide", page_title="Melopros | Investor Command Center")

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
selected_state = st.sidebar.selectbox("Select Target State", list(LANDLORD_STATES.keys()))
st.sidebar.success(f"Context: {LANDLORD_STATES[selected_state]}")

# --- BUDGET FILTERS ---
st.sidebar.divider()
st.sidebar.subheader("💰 Investment Budget")
min_price = st.sidebar.number_input("Min Price ($)", value=10000, step=10000)
max_price = st.sidebar.number_input("Max Price ($)", value=1000000, step=50000)

# --- SEARCH TRIGGER ---
st.sidebar.divider()
# target_zip is gone! We only need the button now.
search_button = st.sidebar.button("🔍 Run Melopros Analysis")

if search_button:
    with st.spinner(f"Scouting the best deals in {selected_state}..."):
        # We now pass 'selected_state' into the function
        listings = fetch_properties(selected_state, min_price, max_price)
        
        if listings:
            df = pd.DataFrame(listings)
            # FIX: Rename columns so the map understands them
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
            
            st.success(f"Found {len(listings)} active opportunities in {selected_state}!")
            
            # FIX: This centers the map on the NEW search location
            view_state = pdk.ViewState(
                latitude=df['lat'].iloc[0], 
                longitude=df['lon'].iloc[0], 
                zoom=12, 
                pitch=45
            )
            
            # Display the map with real pins
            st.pydeck_chart(pdk.Deck(
                initial_view_state=view_state,
                layers=[pdk.Layer(
                    'ScatterplotLayer', 
                    data=df, 
                    get_position='[lon, lat]', 
                    get_color='[200, 30, 0, 160]', 
                    get_radius=200,
                    pickable=True
                )]
            ))
        else:
            st.warning(f"No properties found in {target_zip} within your budget.")

st.sidebar.divider()
st.sidebar.subheader("💰 Financing & Strategy")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0, step=0.1)
closing_pct = st.sidebar.slider("Closing Costs (%)", 1, 10, 3)

# --- SEARCH TRIGGER ---
st.sidebar.divider()
target_zip = st.sidebar.text_input("Enter ZIP Code to Scout", value="34787")
search_button = st.sidebar.button("🔍 Run Melopros Analysis")

# --- MAIN UI LAYOUT ---
col_map, col_ctrl = st.columns([2, 1])

with col_map:
    st.title(f"Scouting Opportunities: {selected_state}")
    # Placeholder for Map - In next refinement, we connect RentCast live here
    st.info("Map View: Pins will appear based on live ROI calculations.")
    
    # Static Example Map
    view_state = pdk.ViewState(latitude=28.5383, longitude=-81.3792, zoom=10, pitch=45)
    st.pydeck_chart(pdk.Deck(initial_view_state=view_state))

with col_ctrl:
    st.subheader("🤝 Featured Pro")
    if selected_state == "FL":
        st.info("⭐ **Roberta Melo**\n\nSelecta Realty | Winter Garden Specialist")
        st.write("Expert in Horizon West & Lake Nona acquisitions.")
        st.markdown("[Contact Roberta](https://wa.me/13219007539)")
    
    st.divider()
    st.subheader("📊 Deal Analyzer")
    # This reflects the Control Panel layout you liked
    price = st.number_input("Property Price ($)", value=350000)
    est_rent = st.number_input("Est. Monthly Rent ($)", value=2800)
    
    # Basic ROI Math for the MVP
    down_payment = price * (dp_pct / 100)
    closing_costs = price * (closing_pct / 100)
    total_cash = down_payment + closing_costs
    
    annual_cf = (est_rent * 12) - (price * 0.012) # Est 1.2% tax for now
    roi = (annual_cf / total_cash) * 100
    
    st.metric("Total Cash Needed", f"${total_cash:,.0f}")
    st.metric("Estimated ROI", f"{roi:.2f}%")
