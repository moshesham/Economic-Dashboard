"""
API Key Management Page
Configure and manage API keys for various data sources.
"""

import streamlit as st
from modules.auth.credentials_manager import get_credentials_manager

# Page configuration
st.set_page_config(
    page_title="API Key Management",
    page_icon="🔑",
    layout="wide"
)

st.title("🔑 API Key Management")
st.markdown("### Securely manage your API keys and credentials")

# Initialize credentials manager
creds_manager = get_credentials_manager()

# Display current status
st.divider()
st.subheader("📋 Configured API Keys")

configured_services = creds_manager.list_services()

if configured_services:
    cols = st.columns(3)
    
    for idx, service in enumerate(configured_services):
        with cols[idx % 3]:
            st.success(f"✅ **{service.upper()}**")
            st.caption(f"API key configured")
            
            if st.button(f"Remove", key=f"remove_{service}"):
                if creds_manager.delete_api_key(service):
                    st.success(f"Removed {service} API key")
                    st.rerun()
else:
    st.info("ℹ️ No API keys configured yet. Add one below.")

# Add/Update API Keys
st.divider()
st.subheader("➕ Add or Update API Key")

col1, col2 = st.columns([1, 2])

with col1:
    service_options = [
        "FRED (Federal Reserve)",
        "Yahoo Finance",
        "World Bank",
        "Alpha Vantage",
        "Quandl",
        "Custom API"
    ]
    selected_service = st.selectbox("Select Service", service_options)
    
    # Map display name to internal key
    service_map = {
        "FRED (Federal Reserve)": "fred",
        "Yahoo Finance": "yahoo_finance",
        "World Bank": "world_bank",
        "Alpha Vantage": "alpha_vantage",
        "Quandl": "quandl",
        "Custom API": "custom"
    }
    
    service_key = service_map[selected_service]

with col2:
    api_key_input = st.text_input(
        "API Key",
        type="password",
        help="Your API key will be encrypted and stored securely"
    )
    
    col_a, col_b = st.columns([1, 3])
    
    with col_a:
        if st.button("💾 Save API Key", use_container_width=True):
            if api_key_input:
                creds_manager.set_api_key(service_key, api_key_input)
                st.success(f"✅ {selected_service} API key saved securely!")
                st.rerun()
            else:
                st.error("Please enter an API key")

# Information section
st.divider()
st.subheader("ℹ️ How to Get API Keys")

with st.expander("🏦 FRED (Federal Reserve Economic Data)"):
    st.markdown("""
    **Steps to get a FRED API key:**
    1. Visit [FRED API Registration](https://fredaccount.stlouisfed.org/apikeys)
    2. Create a free account or log in
    3. Request an API key
    4. Copy the API key and paste it above
    
    **Benefits:**
    - Higher rate limits
    - Access to all FRED economic data series
    - No usage fees for most data
    """)

with st.expander("📈 Alpha Vantage"):
    st.markdown("""
    **Steps to get an Alpha Vantage API key:**
    1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
    2. Enter your email address
    3. Receive API key via email
    4. Paste it above
    
    **Features:**
    - Real-time and historical stock data
    - Technical indicators
    - Free tier available (500 requests/day)
    """)

with st.expander("📊 Quandl"):
    st.markdown("""
    **Steps to get a Quandl API key:**
    1. Visit [Quandl](https://www.quandl.com/)
    2. Create a free account
    3. Go to Account Settings → API Key
    4. Copy and paste above
    
    **Features:**
    - Financial, economic, and alternative data
    - Free and premium datasets
    - 50 calls/day on free tier
    """)

# Security information
st.divider()
st.subheader("🔒 Security & Privacy")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🔐 Encryption**
    
    All API keys are encrypted using Fernet (symmetric encryption) before storage.
    """)

with col2:
    st.markdown("""
    **📁 Storage Location**
    
    Encrypted credentials are stored in:
    `data/credentials/credentials.enc`
    """)

with col3:
    st.markdown("""
    **🛡️ Best Practices**
    
    - Never share your API keys
    - Rotate keys periodically
    - Delete unused keys
    """)

# Current FRED API Key Status
st.divider()
st.subheader("📊 FRED API Status")

if creds_manager.has_api_key('fred'):
    st.success("✅ FRED API key is configured and active")
    st.info("Your dashboard is now using authenticated FRED API access for higher rate limits and reliability.")
else:
    st.warning("⚠️ FRED API key not configured")
    st.info("The dashboard will use unauthenticated access (limited rate limits)")
    
    if st.button("🚀 Quick Setup FRED Key"):
        st.info("""
        To set up your FRED API key:
        1. Get your key from [FRED API Keys](https://fredaccount.stlouisfed.org/apikeys)
        2. Use the form above to add it
        3. Or run: `python setup_credentials.py`
        """)

# Sidebar information
with st.sidebar:
    st.header("About API Keys")
    st.markdown("""
    This page allows you to securely manage API keys for various data sources.
    
    **Why use API keys?**
    - Higher rate limits
    - More reliable access
    - Access to premium data
    - Better performance
    
    **Security:**
    All keys are encrypted using industry-standard encryption before storage.
    """)
    
    st.divider()
    st.caption("Credentials Manager v1.0")
