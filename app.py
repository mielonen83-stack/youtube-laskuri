import streamlit as st
import urllib.request
import json
from datetime import date, datetime, timedelta
import pandas as pd

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
st.sidebar.subheader("🎯 Tuottotavoite")
valuutta_valinta = st.sidebar.radio("Tavoitteen valuutta:", ["EUR (€)", "USD ($)"], horizontal=True)

if valuutta_valinta == "EUR (€)":
    tavoite_eur = st.sidebar.number_input("Aseta tavoite (€ EUR)", min_value=100, max_value=100000, value=1000, step=100)
    tavoite_usd = tavoite_eur / eur_rate
else:
    tavoite_usd = st.sidebar.number_input("Aseta tavoite ($ USD)", min_value=100, max_value=100000, value=1000, step=100)
    tavoite_eur = tavoite_usd * eur_rate

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

kaikki_nayttokerrat_yhteensa = 0
kaikki_videot_data = []

sarakkeet = st.columns(len(kanavat))

for idx, (nimi, channel_id) in enumerate(kanavat.items()):
    with sarakkeet[idx]:
        st.markdown(f"### 📊 {nimi}")
        
        if not channel_id or channel_id == "UCxxxxxxxxxxxxxx":
            st.warning("Kanavan ID puuttuu tai on oletusarvona asetuksista.")
            continue
            
        try:
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
                
                paiva_kohtaiset_keskiarvot = []
                temp_calc = []
                for v in raw_videos:
                    v_views = haetut_tiedot.get(v["id"], 0)
                    paivia_olemassa = (tanaan - v["date"]).days
                    if paivia_olemassa < 1:
                        paivia_olemassa = 1
                    vpaiva = v_views / paivia_olemassa
                    paiva_kohtaiset_keskiarvot.append(vpaiva)
                    temp_calc.append((v, v_views, vpaiva))

                keskiarvo_tahti = sum(paiva_kohtaiset_keskiarvot) / len(paiva_kohtaiset_keskiarvot) if paiva_kohtaiset_keskiarvot else 1

                for v, v_views, vpaiva in temp_calc:
                    v_usd = (v_views / 1000) * cpm_rate
                    v_eur = v_usd * eur_rate
                    ajanjakson_nayttokerrat += v_views
                    kaikki_nayttokerrat_yhteensa += v_views
                    
                    if vpaiva > keskiarvo_tahti * 1.5:
                        trendi = "🚀 Nousussa"
                    elif vpaiva < keskiarvo_tahti * 0.5:
                        trendi = "💤 Hiljainen"
                    else:
                        trendi = "⚖️ Tasainen"

                    v_linkki = f"https://www.youtube.com/watch?v={v['id']}"

                    v_info = {
                        "Kanava": nimi,
                        "Otsikko": v["title"],
                        "Julkaisupäivä": str(v["date"]),
                        "Näyttökerrat": v_views,
                        "Trendi": trendi,
                        "Tuotto ($)": round(v_usd, 2),
                        "Tuotto (€)": round(v_eur, 2),
                        "Linkki": v_linkki
                    }
                    video_list.append(v_info)
                    kaikki_videot_data.append(v_info)
                
                video_list = sorted(video_list, key=lambda x: x["Näyttökerrat"], reverse=True)
                
                jakso_usd = (ajanjakson_nayttokerrat / 1000) * cpm_rate
                jakso_eur = jakso_usd * eur_rate
                
                st.metric("Valitun ajan näyttökerrat", f"{ajanjakson_nayttokerrat:,} kpl")
                
                col_u, col_e = st.columns(2)
                col_u.metric("Tuotot (USD)", f"${jakso_usd:,.2f}")
                col_e.metric("Tuotot (EUR)", f"~{jakso_eur:,.2f} €")
                
                if video_list:
                    paras_video = video_list[0]
                    st.success(f"🏆 **Kanavan hitti:**\n[{paras_video['Otsikko']}]({paras_video['Linkki']})\n({paras_video['Näyttökerrat']:,} näyttöä | ~{paras_video['Tuotto (€)']:,} €)")
                
                st.markdown("---")
                st.markdown(f"🎬 **Löytyneet videot ({len(video_list)} kpl):**")
                
                df_kanava = pd.DataFrame(video_list)
                display_df = df_kanava[["Otsikko", "Julkaisupäivä", "Näyttökerrat", "Trendi", "Tuotto ($)", "Tuotto (€)"]]
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                with st.expander(f"🔗 Avaa suorat YouTube-linkit ({nimi})"):
                    for v in video_list:
                        st.markdown(f"[{v['Otsikko']}]({v['Linkki']}) — 👁️ {v['Näyttökerrat']:,} näyttöä ({v['Trendi']})")
                
            else:
                st.info(f"Ei videoita valitulla aikajaksolla.")
                
        except Exception as e:
            st.error(f"Virhe tietojen käsittelyssä: {e}")

