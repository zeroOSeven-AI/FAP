
import json
import cloudscraper
import base64
import time
import os

from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# ==========================================
# PODEŠAVANJA
# ==========================================

URLS = {
    "LATEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without",

    "BEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&trans=without",

    "MOST_COMMENTS": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&gender%5B0%5D=1&trans=without",

    "RANDOM": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=rand&category%5B0%5D=2&gender%5B0%5D=1&trans=without"
}


OUTPUT_FILE = "amateri_news.json"
DEBUG_FILE = "debug_amateri.html"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.amateri.com/"
}


# ==========================================
# POMOĆNE FUNKCIJE
# ==========================================

def get_focus_y(w, h):

    ratio = w / h

    if ratio < 0.8:
        return 0.30

    elif ratio < 1.0:
        return 0.38

    elif ratio < 1.3:
        return 0.45

    else:
        return 0.50


def normalize_url(url):

    if not url:
        return ""

    return urljoin("https://www.amateri.com/", url.strip())


# ==========================================
# PREUZIMANJE I OBRADA SLIKE
# ==========================================

def get_image_info(scraper, url):

    if not url:
        return None

    try:

        url = normalize_url(url)

        response = scraper.get(
            url,
            timeout=20,
            headers=HEADERS
        )

        if response.status_code != 200:

            print(
                f"   ⚠ Slika HTTP greška: "
                f"{response.status_code}"
            )

            return None

        img = Image.open(BytesIO(response.content))
        img.load()

        w, h = img.size

        if w == 0 or h == 0:
            return None

        focus_y = get_focus_y(w, h)

        img.thumbnail((600, 600))

        buffered = BytesIO()

        img.convert("RGB").save(
            buffered,
            format="JPEG",
            quality=75
        )

        img_str = base64.b64encode(
            buffered.getvalue()
        ).decode("utf-8")

        return {
            "b64": f"data:image/jpeg;base64,{img_str}",
            "w": w,
            "h": h,
            "focus_y": focus_y
        }

    except Exception as e:

        print(f"   ⚠ Greška slike: {repr(e)}")

        return None


# ==========================================
# PRONALAŽENJE SLIKA U HTML-U
# ==========================================

def extract_image_url(img):

    attributes = [
        "data-src",
        "data-lazy-src",
        "data-original",
        "data-original-src",
        "data-url",
        "src"
    ]

    for attr in attributes:

        value = img.get(attr)

        if value:
            return value

    # Provera srcset atributa

    srcset = img.get("srcset")

    if srcset:

        first_image = srcset.split(",")[0].strip()

        if first_image:

            return first_image.split(" ")[0]

    return ""


# ==========================================
# SKUPLJANJE ALBUMA
# ==========================================

