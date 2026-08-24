import streamlit as st
import urllib.request
import json
from datetime import date, datetime

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.write("Seuraa kanavien tuloja tietystä aloituspäivästä alkaen eteenpäin.")

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

# --- SIVUPALKKI: Asetukset ja Ajanjakso ---
st.sidebar.header("⚙️ Asetukset")
cpm_rate = st.sidebar.slider("Tuotto / 1000 näyttökertaa ($ USD)", min_value=0.5, max_value=10.0, value=1.0, step=0.1)
eur_rate = st.sidebar.number_input("EUR / USD valuuttakurssi", value=0.92, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Aloituspäivä")
st.sidebar.write("Valitse päivä, josta alkaen julkaistuja videoita lasketaan:")
valittu_alkupaiva = st.sidebar.date_input("Aloituspäivä", date(2026, 1, 1))

st.markdown("---")

# --- NÄYTETÄÄN KANAVAT VIEREKKÄIN ---
sarakkeet = st.columns(len(kanavat))

for idx, (nimi, channel_id) in enumerate(kanavat.items()):
    with sarakkeet[idx]:
        st.subheader(f"📊 {nimi}")
        
        try:
            # 1. Haetaan kanavan tiedot ja uploads-soittolista
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
                
                st.markdown(f"**Kanava:** {yt_nimi}")
                st.caption(f"Lasketaan videot alkaen: **{valittu_alkupaiva}**")
                
                # 2. Haetaan soittolistasta videoita (haetaan kerralla useampi, esim. 50 tuoreinta, jotta osuu halutulle ajanjaksolle)
                playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&key={api_key}"
                
                with urllib.request.urlopen(playlist_url) as pl_response:
                    pl_data = json.loads(pl_response.read().decode())
                    
                video_list = []
                for item in pl_data.get("items", []):
                    vid = item["snippet"]["resourceId"]["videoId"]
                    vtitle = item["snippet"]["title"]
                    # Julkaisupäivä muodossa "2026-03-01T..."
                    v_published_at = item["snippet"]["publishedAt"][:10]
                    v_date = datetime.strptime(v_published_at, "%Y-%m-%d").date()
                    
                    # Tarkistetaan, että video on julkaistu valittuna päivänä tai sen jälkeen
                    if v_date >= valittu_alkupaiva:
                        video_list.append({"id": vid, "title": vtitle, "date": v_date})
                
                # 3. Jos videoita löytyi valitulta aikajaksolta, haetaan niiden näyttökerrat
                ajanjakson_nayttokerrat = 0
                
                if video_list:
                    vids_string = ",".join([v["id"] for v in video_list])
                    stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={vids_string}&key={api_key}"
                    
                    with urllib.request.urlopen(stats_url) as st_response:
                        st_data = json.loads(st_response.read().decode())
                        
                    # Tallennetaan videokohtaiset tiedot listaukseen
                    haetut_tiedot = {}
                    for v_item in st_data.get("items", []):
                        v_id = v_item["id"]
                        v_views = int(v_item["statistics"].get("viewCount", 0))
                        haetut_tiedot[v_id] = v_views
                        ajanjakson_nayttokerrat += v_views
                    
                    # Lasketaan tuotot tälle ajanjaksolle
                    jakso_usd = (ajanjakson_nayttokerrat / 1000) * cpm_rate
                    jakso_eur = jakso_usd * eur_rate
                    
                    # Näytetään tulokset
                    st.metric("Ajanjakson näyttökerrat", f"{ajanjakson_nayttokerrat:,} kpl")
                    st.metric("Tuotot yhteensä (USD)", f"${jakso_usd:,.2f} USD")
                    st.metric("Tuotot yhteensä (EUR)", f"~{jakso_eur:,.2f} €")
                    
                    st.markdown("---")
                    st.markdown(f"🎬 **Löytyneet videot ({len(video_list)} kpl):**")
                    
                    for v in video_list:
                        v_views = haetut_tiedot.get(v["id"], 0)
                        v_usd = (v_views / 1000) * cpm_rate
                        title = v["title"]
                        if len(title) > 35:
                            title = title[:32] + "..."
                        
                        st.text(f"• {title} ({v['date']})")
                        st.caption(f"  👁️ {v_views:,} näyttöä | 💵 ${v_usd:.2f}")
                else:
                    st.info(f"Ei videoita valitun päivämäärän ({valittu_alkupaiva}) jälkeen.")
                    
            else:
                st.error(f"Kanavaa ei löytynyt ID:llä: {channel_id}")
                
        except Exception as e:
            st.error(f"Virhe haussa: {e}")

st.markdown("---")
st.caption(f"💡 Laskelmat perustuvat arvoon **${cpm_rate} / 1000 näyttökertaa**.")
