import streamlit as st
import urllib.request
import json

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.write("Kanavasi näyttökerrat ja arvioidut tulot automaattisesti pilvestä.")

# Haetaan avain ja kanava-ID Streamlitin Secrets-piilopaikasta
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
    channel_id = st.secrets["YOUTUBE_CHANNEL_ID"]
except Exception:
    st.error("⚠️ Salaisuuksia (Secrets) ei ole määritetty oikein Streamlit Cloudin asetuksiin! Tarkista asetukset.")
    st.stop()

# Sivupalkki (Sidebar) asetuksille
st.sidebar.header("⚙️ Asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Arvio aikajaksolle")
valittu_aikajakso = st.sidebar.selectbox(
    "Valitse ajanjakso arviolle:",
    ["Koko kanavan historia", "Arvio per kuukausi (keskiarvo)", "Arvio per vuosi (keskiarvo)"]
)

# Haetaan tiedot YouTubesta automaattisesti
try:
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet,brandingSettings&id={channel_id}&key={api_key}"
    
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
        
        # Yritetään hakea kanavan luontipäivä, jos tarpeen (tai käytetään oletusta)
        # Jos pubAt ei löydy, näytetään perusmetriikat
        
        # Otsikko kanavan tiedoilla
        st.header(f"Kanava: {channel_name}")
        
        # Peruslaskennat koko historialle
        total_usd = (total_views / 1000) * cpm_rate
        total_eur = total_usd * eur_rate
        
        # Metriikat sarakkeissa
        col1, col2, col3 = st.columns(3)
        col1.metric("Kokonaisnäyttökerrat", f"{total_views:,} kpl")
        col2.metric("Tilaajat", f"{total_subs:,} kpl")
        col3.metric("Julkaistut videot", f"{total_videos} kpl")
        
        st.markdown("---")
        
        if valittu_aikajakso == "Koko kanavan historia":
            st.subheader("💵 Arvioidut kokonaistulot (Koko historia)")
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("Tuotot yhteensä (USD)", f"${total_usd:,.2f} USD")
            res_col2.metric("Tuotot yhteensä (EUR)", f"~{total_eur:,.2f} €")
            
        elif valittu_aikajakso == "Arvio per kuukausi (keskiarvo)":
            st.subheader("📅 Arvioidut tuotot kuukaudessa")
            # Oletetaan karkea arvio tai annetaan käyttäjän säätää, mutta näytetään laskelma
            kk_nayttokerrat = st.slider("Arvioidut kuukausittaiset näyttökerrat:", min_value=1000, max_value=500000, value=10000, step=1000)
            kk_usd = (kk_nayttokerrat / 1000) * cpm_rate
            kk_eur = kk_usd * eur_rate
            
            r1, r2 = st.columns(2)
            r1.metric("Kuukausitulot (USD)", f"${kk_usd:,.2f} USD")
            r2.metric("Kuukausitulot (EUR)", f"~{kk_eur:,.2f} €")
            
        elif valittu_aikajakso == "Arvio per vuosi (keskiarvo)":
            st.subheader("📅 Arvioidut tuotot vuodessa")
            v_nayttokerrat = st.slider("Arvioidut vuotuiset näyttökerrat:", min_value=10000, max_value=5000000, value=120000, step=10000)
            v_usd = (v_nayttokerrat / 1000) * cpm_rate
            v_eur = v_usd * eur_rate
            
            r1, r2 = st.columns(2)
            r1.metric("Vuositulot (USD)", f"${v_usd:,.2f} USD")
            r2.metric("Vuositulot (EUR)", f"~{v_eur:,.2f} €")
        
        st.info(f"💡 Laskelma käyttää arvoa **${cpm_rate} per 1,000 näyttöä** ja valuuttakurssia **{eur_rate} EUR/USD**.")
        
    else:
        st.error("Kanavaa ei löytynyt annetulla Kanavan ID:llä. Tarkista ID Streamlit Secrets -asetuksista.")
        
except Exception as e:
    st.error(f"Virhe tietojen haussa: {e}")
