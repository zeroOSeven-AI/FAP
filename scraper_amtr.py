import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

# Standardizirani endpointi prema tvom zahtjevu
CATEGORIES = [
    {"name": "LATEST", "url": "https://www.amateri.com/en/albums/?sort=time&category%5B0%5D=2&trans=include"},
    {"name": "BEST", "url": "https://www.amateri.com/en/albums/?sort=standard&category%5B0%5D=2&trans=include"},
    {"name": "MOST COMMENTS", "url": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&trans=include"},
    {"name": "RANDOM", "url": "https://www.amateri.com/en/albums/?listingType=thumbListing&category%5B0%5D=2&sort=rand&trans=include"}
]

def get_focus_y(w, h):
    """
    Logika za dinamički fokus:
    Što je slika "viša" (manji ratio), to fokus mora ići niže.
    """
    ratio = w / h
    if ratio < 0.8:    # Jako uska i visoka slika
        return 0.30
    elif ratio < 1.0:  # Portret
        return 0.38
    elif ratio < 1.3:  # Kvadratasta
        return 0.45
    else:              # Široka slika
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
            
            # Smanjujemo sliku za widget (da JSON ne bude pretežak)
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
    # Cloudscraper je nužan jer Amateri često koriste Cloudflare zaštitu
    scraper = cloudscraper.create_scraper()
    news_items = []
    
    for cat in CATEGORIES:
        print(f"🚀 Obrađujem: {cat['name']}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = scraper.get(cat['url'], timeout=30, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Fleksibilni selektori za albume/sličice na amateri.com
            items = soup.select('.album-item, .thumb-box, .album, .picture-box')
            
            # Fallback ako specifične klase ne vrate ništa
            if not items:
                items = [a for a in soup.find_all('a', href=True) if a.find('img')]
            
            for item in items:
                img = item.find('img') if hasattr(item, 'find') else None
                if not img: continue

                # Hvatanje URL-a slike (lazy load zaštita)
                raw_url = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
                if "logo" in raw_url.lower() or not raw_url or "base64" in raw_url: continue
                
                # Ovdje smo maknuli .replace('-th.', '-norm.') jer Amateri imaju drugačiju strukturu URL-ova.
                # Ako primijetiš da dohvaća premale sličice, ovdje ćemo ubaciti zamjenu (npr. /thumbs/ u /images/).
                image_url = raw_url
                
                info = get_image_info(scraper, image_url)
                
                if info:
                    link = item.get('href') or item.find_parent('a').get('href', '#')
                    if link.startswith('/'): link = "https://www.amateri.com" + link
                    
                    news_items.append({
                        "source_title1": cat['name'].upper(),
                        "source_title2": "AMATERI",
                        "image_b64": info["b64"],
                        "w": info["w"],
                        "h": info["h"],
                        "focus_y": info["focus_y"],
                        "link": link
                    })
                    break # Uzmi samo prvu najnoviju sliku iz ove kategorije kao i prije
            
            time.sleep(1.5) # Malo veći delay zbog Cloudflare-a
        except Exception as e:
            print(f"❌ Greška na {cat['name']}: {e}")

    if news_items:
        with open('amateri_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✅ JSON spreman s novim podacima sa stranice Amateri!")

if __name__ == "__main__":
    scrape_amateri()
