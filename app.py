import streamlit as st
import urllib.request
import json
from datetime import date

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.write("Hallitse ja seuraa useamman kanavan näyttökertoja ja tuloja turvallisesti pilvestä.")

# Haetaan API-avain salaisuuksista
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error("⚠️ API-avainta ei löydy Streamlit Secretsistä! Tarkista asetukset.")
    st.stop()

# Haetaan kanavat Secretsistä (tuetaan [channels] -osiota)
try:
    channels_dict = st.secrets["channels"]
    # Muotoillaan ne siistiin muotoon: {"Pääkanava": "UC...", "Toinen kanava": "UC..."}
    kanavat = {}
    # Koska Secrets antaa avaimet satunnaisessa järjestyksessä, poimitaan ne pareittain
    # Oletetaan muoto: kanava1_nimi, kanava1_id, kanava2_nimi, kanava2_id jne.
    keys = list(channels_dict.keys())
    # Etsitään kaikki parit
    i = 1
    while f"kanava{i}_nimi" in channels_dict and f"kanava{i}_id" in channels_dict:
        nimi = channels_dict[f"kanava{i}_nimi"]
        cid = channels_dict[f"kanava{i}_id"]
        kanavat[nimi] = cid
        i += 1
        
    if not kanavat:
        raise Exception("Ei kanavia löytynyt")
        
except Exception:
    # Varakonfiguraatio, jos vanha tyyli käytössä
    kanavat = {
        "Kanava 1": st.secrets.get("YOUTUBE_CHANNEL_ID", "UCxxxxxxxxxxxxxx"),
        "Uusi Kanava": "UC4GkaGiV3vnTUG_PiOfgu7w"
    }

# --- SIVUPALKKI: Kanavan valinta ja asetukset ---
st.sidebar.header("⚙️ Kanavan valinta")
valittu_kanava_nimi = st.sidebar.selectbox("Valitse tarkasteltava kanava:", list(kanavat.keys()))
valittu_channel_id = kanavat[valittu_kanava_nimi]

st.sidebar.markdown("---")
st.sidebar.header("💵 Tulolaskurin asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Valitse aikajakso arviolle")
aikajakso_tyyppi = st.sidebar.radio(
    "Miten haluat määrittää ajanjakson?",
    ["Päivämääräväli (Kalenteri)", "Syötä arvioidut näyttökerrat ajanjaksolle"]
)

# Haetaan tiedot valitulle kanavalle YouTubesta
try:
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={valittu_channel_id}&key={api_key}"
    
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
        
        st.header(f"Kanava: {channel_name} ({valittu_kanava_nimi})")
        
        # Päämetriikat
        col1, col2, col3 = st.columns(3)
        col1.metric("Kokonaisnäyttökerrat", f"{total_views:,} kpl")
        col2.metric("Tilaajat", f"{total_subs:,} kpl")
        col3.metric("Julkaistut videot", f"{total_videos} kpl")
        
        st.markdown("---")
        
        # --- AIKAJAKSON KÄSITTELY ---
        if aikajakso_tyyppi == "Päivämääräväli (Kalenteri)":
            st.subheader("📆 Valitse kalenterista tarkastelujakso")
            
            col_alku, col_loppu = st.columns(2)
            aloituspaiva = col_alku.date_input("Alkupäivä", date(2026, 1, 1))
            loppupaiva = col_loppu.date_input("Loppupäivä", date.today())
            
            paivia = (loppupaiva - aloituspaiva).days
            if paivia <= 0:
                paivia = 1
                
            st.write(f"Valittu aikajakso: **{paivia} päivää** ({aloituspaiva} – {loppupaiva})")
            
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
        st.error("Kanavaa ei löytynyt annetulla Kanavan ID:llä. Tarkista ID Streamlit Secrets -asetuksista.")
        
except Exception as e:
    st.error(f"Virhe tietojen haussa: {e}")
