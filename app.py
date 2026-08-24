import streamlit as st
import urllib.request
import json
from datetime import datetime, timedelta

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.write("Seuraa kanavasi näyttökertoja ja arvioituja tuloja kattavasti.")

# Sivupalkki (Sidebar) asetuksille
st.sidebar.header("⚙️ Asetukset")

# Tässä voit laittaa oman API-avaimesi valmiiksi, tai käyttää kenttää
# Vinkki: Turvallisemmin saat sen Streamlit Secretsistä, mutta laitetaan tähän helppo kenttä
default_key = "" 
api_key = st.sidebar.text_input("YouTube API -avain", value=default_key, type="password")

channel_id = st.sidebar.text_input("YouTube Kanavan ID (Channel ID)", value="", placeholder="Esim. UCxxxxxxxxxxxxxx")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Tulolaskurin asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

# Pääsisältö
if not api_key or not channel_id:
    st.info("👈 Syötä sivupalkkiin YouTube API-avain ja Kanavan ID nähdäksesi tiedot.")
    
    # Näytetään esimerkkilaskuri, jos tietoja ei ole vielä syötetty
    st.markdown("### Pikakokeilu (manuaalinen laskuri)")
    demo_views = st.number_input("Testaa näyttökertamäärällä:", min_value=0, value=50000, step=1000)
    demo_usd = (demo_views / 1000) * cpm_rate
    demo_eur = demo_usd * eur_rate
    
    col1, col2 = st.columns(2)
    col1.metric("Arvioidut tuotot (USD)", f"${demo_usd:.2f}")
    col2.metric("Arvioidut tuotot (EUR)", f"~{demo_eur:.2f} €")

else:
    try:
        # Haetaan kanavan tiedot API:n kautta
        url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={api_key}"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        if data["items"]:
            channel_info = data["items"][0]
            snippet = channel_info["snippet"]
            stats = channel_info["statistics"]
            
            channel_name = snippet["title"]
            total_views = int(stats["viewCount"])
            total_videos = int(stats["videoCount"])
            total_subs = int(stats["subscriberCount"])
            
            # Otsikko kanavan tiedoilla
            st.header(f"Kanava: {channel_name}")
            
            # Laskennat
            total_usd = (total_views / 1000) * cpm_rate
            total_eur = total_usd * eur_rate
            
            # Métriikat kolmessa sarakkeessa
            col1, col2, col3 = st.columns(3)
            col1.metric("Kokonaisnäyttökerrat", f"{total_views:,} kpl")
            col2.metric("Tilaajat", f"{total_subs:,} kpl")
            col3.metric("Julkaistut videota", f"{total_videos} kpl")
            
            st.markdown("---")
            st.subheader("💵 Arvioidut kokonaistulot")
            
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("Tuotot yhteensä (USD)", f"${total_usd:,.2f} USD")
            res_col2.metric("Tuotot yhteensä (EUR)", f"~{total_eur:,.2f} €")
            
            # Lisäosio: Arvio aikajaksolle (esim. kuukausikeskiarvo jos oletetaan kanavan elinkaari)
            st.info(f"💡 Huomio: Tämä laskelma käyttää arvoa **${cpm_rate} per 1,000 näyttöä** perustuen kanavasi koko historian näyttökertoihin.")
            
        else:
            st.error("Kanavaa ei löytynyt annetulla Kanavan ID:llä. Tarkista ID.")
            
    except Exception as e:
        st.error(f"Virhe tietojen haussa: {e}")
