import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# --- 1. ADATBÁZIS (A KÉP ALAPJÁN) ---
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

ALLOWED_PARTNERS = {
    "snikee@gmail.com": "Szombathelyi 4-es Bolt",
    "hayhay4y@gmail.com": "próbabolt2",
    "próba@t-online.hu": "Vidéki Húsbolt"
}

# --- 2. GOOGLE SHEETS KAPCSOLAT INICIALIZÁLÁSA ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

# --- 3. OLDAL BEÁLLÍTÁSAI ---
st.set_page_config(page_title="Húsipari Rendelési Felület", page_icon="🥩", layout="wide")

st.title("🥩 Digitális Megrendelőlap")
st.subheader("Babati-Hús Kft. – Aktuális heti árlista és rendelés")

# --- 4. PARTNER AZONOSÍTÁSA ---
email_input = st.selectbox("Kérjük, válassza ki az Ön regisztrált e-mail címét:", list(ALLOWED_PARTNERS.keys()))
partner_name = ALLOWED_PARTNERS[email_input]

st.info(f"Bejelentkezett partner: **{partner_name}** ({email_input})")

# Heti fix adatok
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("Szállítási hét", "2026 / 39. hét")
col_info2.metric("Lemondási határidő", "Szept. 17. 11:00")
col_info3.metric("Rendelés állapota", "NYITVA")

st.write("---")

# --- 5. INTERAKTÍV RENDELÉS BEÍRÁS ---
st.write("### Termékkatalógus")

rendelesek = {}
osszesen_ft = 0
vegleges_tetelek = []
nyers_adatok_menteshez = []

col1, col2, col3, col4 = st.columns()
col1.markdown("**Termék megnevezése**")
col2.markdown("**Fogyasztói ár (Ft/kg)**")
col3.markdown("**Árrés-stop?**")
col4.markdown("**Rendelt mennyiség (kg)**")

for index, termek in enumerate(PRODUCT_CATALOG):
    c1, c2, c3, c4 = st.columns()
    
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
            "Részösszeg": f"{round(reszosszeg):,}".replace(",", " ") + " Ft"
        })
        
        nyers_adatok_menteshez.append({
            "Időbélyeg": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Partner": partner_name,
            "Email": email_input,
            "Termék": termek['nev'],
            "Mennyiség (kg)": mennyiseg,
            "Egységár": termek['fogy_ar'],
            "Részösszeg": round(reszosszeg)
        })

st.write("---")

# --- 6. ÖSSZESÍTŐ ÉS GOOGLE SHEETS MENTÉS ---
st.write(f"## Fizetendő végösszeg: **{round(osszesen_ft):,} Ft**".replace(",", " "))

if len(vegleges_tetelek) > 0:
    st.write("### Kiválasztott tételek áttekintése:")
    st.dataframe(pd.DataFrame(vegleges_tetelek), use_container_width=True)
    
    if st.button("RENDELÉS VÉGLEGESÍTÉSE ÉS LEZÁRÁSA", type="primary"):
        with st.spinner("Rendelés rögzítése a központi Google Táblázatban..."):
            try:
                if conn is not None:
                    existing_data = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"])
                    existing_df = pd.DataFrame(existing_data)
                    
                    new_rows_df = pd.DataFrame(nyers_adatok_menteshez)
                    updated_df = pd.concat([existing_df, new_rows_df], ignore_index=True)
                    
                    conn.update(
                        spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
                        data=updated_df
                    )
                    
                    st.success(f"Köszönjük, {partner_name}! A rendelést sikeresen mentettük a Google Táblázatba.")
                    st.balloons()
                else:
                    st.warning("Lokális teszt mód: A Google Sheets kapcsolat nincs konfigurálva.")
                    st.json(nyers_adatok_menteshez)
                    st.balloons()
                    
            except Exception as e:
                st.error(f"Hiba történt a mentés során: {str(e)}")
else:
    st.warning("Még nem írt be mennyiséget egyetlen termékhez sem.")
