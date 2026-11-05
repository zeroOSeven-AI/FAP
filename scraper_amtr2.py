import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

# URL-ovi za 4 glavne kategorije
URLS = {
    "LATEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "BEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "MOST_COMMENTS": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "RANDOM": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=rand&category%5B0%5D=2&gender%5B0%5D=1&trans=without"
}

def get_focus_y(w, h):
    ratio = w / h
    if ratio < 0.8: return 0.30
    elif ratio < 1.0: return 0.38
    elif ratio < 1.3: return 0.45
    else: return 0.50

def get_image_info(scraper, url):
    if not url: return None
    try:
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https://www.amateri.com' + url
        
        headers = {
            "Referer": "https://www.amateri.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = scraper.get(url, timeout=15, headers=headers)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            w, h = img.size
            focus_y = get_focus_y(w, h)
            img.thumbnail((600, 600)) 
            buffered = BytesIO()
            img.convert('RGB').save(buffered, format="JPEG", quality=75)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"b64": f"data:image/jpeg;base64,{img_str}", "w": w, "h": h, "focus_y": focus_y}
    except:
        pass
    return None

def fetch_albums_from_url(scraper, url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = scraper.get(url, timeout=30, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        album_items = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/album/' in href and not any(x in href for x in ['/albums', 'upload', 'search']):
                img = link.find('img')
                if img:
                    album_url = "https://www.amateri.com" + href if href.startswith('/') else href
                    raw_img = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
                    if raw_img and not any(x in raw_img.lower() for x in ["logo", "default-avatar"]):
                        album_items.append({"link": album_url, "img_url": raw_img})
        return album_items
    except Exception as e:
        print(f"Greška pri dohvaćanju URL-a: {e}")
        return []

def scrape_amateri():
    scraper = cloudscraper.create_scraper()
    final_widgets = [None] * 6 
    used_links = set()
    
    print("⏳ Skupljam sve dostupne albume sa stranica...")
    latest_list = fetch_albums_from_url(scraper, URLS["LATEST"])
    time.sleep(1)
    best_list = fetch_albums_from_url(scraper, URLS["BEST"])
    time.sleep(1)
    comments_list = fetch_albums_from_url(scraper, URLS["MOST_COMMENTS"])
    time.sleep(1)
    random_list = fetch_albums_from_url(scraper, URLS["RANDOM"])
    
    # POPRAVLJENA FUNKCIJA: Prolazi kroz cijelu listu dok god ne nađe slobodan album, ne odustaje na prvom duplikatu!
    def pop_unique_album(album_list, debug_name):
        for item in album_list:
            if item["link"] not in used_links:
                print(f"   🔎 [{debug_name}] Pokušavam uzeti: {item['link']}")
                info = get_image_info(scraper, item["img_url"])
                if info:
                    used_links.add(item["link"])
                    return {
                        "image_b64": info["b64"], "w": info["w"], "h": info["h"],
                        "focus_y": info["focus_y"], "link": item["link"]
                    }
                else:
                    print(f"   ⚠ Slika ne radi za {item['link']}, tražim sljedeći...")
            else:
                print(f"   ⏭ Preskačem duplikat za [{debug_name}]: {item['link']}")
        return None

    # Polje 1: LATEST 1
    res = pop_unique_album(latest_list, "LATEST 1")
    if res: final_widgets[0] = {**res, "source_title1": "LATEST 1", "source_title2": "AMATERI"}
    
    # Polje 2: LATEST 2 (uzima idući najnoviji)
    res = pop_unique_album(latest_list, "LATEST 2")
    if res: final_widgets[1] = {**res, "source_title1": "LATEST 2", "source_title2": "AMATERI"}
    
    # Polje 3: LATEST 3 (uzima treći najnoviji)
    res = pop_unique_album(latest_list, "LATEST 3")
    if res: final_widgets[2] = {**res, "source_title1": "LATEST 3", "source_title2": "AMATERI"}
    
    # Polje 4: BEST
    res = pop_unique_album(best_list, "BEST")
    if res: final_widgets[3] = {**res, "source_title1": "BEST", "source_title2": "AMATERI"}
    
    # Polje 5: MOST COMMENTS (ako je prvi isti kao u BEST, petlja sada ide dalje i uzima idući s najviše komentara)
    res = pop_unique_album(comments_list, "MOST COMMENTS")
    if res: final_widgets[4] = {**res, "source_title1": "MOST COMMENTS", "source_title2": "AMATERI"}
    
    # Polje 6: RANDOM
    res = pop_unique_album(random_list, "RANDOM")
    if res: final_widgets[5] = {**res, "source_title1": "RANDOM", "source_title2": "AMATERI"}

    # Spremanje isključivo popunjenih widgeta
    news_items = [x for x in final_widgets if x is not None]

    with open('amateri_news.json', 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    print(f"\n✅ JSON uspješno spremljen! Ukupno stavki: {len(news_items)}/6")

if __name__ == "__main__":
    scrape_amateri()