def fetch_albums_from_url(scraper, url, debug_name):

    print(f"\n🔍 Učitavam kategoriju: {debug_name}")

    try:

        response = scraper.get(
            url,
            timeout=30,
            headers=HEADERS
        )

        print("   HTTP STATUS:", response.status_code)
        print("   FINAL URL:", response.url)
        print("   HTML SIZE:", len(response.text))

        if response.status_code != 200:

            print("   ❌ Server nije vratio HTTP 200.")

            return []

        # Sačuvaj HTML radi dijagnostike

        with open(
            f"debug_{debug_name.lower()}.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(response.text)

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        album_items = []
        seen = set()

        # Pronalazak linkova

        for link in soup.find_all("a", href=True):

            href = link.get("href", "")

            if not href:
                continue

            href_lower = href.lower()

            # Osnovni filter linkova albuma

            if "album" not in href_lower:
                continue

            if any(
                x in href_lower
                for x in [
                    "/albums",
                    "upload",
                    "search"
                ]
            ):
                continue

            img = link.find("img")

            if not img:
                continue

            raw_img = extract_image_url(img)

            if not raw_img:
                continue

            if any(
                x in raw_img.lower()
                for x in [
                    "logo",
                    "default-avatar"
                ]
            ):
                continue

            album_url = normalize_url(href)
            image_url = normalize_url(raw_img)

            if album_url in seen:
                continue

            seen.add(album_url)

            album_items.append({
                "link": album_url,
                "img_url": image_url
            })

        print(
            f"   ✅ Pronađeno albuma: {len(album_items)}"
        )

        # Dodatni pregled HTML-a

        if len(album_items) == 0:

            print("   ⚠ Nije pronađen nijedan album!")

            print(
                "   HTML PREVIEW:\n",
                response.text[:1500]
            )

        return album_items

    except Exception as e:

        print(
            f"   ❌ Greška pri dohvaćanju: {repr(e)}"
        )

        return []


# ==========================================
# IZBOR JEDINSTVENOG ALBUMA
# ==========================================

def pop_unique_album(
    scraper,
    album_list,
    used_links,
    debug_name
):

    for item in album_list:

        album_link = item["link"]

        if album_link in used_links:

            print(
                f"   ⏭ Duplikat [{debug_name}]: "
                f"{album_link}"
            )

            continue

        print(
            f"   🔎 [{debug_name}] Pokušavam: "
            f"{album_link}"
        )

        info = get_image_info(
            scraper,
            item["img_url"]
        )

        if not info:

            print(
                f"   ⚠ Slika nije dostupna: "
                f"{album_link}"
            )

            continue

        used_links.add(album_link)

        print(
            f"   ✅ Uspešno preuzet album: "
            f"{album_link}"
        )

        return {
            "image_b64": info["b64"],
            "w": info["w"],
            "h": info["h"],
            "focus_y": info["focus_y"],
            "link": album_link
        }

    print(
        f"   ❌ Nema više dostupnih albuma za "
        f"{debug_name}"
    )

    return None


# ==========================================
# GLAVNA FUNKCIJA
# ==========================================

def scrape_amateri():

    scraper = cloudscraper.create_scraper()

    final_widgets = [None] * 6

    used_links = set()

    print("\n================================")
    print("       AMATERI SCRAPER")
    print("================================")

    print(
        "\n⏳ Skupljam sve dostupne albume..."
    )

    # Preuzimanje kategorija

    latest_list = fetch_albums_from_url(
        scraper,
        URLS["LATEST"],
        "LATEST"
    )

    time.sleep(1)

    best_list = fetch_albums_from_url(
        scraper,
        URLS["BEST"],
        "BEST"
    )

    time.sleep(1)

    comments_list = fetch_albums_from_url(
        scraper,
        URLS["MOST_COMMENTS"],
        "MOST_COMMENTS"
    )

    time.sleep(1)

    random_list = fetch_albums_from_url(
        scraper,
        URLS["RANDOM"],
        "RANDOM"
    )

    print("\n================================")
    print("       OBRADA ALBUMA")
    print("================================")

    # POZICIJA 1

    res = pop_unique_album(
        scraper,
        latest_list,
        used_links,
        "LATEST 1"
    )

    if res:

        final_widgets[0] = {
            **res,
            "source_title1": "LATEST 1",
            "source_title2": "AMATERI"
        }

    # POZICIJA 2

    res = pop_unique_album(
        scraper,
        latest_list,
        used_links,
        "LATEST 2"
    )

    if res:

        final_widgets[1] = {
            **res,
            "source_title1": "LATEST 2",
            "source_title2": "AMATERI"
        }

    # POZICIJA 3

    res = pop_unique_album(
        scraper,
        latest_list,
        used_links,
        "LATEST 3"
    )

    if res:

        final_widgets[2] = {
            **res,
            "source_title1": "LATEST 3",
            "source_title2": "AMATERI"
        }

    # POZICIJA 4

    res = pop_unique_album(
        scraper,
        best_list,
        used_links,
        "BEST"
    )

    if res:

        final_widgets[3] = {
            **res,
            "source_title1": "BEST",
            "source_title2": "AMATERI"
        }

    # POZICIJA 5

    res = pop_unique_album(
        scraper,
        comments_list,
        used_links,
        "MOST COMMENTS"
    )

    if res:

        final_widgets[4] = {
            **res,
            "source_title1": "MOST COMMENTS",
            "source_title2": "AMATERI"
        }

    # POZICIJA 6

    res = pop_unique_album(
        scraper,
        random_list,
        used_links,
        "RANDOM"
    )

    if res:

        final_widgets[5] = {
            **res,
            "source_title1": "RANDOM",
            "source_title2": "AMATERI"
        }

    # ======================================
    # SPREMANJE JSON-A
    # ======================================

    news_items = [
        item
        for item in final_widgets
        if item is not None
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            news_items,
            f,
            ensure_ascii=False,
            indent=4
        )

    print("\n================================")
    print("       REZULTAT")
    print("================================")

    print(
        f"\n✅ JSON spremljen: {OUTPUT_FILE}"
    )

    print(
        f"📦 Ukupno stavki: "
        f"{len(news_items)}/6"
    )

    print(
        f"🔗 Jedinstvenih linkova: "
        f"{len(used_links)}"
    )

    print("\n🏁 GOTOVO!")


# ==========================================
# POKRETANJE
# ==========================================

if __name__ == "__main__":

    scrape_amateri()
