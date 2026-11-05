
import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

# ==========================================
# URL-OVI
# ==========================================

URLS = {
    "LATEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without",

    "BEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&trans=without",

    "MOST_COMMENTS": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&gender%5B0%5D=1&trans=without",

    "RANDOM": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=rand&category%5B0%5D=2&gender%5B0%5D=1&trans=without"
}


# ==========================================
# FOKUS SLIKE
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


# ==========================================
# PREUZIMANJE SLIKE
# ==========================================

def get_image_info(scraper, url):

    if not url:
        return None

    try:

        if url.startswith('//'):
            url = 'https:' + url

        elif url.startswith('/'):
            url = 'https://www.amateri.com' + url

        headers = {
            "Referer": "https://www.amateri.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        res = scraper.get(
            url,
            timeout=15,
            headers=headers
        )

        if res.status_code == 200:

            img = Image.open(BytesIO(res.content))
            img.load()

            w, h = img.size

            if w <= 0 or h <= 0:
                return None

            focus_y = get_focus_y(w, h)

            img.thumbnail((600, 600))

            buffered = BytesIO()

            img.convert('RGB').save(
                buffered,
                format="JPEG",
                quality=75
            )

            img_str = base64.b64encode(
                buffered.getvalue()
            ).decode()

            return {
                "b64": f"data:image/jpeg;base64,{img_str}",
                "w": w,
                "h": h,
                "focus_y": focus_y
            }

        else:

            print(
                f"   ⚠ HTTP {res.status_code} "
                f"pri preuzimanju slike"
            )

    except Exception as e:

        print(f"   ⚠ Greška slike: {e}")

    return None


# ==========================================
# DOHVAT ALBUMA
# ORIGINALNI NAČIN ZAHTJEVA
# ==========================================

def fetch_albums_from_url(scraper, url):

    try:

        # Namjerno zadržan originalni User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = scraper.get(
            url,
            timeout=30,
            headers=headers
        )

        print(f"   HTTP STATUS: {response.status_code}")

        if response.status_code != 200:

            print("   ❌ Server odbio zahtjev.")

            # Sačuvaj odgovor za dijagnostiku
            with open(
                "debug_403.html",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(response.text)

            return []

        soup = BeautifulSoup(
            response.text,
            'html.parser'
        )

        album_items = []
        seen_links = set()

        for link in soup.find_all('a', href=True):

            href = link.get('href', '')

            if '/album/' not in href:
                continue

            if any(
                x in href
                for x in ['/albums', 'upload', 'search']
            ):
                continue

            img = link.find('img')

            if not img:
                continue

            raw_img = (
                img.get('data-src')
                or img.get('data-lazy-src')
                or img.get('src')
                or ""
            )

            if not raw_img:
                continue

            if any(
                x in raw_img.lower()
                for x in ["logo", "default-avatar"]
            ):
                continue

            album_url = (
                "https://www.amateri.com" + href
                if href.startswith('/')
                else href
            )

            if album_url in seen_links:
                continue

            seen_links.add(album_url)

            album_items.append({
                "link": album_url,
                "img_url": raw_img
            })

        print(
            f"   ✅ Pronađeno albuma: {len(album_items)}"
        )

        return album_items

    except Exception as e:

        print(
            f"   ❌ Greška pri dohvaćanju URL-a: {e}"
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

        if item["link"] not in used_links:

            print(
                f"   🔎 [{debug_name}] Pokušavam uzeti: "
                f"{item['link']}"
            )

            info = get_image_info(
                scraper,
                item["img_url"]
            )

            if info:

                used_links.add(item["link"])

                return {
                    "image_b64": info["b64"],
                    "w": info["w"],
                    "h": info["h"],
                    "focus_y": info["focus_y"],
                    "link": item["link"]
                }

            else:

                print(
                    f"   ⚠ Slika ne radi za "
                    f"{item['link']}, tražim sljedeći..."
                )

        else:

            print(
                f"   ⏭ Preskačem duplikat za "
                f"[{debug_name}]: {item['link']}"
            )

    return None


# ==========================================
# GLAVNA FUNKCIJA
# ==========================================

def scrape_amateri():

    scraper = cloudscraper.create_scraper()

    final_widgets = [None] * 6

    used_links = set()

    print("⏳ Skupljam sve dostupne albume sa stranica...")

    # Preuzimanje kategorija

    latest_list = fetch_albums_from_url(
        scraper,
        URLS["LATEST"]
    )

    time.sleep(1)

    best_list = fetch_albums_from_url(
        scraper,
        URLS["BEST"]
    )

    time.sleep(1)

    comments_list = fetch_albums_from_url(
        scraper,
        URLS["MOST_COMMENTS"]
    )

    time.sleep(1)

    random_list = fetch_albums_from_url(
        scraper,
        URLS["RANDOM"]
    )

    # ======================================
    # POLJE 1: LATEST 1
    # ======================================

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

    # ======================================
    # POLJE 2: LATEST 2
    # ======================================

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

    # ======================================
    # POLJE 3: LATEST 3
    # ======================================

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

    # ======================================
    # POLJE 4: BEST
    # ======================================

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

    # ======================================
    # POLJE 5: MOST COMMENTS
    # ======================================

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

    # ======================================
    # POLJE 6: RANDOM
    # ======================================

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
    # JSON
    # ======================================

    news_items = [
        x for x in final_widgets
        if x is not None
    ]

    with open(
        'amateri_news.json',
        'w',
        encoding='utf-8'
    ) as f:

        json.dump(
            news_items,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"\n✅ JSON uspješno spremljen! "
        f"Ukupno stavki: {len(news_items)}/6"
    )


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    scrape_amateri()
