import streamlit as st

st.title("YouTube Tulolaskuri 💰")
st.write("Laske arvioidut YouTube-tulosi helposti (1$ per 1000 näyttökertaa).")

# Liukusäädin näyttökertojen valintaan
views = st.slider("Valitse näyttökertojen määrä:", min_value=0, max_value=1000000, value=10000, step=1000)

# Laskenta
dollars_per_1000 = 1.0
estimated_usd = (views / 1000) * dollars_per_1000

# Tulokset hienosti esille
st.markdown("---")
st.subheader("Tulokset:")
st.metric(label="Arvioidut tulot", value=f"${estimated_usd:.2f} USD")
