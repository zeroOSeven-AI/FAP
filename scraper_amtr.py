import json
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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

def get_image_info(page, url):
    if not url: return None
    try:
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https://www.amateri.com' + url
        
        response = page.request.get(url, headers={"Referer": "https://www.amateri.com/"}, timeout=15000)
        if response.status == 200:
            img_bytes = response.body()
            img = Image.open(BytesIO(img_bytes))
            w, h = img.size
            focus_y = get_focus_y(w, h)
            img.thumbnail((600, 600)) 
            buffered = BytesIO()
            img.convert('RGB').save(buffered, format="JPEG", quality=75)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"b64": f"data:image/jpeg;base64,{img_str}", "w": w, "h": h, "focus_y": focus_y}
    except Exception as e:
        print(f"   ⚠ Greška pri obradi slike: {e}")
    return None

def fetch_albums_from_page(page, url):
    try:
        print(f"🌐 Otvaram URL: {url[:60]}...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
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
        
        print(f"   📥 Pronađeno albuma: {len(album_items)}")
        return album_items
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju URL-a: {e}")
        return []

def scrape_amateri():
    final_widgets = [None] * 6 
    used_links = set()
    
    print("⏳ Pokrećem browser i skupljam albume...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        latest_list = fetch_albums_from_page(page, URLS["LATEST"])
        best_list = fetch_albums_from_page(page, URLS["BEST"])
        comments_list = fetch_albums_from_page(page, URLS["MOST_COMMENTS"])
        random_list = fetch_albums_from_page(page, URLS["RANDOM"])
        
        def pop_unique_album(album_list, debug_name):
            for item in album_list:
                if item["link"] not in used_links:
                    print(f"   🔎 [{debug_name}] Pokušavam uzeti: {item['link']}")
                    info = get_image_info(page, item["img_url"])
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

        res = pop_unique_album(latest_list, "LATEST 1")
        if res: final_widgets[0] = {**res, "source_title1": "LATEST 1", "source_title2": "AMATERI"}
        
        res = pop_unique_album(latest_list, "LATEST 2")
        if res: final_widgets[1] = {**res, "source_title1": "LATEST 2", "source_title2": "AMATERI"}
        
        res = pop_unique_album(latest_list, "LATEST 3")
        if res: final_widgets[2] = {**res, "source_title1": "LATEST 3", "source_title2": "AMATERI"}
        
        res = pop_unique_album(best_list, "BEST")
        if res: final_widgets[3] = {**res, "source_title1": "BEST", "source_title2": "AMATERI"}
        
        res = pop_unique_album(comments_list, "MOST COMMENTS")
        if res: final_widgets[4] = {**res, "source_title1": "MOST COMMENTS", "source_title2": "AMATERI"}
        
        res = pop_unique_album(random_list, "RANDOM")
        if res: final_widgets[5] = {**res, "source_title1": "RANDOM", "source_title2": "AMATERI"}

        browser.close()

    news_items = [x for x in final_widgets if x is not None]

    with open('amateri_news.json', 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    print(f"\n✅ JSON uspješno spremljen! Ukupno stavki: {len(news_items)}/6")

if __name__ == "__main__":
    scrape_amateri()