# --- KOKONAISYHTEENVETO JA TAVOITE ---
if len(kanavat) > 1 and kaikki_nayttokerrat_yhteensa > 0:
    st.markdown("---")
    st.header("🌐 Kaikkien kanavien kokonaissaldo yhteensä")
    
    kokonais_usd = (kaikki_nayttokerrat_yhteensa / 1000) * cpm_rate
    kokonais_eur = kokonais_usd * eur_rate
    
    col_tot1, col_tot2, col_tot3 = st.columns(3)
    col_tot1.metric("Kokonaisnäyttökerrat", f"{kaikki_nayttokerrat_yhteensa:,} kpl")
    col_tot2.metric("Kokonistuotot (USD)", f"${kokonais_usd:,.2f}")
    col_tot3.metric("Kokonistuotot (EUR)", f"~{kokonais_eur:,.2f} €")

# --- TUOTTOTAVOITTEEN SEURANTA ---
if kaikki_videot_data:
    st.markdown("---")
    st.header("🎯 Tuottotavoitteen seurunta")
    
    nykyiset_tuotot_usd = (kaikki_nayttokerrat_yhteensa / 1000) * cpm_rate
    nykyiset_tuotot_eur = nykyiset_tuotot_usd * eur_rate
    
    prosentti = min(int((nykyiset_tuotot_usd / tavoite_usd) * 100), 100)
    
    st.write(f"Asetettu tavoite: **{tavoite_eur:,.2f} €** (${tavoite_usd:,.2f}) | Nykyinen tuotto: **~{nykyiset_tuotot_eur:,.2f} €** (${nykyiset_tuotot_usd:,.2f}) — **{prosentti}% saavutettu**")
    st.progress(prosentti / 100.0)
    
    if nykyiset_tuotot_usd >= tavoite_usd:
        st.success("🎉 Onneksi olkoon! Olet saavuttanut asettamasi tuottotavoitteen tällä aikajaksolla!")
    else:
        puuttuu_usd = tavoite_usd - nykyiset_tuotot_usd
        puuttuu_eur = tavoite_eur - nykyiset_tuotot_eur
        puuttuu_nayttoja = int((puuttuu_usd / cpm_rate) * 1000)
        
        # Lasketaan virstanpylväitä
        tuhat_videot = puuttuu_nayttoja / 1000
        kymppi_videot = puuttuu_nayttoja / 10000
        satku_videot = puuttuu_nayttoja / 100000
        
        # Keskiarvo per video valitulla aikajaksolla
        löytyneiden_maara = len(kaikki_videot_data)
        keskiarvo_per_video_eur = (puuttuu_eur / löytyneiden_maara) if löytyneiden_maara > 0 else 0
        keskiarvo_per_video_naytot = int(puuttuu_nayttoja / löytyneiden_maara) if löytyneiden_maara > 0 else 0

        st.info(f"💡 Tavoitteesta puuttuu vielä **~{puuttuu_eur:,.2f} €** (${puuttuu_usd:,.2f}), mikä vaatii noin **{puuttuu_nayttoja:,}** uutta näyttökertaa.")
        
        # Havainnollistavat esimerkit tarkennetulla tekstillä
        st.markdown(f"##### 📐 Mitä tämä vaatii käytännössä (perustuu valittuun aikajaksoon: {valittu_alkupaiva} – {valittu_loppupaiva})?")
        col_v1, col_v2, col_v3 = st.columns(3)
        col_v1.metric("10k näyttökerran videoita", f"~{kymppi_videot:.1f} kpl")
        col_v2.metric("1k näyttökerran videoita", f"~{tuhat_videot:.1f} kpl")
        col_v3.metric("Lisätuottoa / video", f"~{keskiarvo_per_video_eur:,.2f} € / kpl ({löytyneiden_maara} videota)")

# --- LATAUSPAINIKE ---
if kaikki_videot_data:
    st.markdown("---")
    df_kaikki = pd.DataFrame(kaikki_videot_data)
    csv = df_kaikki.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Lataa kaikki tiedot CSV-tiedostona (Exceliin)",
        data=csv,
        file_name=f"youtube_tulot_{valittu_alkupaiva}_{valittu_loppupaiva}.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption(f"💡 Laskelmat perustuvat arvoon **${cpm_rate} / 1000 näyttökertaa** ja valuuttakurssiin **{eur_rate} EUR/USD**.")
