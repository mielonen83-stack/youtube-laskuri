import streamlit as st
import urllib.request
import json
from datetime import date, timedelta

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

# Moderni tyylittely CSS-muotoiluilla (korteille ja reunuksille)
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.markdown("Seuraa kanaviesi tuottoja ja näyttökertoja valitsemallasi aikajaksolla.")

# Haetaan API-avain salaisuuksista
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error("⚠️ API-avainta ei löydy Streamlit Secretsistä! Tarkista asetukset.")
    st.stop()

# Määritellään kanavat
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

if not kanavat:
    kanavat = {
        "Pääkanava": st.secrets.get("YOUTUBE_CHANNEL_ID", "UCxxxxxxxxxxxxxx"),
        "Toinen kanava": "UC4GkaGiV3vnTUG_PiOfgu7w"
    }

# --- SIVUPALKKI: Asetukset ja Parannettu Kalenteri ---
st.sidebar.header("⚙️ Asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Tarkastelujakso")

# Pikavalinnat kalenterille
aikajakso_valinta = st.sidebar.selectbox(
    "Pikavalinta aikajaksolle:",
    ["Mukautettu (Valitse alta)", "Viimeiset 30 päivää", "Viimeiset 90 päivää", "Vuosi 2026", "Koko historia (Kaikki videot)"]
)

# Määritetään alkupäivä valinnan mukaan
tanaan = date.today()
if aikajakso_valinta == "Viimeiset 30 päivää":
    oletus_alku = tanaan - timedelta(days=30)
elif aikajakso_valinta == "Viimeiset 90 päivää":
    oletus_alku = tanaan - timedelta(days=90)
elif aikajakso_valinta == "Vuosi 2026":
    oletus_alku = date(2026, 1, 1)
elif aikajakso_valinta == "Koko historia (Kaikki videot)":
    oletus_alku = date(2015, 1, 1) # Riittävän kaukaa
else:
    oletus_alku = date(2026, 1, 1)

# Kalenterivalitsin
valittu_alkupaiva = st.sidebar.date_input("Aloituspäivä", oletus_alku)

st.markdown("---")

# --- NÄYTETÄÄN KANAVAT VIEREKKÄIN ---
sarakkeet = st.columns(len(kanavat))

for idx, (nimi, channel_id) in enumerate(kanavat.items()):
    with sarakkeet[idx]:
        st.markdown(f"### 📊 {nimi}")
        
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet,contentDetails&id={channel_id}&key={api_key}"
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if data["items"]:
                channel_info = data["items"][0]
                snippet = channel_info["snippet"]
                stats = channel_info["statistics"]
                content_details = channel_info["contentDetails"]
                
                uploads_playlist_id = content_details["relatedPlaylists"]["uploads"]
                yt_nimi = snippet["title"]
                
                st.caption(f"YouTube-nimi: **{yt_nimi}**")
                st.write(f"Lasketaan videot alkaen: `{valittu_alkupaiva}`")
                
                # Haetaan videoita soittolistasta
                playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&key={api_key}"
                
                with urllib.request.urlopen(playlist_url) as pl_response:
                    pl_data = json.loads(pl_response.read().decode())
                    
                video_list = []
                for item in pl_data.get("items", []):
                    vid = item["snippet"]["resourceId"]["videoId"]
                    vtitle = item["snippet"]["title"]
                    v_published_at = item["snippet"]["publishedAt"][:10]
                    v_date = datetime.strptime(v_published_at, "%Y-%m-%d").date()
                    
                    if v_date >= valittu_alkupaiva:
                        video_list.append({"id": vid, "title": vtitle, "date": v_date})
                
                ajanjakson_nayttokerrat = 0
                
                if video_list:
                    vids_string = ",".join([v["id"] for v in video_list])
                    stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={vids_string}&key={api_key}"
                    
                    with urllib.request.urlopen(stats_url) as st_response:
                        st_data = json.loads(st_response.read().decode())
                        
                    haetut_tiedot = {}
                    for v_item in st_data.get("items", []):
                        v_id = v_item["id"]
                        v_views = int(v_item["statistics"].get("viewCount", 0))
                        haetut_tiedot[v_id] = v_views
                        ajanjakson_nayttokerrat += v_views
                    
                    jakso_usd = (ajanjakson_nayttokerrat / 1000) * cpm_rate
                    jakso_eur = jakso_usd * eur_rate
                    
                    # Siistit tuloslaatikot
                    st.metric("Valitun ajan näyttökerrat", f"{ajanjakson_nayttokerrat:,} kpl")
                    
                    col_u, col_e = st.columns(2)
                    col_u.metric("Tuotot (USD)", f"${jakso_usd:,.2f}")
                    col_e.metric("Tuotot (EUR)", f"~{jakso_eur:,.2f} €")
                    
                    st.markdown("---")
                    st.markdown(f"🎬 **Jaksolta löytyneet videot ({len(video_list)} kpl):**")
                    
                    # Näytetään videot siistissä expanderissa (laajennettavassa laatikossa), jotta sivu pysyy siistinä
                    with st.expander(f"Näytä videot ({nimi})"):
                        for v in video_list:
                            v_views = haetut_tiedot.get(v["id"], 0)
                            v_usd = (v_views / 1000) * cpm_rate
                            title = v["title"]
                            st.markdown(f"**{title}**")
                            st.caption(f"📅 {v['date']} | 👁️ {v_views:,} näyttöä | 💵 ${v_usd:.2f}")
                            st.markdown("---")
                else:
                    st.info(f"Ei videoita valitun päivämäärän jälkeen.")
                    
            else:
                st.error(f"Kanavaa ei löytynyt ID:llä: {channel_id}")
                
        except Exception as e:
            st.error(f"Virhe haussa: {e}")

st.markdown("---")
st.caption(f"💡 Laskelmat perustuvat arvoon **${cpm_rate} / 1000 näyttökertaa** ja valuuttakurssiin **{eur_rate} EUR/USD**.")
