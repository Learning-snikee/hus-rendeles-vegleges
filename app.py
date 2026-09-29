import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. TERMÉKKATALÓGUS ---
PRODUCT_CATALOG = [
    {"nev": "Sertés comb", "fogy_ar": 1386, "arres_stop": "Igen"},
    {"nev": "Sertés lapocka", "fogy_ar": 1790, "arres_stop": "Nem"},
    {"nev": "Sertés oldalas", "fogy_ar": 1848, "arres_stop": "Igen"},
    {"nev": "Sertés dagadó", "fogy_ar": 2090, "arres_stop": "Nem"},
    {"nev": "Sertés karaj csontos", "fogy_ar": 1617, "arres_stop": "Igen"},
    {"nev": "Sertés tarja csontos", "fogy_ar": 1871, "arres_stop": "Igen"},
    {"nev": "S.karaj csont nélkül", "fogy_ar": 1617, "arres_stop": "Igen"},
    {"nev": "S.tarja csont nélkül", "fogy_ar": 1871, "arres_stop": "Igen"},
    {"nev": "Sertés szűzpecsenye", "fogy_ar": 2999, "arres_stop": "Nem"},
    {"nev": "Sertés máj", "fogy_ar": 829, "arres_stop": "Nem"},
    {"nev": "S.húsos csont", "fogy_ar": 499, "arres_stop": "Nem"},
    {"nev": "Sertés h.csülök csont nélkül", "fogy_ar": 1990, "arres_stop": "Nem"},
    {"nev": "Darált hús", "fogy_ar": 2499, "arres_stop": "Nem"}
]

# Biztonsági adatbázis: Token -> Partner adatai
PARTNERS_DATABASE = {
    "token_bolt1": {"nev": "Szombathelyi 4-es Bolt", "email": "bolt1@gmail.com"},
    "token_partner2": {"nev": "Győri Lerakat", "email": "partner2@partner.hu"},
    "token_videki": {"nev": "Vidéki Húsbolt", "email": "videki_husbolt@t-online.hu"}
}

# --- 2. OLDAL BEÁLLÍTÁSAI ---
st.set_page_config(page_title="Húsipari Rendelési Felület", page_icon="🥩", layout="wide")
st.title("🥩 Digitális Megrendelőlap")
st.subheader("Babati-Hús Kft. – Aktuális heti árlista és rendelés")

# --- 3. BIZTONSÁGI SZŰRŐ ---
query_params = st.query_params

if "token" not in query_params or query_params["token"] not in PARTNERS_DATABASE:
    st.error("❌ Hiba: Érvénytelen vagy hiányzó hozzáférési link!")
    st.info("Kérjük, a Babati-Hús Kft. által kiküldött hivatalos, egyedi linket használja a rendeléshez.")
    st.stop()

aktiv_token = query_params["token"]
partner_adatok = PARTNERS_DATABASE[aktiv_token]
partner_name = partner_adatok["nev"]
email_input = partner_adatok["email"]

st.success(f"Bejelentkezett partner: **{partner_name}**")
st.write("---")

# --- 4. INTERAKTÍV RENDELÉS BEÍRÁS ---
osszesen_ft = 0
vegleges_tetelek = []
nyers_adatok_menteshez = []

col1, col2, col3, col4 = st.columns(4)
col1.markdown("**Termék megnevezése**")
col2.markdown("**Fogyasztói ár (Ft/kg)**")
col3.markdown("**Árrés-stop?**")
col4.markdown("**Rendelt mennyiség (kg)**")

for index, termek in enumerate(PRODUCT_CATALOG):
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**{termek['nev']}**")
    c2.write(f"{termek['fogy_ar']:,} Ft / kg".replace(",", " "))
    c3.write(termek['arres_stop'])
    
    mennyiseg = c4.number_input(
        f"kg_{index}", 
        min_value=0.0, 
        max_value=1000.0, 
        value=0.0, 
        step=0.5, 
        label_visibility="collapsed"
    )
    
    if mennyiseg > 0:
        reszosszeg = termek['fogy_ar'] * mennyiseg
        osszesen_ft += reszosszeg
        
        vegleges_tetelek.append({
            "Termék": termek['nev'],
            "Mennyiség (kg)": mennyiseg,
            "Egységár": f"{termek['fogy_ar']} Ft",
            "Részösszeg": f"{round(reszosszeg):,} Ft".replace(",", " ")
        })
        
        nyers_adatok_menteshez.append({
            "Időbélyeg": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Partner": partner_name,
            "Email": email_input,
            "Termék": termek['nev'],
            "Mennyiség": mennyiseg,
            "Egységár": termek['fogy_ar'],
            "Részösszeg": round(reszosszeg)
        })

st.write("---")
st.write(f"## Fizetendő végösszeg: **{round(osszesen_ft):,} Ft**".replace(",", " "))

# --- 5. RENDELÉS LEZÁRÁSA ÉS KÜLDÉSE ---
if len(vegleges_tetelek) > 0:
    st.write("### Kiválasztott tételek áttekintése:")
    st.dataframe(pd.DataFrame(vegleges_tetelek), use_container_width=True)
    
    if st.button("RENDELÉS VÉGLEGESÍTÉSE ÉS LEZÁRÁSA", type="primary"):
        with st.spinner("Rendelés küldése a központi Google Táblázatba..."):
            try:
                # 🔴 A 97. SORBAN CSERÉLD KI AZ ALÁBBI LINKET A SAJÁTODRA 🔴
                GOOGLE_SCRIPT_URL = "IDE_MASOLD_BE_A_GOOGLE_SCRIPT_LINKET"
                
                response = requests.post(GOOGLE_SCRIPT_URL, json=nyers_adatok_menteshez)
                
                if response.status_code == 200:
                    st.success("A rendelését sikeresen rögzítettük a központi rendszerben!")
                    st.balloons()
                else:
                    st.error("Hiba történt a szerver kapcsolatban, kérjük próbálja újra.")
            except Exception as e:
                st.error(f"Hiba történt a mentés során: {str(e)}")
else:
    st.warning("Még nem írt be mennyiséget egyetlen termékhez sem.")
