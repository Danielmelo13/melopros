import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

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

st.sidebar.divider()
st.sidebar.subheader("💰 Financing & Strategy")
dp_pct = st.sidebar.slider("Down Payment (%)", 5, 100, 20)
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=7.0, step=0.1)
closing_pct = st.sidebar.slider("Closing Costs (%)", 1, 10, 3)

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
