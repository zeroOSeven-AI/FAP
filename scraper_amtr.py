import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta

# Dinamičko računanje datuma (zadnjih mjesec dana)
today = datetime.now()
one_month_ago = today - timedelta(days=30)

date_max = today.strftime('%Y-%m-%d')
date_min = one_month_ago.strftime('%Y-%m-%d')

# TOČNO TVOJA LISTA + DODANE DVIJE KATEGORIJE ZA ŽENSKE PAROVE (gender=5)
CATEGORIES = [
    {
        "name": "LATEST", 
        "url": f"https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&dateMin={date_min}&dateMax={date_max}&price=100-100000&trans=without"
    },
    {
        "name": "BEST", 
        "url": f"https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&dateMin={date_min}&dateMax={date_max}&price=100-100000&trans=without"
    },
    {
        "name": "MOST COMMENTS", 
        "url": f"https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&gender%5B0%5D=1&dateMin={date_min}&dateMax={date_max}&price=100-100000&trans=without"
    },
    {
        "name": "RANDOM", 
        "url": f"https://www.amateri.com/en/albums/?listingType=thumbListing&sort=rand&category%5B0%5D=2&gender%5B0%5D=1&dateMin={date_min}&dateMax={date_max}&price=100-100000&trans=without"
    },
    {
        "name": "GIRL PAIRS LATEST", 
        "url": f"https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=5&dateMin={date_min}&dateMax={date_max}&price=100-100000&trans=without"
    },
    {
        "name": "GIRL PAIRS BEST", 
        "url": f"https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=5&dateMin={date_min}&dateMax={date_max}&price=100-100000&trans=without"
    }
]

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
            
            return {
                "b64": f"data:image/jpeg;base64,{img_str}",
                "w": w,
                "h": h,
                "focus_y": focus_y
            }
    except Exception as e:
        print(f"Greška kod slike: {e}")
    return None

def scrape_amateri():
    scraper = cloudscraper.create_scraper()
    news_items = []
    used_links = set() # Sprečava da se isti album ponovi u više polja
    
    for cat in CATEGORIES:
        print(f"🚀 Obrađujem Amateri albume: {cat['name']}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = scraper.get(cat['url'], timeout=30, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            all_links = soup.find_all('a', href=True)
            album_items = []
            
            for link in all_links:
                href = link.get('href', '')
                if '/album/' in href and not any(x in href for x in ['/albums', 'upload', 'search']):
                    img = link.find('img')
                    if img:
                        album_items.append((link, img))

            if not album_items:
                for img in soup.find_all('img'):
                    parent_a = img.find_parent('a', href=True)
                    if parent_a and '/album/' in parent_a.get('href', ''):
                        album_items.append((parent_a, img))

            success = False
            for box_link, img in album_items:
                album_url = box_link.get('href')
                if album_url.startswith('/'): 
                    album_url = "https://www.amateri.com" + album_url
                
                # Ako je album već izvučen u nekoj od prošlih kategorija, preskoči ga
                if album_url in used_links:
                    continue
                
                raw_url = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
                if "logo" in raw_url.lower() or "avatar" in raw_url.lower() or not raw_url or "base64" in raw_url: 
                    continue
                
                image_url = raw_url
                info = get_image_info(scraper, image_url)
                
                if info:
                    used_links.add(album_url) # Označi album kao iskorišten
                    
                    news_items.append({
                        "source_title1": cat['name'].upper(),
                        "source_title2": "AMATERI",
                        "image_b64": info["b64"],
                        "w": info["w"],
                        "h": info["h"],
                        "focus_y": info["focus_y"],
                        "link": album_url
                    })
                    print(f"   ✅ Uspješno uhvaćen album: {album_url}")
                    success = True
                    break 
            
            if not success:
                print(f"   ⚠ Nije pronađen valjan album za kategoriju {cat['name']}.")
            
            time.sleep(2)
        except Exception as e:
            print(f"❌ Greška na {cat['name']}: {e}")

    # Osiguravamo da se datoteka uvijek zapiše kako GitHub Actions ne bi bacio grešku
    with open('amateri_news.json', 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    print(f"\n✅ JSON uspješno spremljen! Ukupno stavki: {len(news_items)}")

if __name__ == "__main__":
    scrape_amateri()
