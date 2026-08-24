import streamlit as st
import urllib.request
import json
from datetime import date

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro (Vertailu)")
st.write("Molemmat kanavasi rinnakkain: reaaliaikaiset näyttökerrat, tilaajat ja arvioidut tuotot.")

# Haetaan API-avain salaisuuksista
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error("⚠️ API-avainta ei löydy Streamlit Secretsistä! Tarkista asetukset.")
    st.stop()

# Määritellään kanavat Secretsistä tai suoraan koodista varmana
kanavat = {}
try:
    channels_dict = st.secrets["channels"]
    i = 1
    while f"kanava{i}_nimi" in channels_dict and f"kanava{i}_id" in channels_dict:
        nimi = channels_dict[f"kanava{i}_nimi"]
        cid = channels_dict[f"kanava{i}_id"]
        kanavat[nimi] = cid
        i += 1
except Exception:
    pass

# Jos Secretsistä ei löytynyt, käytetään oletuksia
if not kanavat:
    kanavat = {
        "Pääkanava": st.secrets.get("YOUTUBE_CHANNEL_ID", "UCxxxxxxxxxxxxxx"),
        "Toinen kanava": "UC4GkaGiV3vnTUG_PiOfgu7w"
    }

# --- SIVUPALKKI: Yleiset asetukset ---
st.sidebar.header("⚙️ Yleiset asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Tarkastelujakso")
valittu_aikajakso = st.sidebar.radio(
    "Valitse laskentatapa:",
    ["Koko kanavan historia", "Arvio tietylle päivämäärävälille"]
)

if valittu_aikajakso == "Arvio tietylle päivämäärävälille":
    col_alku, col_loppu = st.sidebar.columns(2)
    aloituspaiva = col_alku.date_input("Alkupäivä", date(2026, 1, 1))
    loppupaiva = col_loppu.date_input("Loppupäivä", date.today())
    paivia = (loppupaiva - aloituspaiva).days
    if paivia <= 0:
        paivia = 1
    st.sidebar.write(f"Valittu jakso: **{paivia} päivää**")

st.markdown("---")

# --- NÄYTETÄÄN KANAVAT VIEREKKÄIN ---
# Luodaan sarakkeet kanavien määrän mukaan (esim. 2 kanavaa = 2 saraketta)
sarakkeet = st.columns(len(kanavat))

for idx, (nimi, channel_id) in enumerate(kanavat.items()):
    with sarakkeet[idx]:
        st.subheader(f"📊 {nimi}")
        
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={api_key}"
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if data["items"]:
                channel_info = data["items"][0]
                snippet = channel_info["snippet"]
                stats = channel_info["statistics"]
                
                yt_nimi = snippet["title"]
                total_views = int(stats["viewCount"])
                total_videos = int(stats["videoCount"])
                total_subs = int(stats["subscriberCount"])
                
                st.markdown(f"**Kanavalla:** {yt_nimi}")
                
                # Selkeät metriikkalaatikot vierekkäin
                st.metric("Tilaajat", f"{total_subs:,} kpl")
                st.metric("Julkaistut videot", f"{total_videos} kpl")
                st.metric("Kokonaisnäyttökerrat", f"{total_views:,} kpl")
                
                st.markdown("---")
                
                # Lasketaan tulot
                if valittu_aikajakso == "Koko kanavan historia":
                    usd = (total_views / 1000) * cpm_rate
                    eur = usd * eur_rate
                    st.metric("Tuotot yhteensä (USD)", f"${usd:,.2f} USD")
                    st.metric("Tuotot yhteensä (EUR)", f"~{eur:,.2f} €")
                else:
                    # Jos kyseessä aikajakso, annetaan käyttäjän arvioida tälle kanavalle näyttökerrat tai skaalataan
                    kanava_views = st.number_input(f"Näyttökerrat jaksolla ({nimi}):", min_value=0, value=int(1000 * paivia), step=100, key=f"views_{idx}")
                    usd = (kanava_views / 1000) * cpm_rate
                    eur = usd * eur_rate
                    st.metric(f"Tuotot ({paivia} pv) USD", f"${usd:,.2f} USD")
                    st.metric(f"Tuotot ({paivia} pv) EUR", f"~{eur:,.2f} €")
                    
            else:
                st.error(f"Kanavaa ei löytynyt ID:llä: {channel_id}")
                
        except Exception as e:
            st.error(f"Virhe haussa: {e}")

st.markdown("---")
st.caption(f"💡 Laskelmat perustuvat asettamaasi tuottoon **${cpm_rate} / 1000 näyttökertaa**.")
