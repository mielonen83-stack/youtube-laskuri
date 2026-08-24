import streamlit as st
import urllib.request
import json
from datetime import date

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.write("Kanavasi näyttökerrat ja arvioidut tulot halutulla aikajaksolla.")

# Haetaan avain ja kanava-ID Streamlitin Secrets-piilopaikasta
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
    channel_id = st.secrets["YOUTUBE_CHANNEL_ID"]
except Exception:
    st.error("⚠️ Salaisuuksia (Secrets) ei ole määritetty oikein Streamlit Cloudin asetuksiin! Tarkista asetukset.")
    st.stop()

# --- SIVUPALKKI: Asetukset ja Ajajakso ---
st.sidebar.header("⚙️ Asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Valitse aikajakso arviolle")

# Vaihtoehdot aikajaksolle
aikajakso_tyyppi = st.sidebar.radio(
    "Miten haluat määrittää ajanjakson?",
    ["Päivämääräväli (Kalenteri)", "Syötä arvioidut näyttökerrat ajanjaksolle"]
)

# Haetaan tiedot YouTubesta kanavan kokonaistilastoja varten
try:
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
        
        st.header(f"Kanava: {channel_name}")
        
        # Päämetriikat
        col1, col2, col3 = st.columns(3)
        col1.metric("Kokonaisnäyttökerrat", f"{total_views:,} kpl")
        col2.metric("Tilaajat", f"{total_subs:,} kpl")
        col3.metric("Julkaistut videot", f"{total_videos} kpl")
        
        st.markdown("---")
        
        # --- AIKAJAKSON KÄSITTELY ---
        if aikajakso_tyyppi == "Päivämääräväli (Kalenteri)":
            st.subheader("📆 Valitse kalenterista tarkastelujakso")
            
            # Kalenterivalitsimet
            col_alku, col_loppu = st.columns(2)
            aloituspaiva = col_alku.date_input("Alkupäivä", date(2026, 1, 1))
            loppupaiva = col_loppu.date_input("Loppupäivä", date.today())
            
            # Lasketaan päivien määrä
            paivia = (loppupaiva - aloituspaiva).days
            if paivia <= 0:
                paivia = 1  # Estetään nollalla jako
                
            st.write(f"Valittu aikajakso: **{paivia} päivää** ({aloituspaiva} – {loppupaiva})")
            
            # Koska YouTube API ei ilman OAuthia anna päiväkohtaista dataa kanavalle, 
            # annetaan käyttäjän arvioida keskimääräinen päivätahti tai syöttää luvut tälle jaksolle:
            st.info("💡 **Vinkki:** Voit säätää alta, kuinka monta näyttökertaa sait keskimäärin päivässä tai yhteensä tällä aikajaksolla.")
            
            jakso_nayttokerrat = st.number_input("Näyttökerrat valitulla aikajaksolla:", min_value=0, value=int(1000 * paivia), step=100)
            
            j_usd = (jakso_nayttokerrat / 1000) * cpm_rate
            j_eur = j_usd * eur_rate
            
            st.subheader(f"💵 Tulot valitulla aikajaksolla ({paivia} pv)")
            r1, r2 = st.columns(2)
            r1.metric("Tuotot (USD)", f"${j_usd:,.2f} USD")
            r2.metric("Tuotot (EUR)", f"~{j_eur:,.2f} €")
            
        else:
            st.subheader("📈 Mukautettu näyttökertamäärä")
            mukautettu_nayttokerrat = st.number_input("Syötä näyttökerrat haluamaltasi jaksolta:", min_value=0, value=50000, step=1000)
            
            m_usd = (mukautettu_nayttokerrat / 1000) * cpm_rate
            m_eur = m_usd * eur_rate
            
            r1, r2 = st.columns(2)
            r1.metric("Tuotot (USD)", f"${m_usd:,.2f} USD")
            r2.metric("Tuotot (EUR)", f"~{m_eur:,.2f} €")
            
    else:
        st.error("Kanavaa ei löytynyt. Tarkista Kanavan ID Streamlit Secrets -asetuksista.")
        
except Exception as e:
    st.error(f"Virhe tietojen haussa: {e}")
