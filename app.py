import streamlit as st
import urllib.request
import json
from datetime import date, datetime, timedelta

# Sivuston ulkoasu
st.set_page_config(page_title="YouTube Tulolaskuri Pro", page_icon="💰", layout="wide")

st.title("💰 YouTube Tulolaskuri & Analytiikka Pro")
st.markdown("Seuraa kanaviesi tuottoja ja näyttökertoja valitsemallasi aikajaksolla.")

# Haetaan API-avain salaisuuksista
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except Exception:
    st.error("⚠️ API-avainta ei löydy Streamlit Secretsistä! Tarkista asetukset.")
    st.stop()

# Määritellään kanavat turvallisesti
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
st.sidebar.subheader("📅 Tarkastelujakso")

aikajakso_valinta = st.sidebar.selectbox(
    "Valitse ajanjakso:",
    [
        "Viimeiset 30 päivää", 
        "Viimeiset 90 päivää", 
        "Tämän vuoden alusta", 
        "Koko historia (Kaikki videot)",
        "Valitse vapaa kalenteriväli (Alku- ja loppupäivä)"
    ]
)

tanaan = date.today()

if aikajakso_valinta == "Viimeiset 30 päivää":
    valittu_alkupaiva = tanaan - timedelta(days=30)
    valittu_loppupaiva = tanaan
elif aikajakso_valinta == "Viimeiset 90 päivää":
    valittu_alkupaiva = tanaan - timedelta(days=90)
    valittu_loppupaiva = tanaan
elif aikajakso_valinta == "Tämän vuoden alusta":
    valittu_alkupaiva = date(tanaan.year, 1, 1)
    valittu_loppupaiva = tanaan
elif aikajakso_valinta == "Koko historia (Kaikki videot)":
    valittu_alkupaiva = date(2010, 1, 1)
    valittu_loppupaiva = tanaan
else:
    col_a, col_l = st.sidebar.columns(2)
    with col_a:
        valittu_alkupaiva = st.date_input("Alkupäivä", tanaan - timedelta(days=30))
    with col_l:
        valittu_loppupaiva = st.date_input("Loppupäivä", tanaan)

st.sidebar.info(f"Ajanjakso: **{valittu_alkupaiva}** – **{valittu_loppupaiva}**")

st.markdown("---")

# --- NÄYTETÄÄN KANAVAT VIEREKKÄIN ---
sarakkeet = st.columns(len(kanavat))

for idx, (nimi, channel_id) in enumerate(kanavat.items()):
    with sarakkeet[idx]:
        st.markdown(f"### 📊 {nimi}")
        
        if not channel_id or channel_id == "UCxxxxxxxxxxxxxx":
            st.warning("Kanavan ID puuttuu tai on oletusarvona asetuksista.")
            continue
            
        try:
            # 1. Haetaan kanavan tiedot
            url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet,contentDetails&id={channel_id}&key={api_key}"
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if not data.get("items"):
                st.error(f"Kanavaa ei löytynyt ID:llä: {channel_id}")
                continue
                
            channel_info = data["items"][0]
            snippet = channel_info["snippet"]
            content_details = channel_info["contentDetails"]
            
            uploads_playlist_id = content_details["relatedPlaylists"]["uploads"]
            yt_nimi = snippet["title"]
            
            st.caption(f"YouTube-nimi: **{yt_nimi}**")
            
            # 2. Haetaan soittolistan videot
            playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&key={api_key}"
            
            try:
                with urllib.request.urlopen(playlist_url) as pl_response:
                    pl_data = json.loads(pl_response.read().decode())
            except Exception:
                st.info("Kanavalla ei ole julkisia videoita tai haku epäonnistui.")
                continue
                
            raw_videos = []
            for item in pl_data.get("items", []):
                snippet_data = item.get("snippet", {})
                resource_id = snippet_data.get("resourceId", {})
                vid = resource_id.get("videoId")
                vtitle = snippet_data.get("title", "Nimetön video")
                v_published_at = snippet_data.get("publishedAt", "")
                
                if vid and v_published_at:
                    try:
                        v_date = datetime.strptime(v_published_at[:10], "%Y-%m-%d").date()
                        if valittu_alkupaiva <= v_date <= valittu_loppupaiva:
                            raw_videos.append({"id": vid, "title": vtitle, "date": v_date})
                    except Exception:
                        continue
            
            ajanjakson_nayttokerrat = 0
            video_list = []
            
            if raw_videos:
                vids_string = ",".join([v["id"] for v in raw_videos])
                stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={vids_string}&key={api_key}"
                
                with urllib.request.urlopen(stats_url) as st_response:
                    st_data = json.loads(st_response.read().decode())
                    
                haetut_tiedot = {}
                for v_item in st_data.get("items", []):
                    v_id = v_item.get("id")
                    v_views = int(v_item.get("statistics", {}).get("viewCount", 0))
                    haetut_tiedot[v_id] = v_views
                
                # Yhdistetään tiedot ja lasketaan tuotot
                for v in raw_videos:
                    v_views = haetut_tiedot.get(v["id"], 0)
                    v_usd = (v_views / 1000) * cpm_rate
                    v_eur = v_usd * eur_rate
                    ajanjakson_nayttokerrat += v_views
                    
                    video_list.append({
                        "Otsikko": v["title"],
                        "Julkaisupäivä": str(v["date"]),
                        "Näyttökerrat": v_views,
                        "Tuotto ($)": round(v_usd, 2),
                        "Tuotto (€)": round(v_eur, 2),
                        "id": v["id"]
                    })
                
                # JÄRJESTYS: Katsotuimmat ensin (voit vaihtaa halutessasi)
                video_list = sorted(video_list, key=lambda x: x["Näyttökerrat"], reverse=True)
                
                jakso_usd = (ajanjakson_nayttokerrat / 1000) * cpm_rate
                jakso_eur = jakso_usd * eur_rate
                
                st.metric("Valitun ajan näyttökerrat", f"{ajanjakson_nayttokerrat:,} kpl")
                
                col_u, col_e = st.columns(2)
                col_u.metric("Tuotot (USD)", f"${jakso_usd:,.2f}")
                col_e.metric("Tuotot (EUR)", f"~{jakso_eur:,.2f} €")
                
                st.markdown("---")
                st.markdown(f"🎬 **Jaksolta löytyneet videot ({len(video_list)} kpl):**")
                
                # Näytetään siistinä taulukkona (jota voi järjestää sarakkeiden mukaan)
                import pandas as pd
                df = pd.DataFrame(video_list)
                # Poistetaan ID-sarake näkyvistä taulukosta
                display_df = df[["Otsikko", "Julkaisupäivä", "Näyttökerrat", "Tuotto ($)", "Tuotto (€)"]]
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            else:
                st.info(f"Ei videoita valitulla aikajaksolla.")
                
        except Exception as e:
            st.error(f"Virhe tietojen käsittelyssä: {e}")

st.markdown("---")
st.caption(f"💡 Laskelmat perustuvat arvoon **${cpm_rate} / 1000 näyttökertaa** ja valuuttakurssiin **{eur_rate} EUR/USD**.")
