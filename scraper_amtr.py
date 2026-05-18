import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

# Samo jedan, najpouzdaniji URL - Najnoviji albumi (LATEST)
URL_LATEST = "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without"

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

def scrape_amateri():
    scraper = cloudscraper.create_scraper()
    news_items = []
    used_links = set()
    
    print("⏳ Dohvaćam najnovije albume s Amatera...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = scraper.get(URL_LATEST, timeout=30, headers=headers)
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
        
        print(f"   Proneđeno ukupno {len(album_items)} albuma na stranici. Uzimam prvih 6 ispravnih...")
        
        # Prolazimo kroz sakupljene albume redom i punimo točno 6 mjesta
        for item in album_items:
            if len(news_items) >= 6:
                break  # Imamo punu mrežu, stani ovdje
                
            if item["link"] not in used_links:
                print(f"   🔎 Obrada albuma {len(news_items) + 1}/6: {item['link']}")
                info = get_image_info(scraper, item["img_url"])
                
                if info:
                    used_links.add(item["link"])
                    # Tag će dinamički ispisivati LATEST 1, LATEST 2, LATEST 3...
                    tag_name = f"LATEST {len(news_items) + 1}"
                    
                    news_items.append({
                        "source_title1": tag_name,
                        "source_title2": "AMATERI",
                        "image_b64": info["b64"],
                        "w": info["w"],
                        "h": info["h"],
                        "focus_y": info["focus_y"],
                        "link": item["link"]
                    })
                    print(f"   ✅ Spremljeno u polje {len(news_items)}")
                else:
                    print("   ⚠ Slika ne valja, idem na idući album...")
                    
    except Exception as e:
        print(f"❌ Greška na stranici: {e}")

    # Zapisivanje u JSON datoteku
    with open('amateri_news.json', 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    print(f"\n✅ JSON uspješno spremljen! Ukupno stavki: {len(news_items)}/6")

if __name__ == "__main__":
    scrape_amateri()
