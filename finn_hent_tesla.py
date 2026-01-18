import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

URL = "https://www.finn.no/car/used/search.html"

PARAMS = {
    "make": "0.807",  # Tesla
    "sort": "PUBLISHED_DESC",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def finn_modell(text: str) -> str:
    t = text.lower()
    if "model s" in t:
        return "Model S"
    if "model 3" in t:
        return "Model 3"
    if "model x" in t:
        return "Model X"
    if "model y" in t:
        return "Model Y"
    return "Ukjent"


def finn_drivlinje(text: str) -> str:
    t = text.lower()
    if "awd" in t or "firehjul" in t or "dual motor" in t:
        return "AWD"
    if "rwd" in t or "bakhjul" in t:
        return "RWD"
    return "Ukjent"


def finn_farge(text: str) -> str:
    for f in ["svart", "hvit", "kvit", "blå", "rød", "raud", "grå", "sølv"]:
        if f in text.lower():
            return f.capitalize()
    return "Ukjent"


def finn_interiør(text: str) -> str:
    t = text.lower()
    if "hvitt interiør" in t or "kvit interiør" in t:
        return "Hvitt"
    if "svart interiør" in t:
        return "Svart"
    return "Ukjent"


def hent_tesla_dataframe(max_pages: int = 10, sleep_sec: int = 1) -> pd.DataFrame:
    annonser = []

    for page in range(1, max_pages + 1):
        PARAMS["page"] = page

        r = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=30)
        print("Status:", r.status_code, "Page:", page)

        soup = BeautifulSoup(r.text, "html.parser")
        arts = soup.select("article")
        print("Fant article:", len(arts))

        # STOPP når side 2+ er tom (FINN er JS-basert videre paging)
        if page > 1 and len(arts) == 0:
            print("Stopper: FINN gir ingen <article> på side", page)
            break

        for art in arts:
            try:
                arts = soup.select("article")
print("Fant article:", len(arts))

# STOPP når side 2+ er tom (FINN er JS-basert videre paging)
if page > 1 and len(arts) == 0:
    print("Stopper: FINN gir ingen <article> på side", page)
    break

for art in arts:
    try:
        tekst = art.get_text(" ", strip=True)
        tittel_tag = art.select_one("h2")
        pris_tag = art.select_one("[data-testid='price']")

        if not tittel_tag or not pris_tag:
            continue

        tittel = tittel_tag.get_text(strip=True)

        pris_txt = pris_tag.get_text()
        pris = int(re.sub(r"\D", "", pris_txt))

        km_match = re.search(r"(\d[\d\s]*)\s?km", tekst)
        km = int(km_match.group(1).replace(" ", "")) if km_match else None

        år_match = re.search(r"(19|20)\d{2}", tekst)
        år = int(år_match.group()) if år_match else None

        a = art.find("a", href=True)
        full_lenke = "https://www.finn.no" + a["href"] if a else None

        annonser.append(
            {
                "Modell": finn_modell(tittel),
                "Årsmodell": år,
                "Km": km,
                "Pris": pris,
                "Drivlinje": finn_drivlinje(tekst),
                "Farge": finn_farge(tekst),
                "Interiør": finn_interiør(tekst),
                "FINN-link": full_lenke,
            }
        )
    except Exception:
        continue

time.sleep(sleep_sec)


    df = pd.DataFrame(annonser)

    # Fix 2: sørg for tom DF med kolonner hvis ingen annonser
    if df.empty:
        print("Ingen annonser samlet.")
        return pd.DataFrame(
            columns=[
                "Modell",
                "Årsmodell",
                "Km",
                "Pris",
                "Drivlinje",
                "Farge",
                "Interiør",
                "FINN-link",
            ]
        )

    return df


def lagre_csv(filename: str = "tesla_finn.csv", max_pages: int = 10) -> pd.DataFrame:
    df = hent_tesla_dataframe(max_pages=max_pages)
    print("Antall annonser funnet:", len(df))
    df.to_csv(filename, index=False)
    return df
