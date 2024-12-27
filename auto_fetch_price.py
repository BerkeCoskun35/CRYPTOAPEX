import streamlit as st
import time
from api import update_crypto_prices, update_currency_prices
from database import get_db_connection

# Initialize database
db = get_db_connection()

# Set the auto-refresh interval (in seconds)
AUTO_REFRESH_INTERVAL = 300  # 5 minutes

# Streamlit app layout
st.title("CryptoApex: Cryptocurrency and Currency Tracker")

# Tabs for navigation
tab1, tab2 = st.tabs(["Cryptocurrency Prices", "Currency Prices"])

# Cryptocurrency Prices
with tab1:
    st.header("Cryptocurrency Prices")
    if st.button("Update Crypto Prices Now", key="update_crypto"):
        update_crypto_prices()
        st.success("Cryptocurrency prices updated!")

    crypto_data = list(db['Kripto Para'].find({}, {"_id": 0, "kripto_adi": 1, "guncel_fiyat": 1}))
    st.table(crypto_data)

# Currency Prices
with tab2:
    st.header("Currency Prices")
    if st.button("Update Currency Prices Now", key="update_currency"):
        update_currency_prices()
        st.success("Currency prices updated!")

    currency_data = list(db['Döviz'].find({}, {"_id": 0, "döviz_adi": 1, "guncel_fiyat": 1}))
    st.table(currency_data)

# Sidebar auto-refresh toggle
if st.sidebar.checkbox("Enable Auto-Refresh (5 min)", key="auto_refresh"):
    time.sleep(AUTO_REFRESH_INTERVAL)
    st.rerun()  # Automatically rerun the app
