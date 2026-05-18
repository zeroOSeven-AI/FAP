import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

# URL-ovi: Za NEXT kategorije skačemo odmah na stranicu 2 (&page=2) da dobijemo nove unikatne albume
URLS = {
    "LATEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "BEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "MOST_COMMENTS": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "RANDOM": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=rand&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "LATEST_NEXT": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without&page=2",
    "BEST_NEXT": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&trans=without&page=2"
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
    
    print("⏳ Skupljam albume (Stranica 1 i Stranica 2)...")
    latest_list = fetch_albums_from_url(scraper, URLS["LATEST"])
    time.sleep(1)
    best_list = fetch_albums_from_url(scraper, URLS["BEST"])
    time.sleep(1)
    comments_list = fetch_albums_from_url(scraper, URLS["MOST_COMMENTS"])
    time.sleep(1)
    random_list = fetch_albums_from_url(scraper, URLS["RANDOM"])
    time.sleep(1)
    latest_next_list = fetch_albums_from_url(scraper, URLS["LATEST_NEXT"])
    time.sleep(1)
    best_next_list = fetch_albums_from_url(scraper, URLS["BEST_NEXT"])
    
    def pop_unique_album(album_list, debug_name):
        for item in album_list:
            if item["link"] not in used_links:
                info = get_image_info(scraper, item["img_url"])
                if info:
                    used_links.add(item["link"])
                    return {
                        "image_b64": info["b64"], "w": info["w"], "h": info["h"],
                        "focus_y": info["focus_y"], "link": item["link"]
                    }
        return None

    # Punjenje 6 polja iz zasebnih lista
    print("📦 Pakiram Polje 1: LATEST")
    res = pop_unique_album(latest_list, "LATEST")
    if res: final_widgets[0] = {**res, "source_title1": "LATEST", "source_title2": "AMATERI"}
    
    print("📦 Pakiram Polje 2: BEST")
    res = pop_unique_album(best_list, "BEST")
    if res: final_widgets[1] = {**res, "source_title1": "BEST", "source_title2": "AMATERI"}
    
    print("📦 Pakiram Polje 3: MOST COMMENTS")
    res = pop_unique_album(comments_list, "MOST COMMENTS")
    if res: final_widgets[2] = {**res, "source_title1": "MOST COMMENTS", "source_title2": "AMATERI"}
    
    print("📦 Pakiram Polje 4: RANDOM")
    res = pop_unique_album(random_list, "RANDOM")
    if res: final_widgets[3] = {**res, "source_title1": "RANDOM", "source_title2": "AMATERI"}
    
    print("📦 Pakiram Polje 5: LATEST NEXT")
    res = pop_unique_album(latest_next_list, "LATEST NEXT")
    if res: final_widgets[4] = {**res, "source_title1": "LATEST NEXT", "source_title2": "AMATERI"}
    
    print("📦 Pakiram Polje 6: BEST NEXT")
    res = pop_unique_album(best_next_list, "BEST NEXT")
    if res: final_widgets[5] = {**res, "source_title1": "BEST NEXT", "source_title2": "AMATERI"}

    news_items = [x for x in final_widgets if x is not None]

    with open('amateri_news.json', 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    print(f"\n✅ JSON uspješno spremljen! Ukupno stavki: {len(news_items)}/6")

if __name__ == "__main__":
    scrape_amateri()
