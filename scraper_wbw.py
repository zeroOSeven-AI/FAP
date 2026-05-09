import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

CATEGORIES = [
    {"name": "BIKINI", "url": "https://whatboyswant.com/babes/beach-bikini-babes"},
    {"name": "PARTY", "url": "https://whatboyswant.com/babes/party-babes"},
    {"name": "NON-NUDE", "url": "https://whatboyswant.com/babes/non-nude-babes"},
    {"name": "KISSING", "url": "https://whatboyswant.com/babes/kissing-babes"},
    {"name": "FIT GIRLS", "url": "https://whatboyswant.com/babes/fit-girls"},
    {"name": "COSPLAY", "url": "https://whatboyswant.com/babes/cosplay"}
]

def get_focus_y(w, h):
    """
    Logika za dinamički fokus:
    Što je slika "viša" (manji ratio), to fokus mora ići niže 
    kako bismo izbjegli samo prazan prostor iznad glave.
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
        elif url.startswith('/'): url = 'https://whatboyswant.com' + url
        
        headers = {"Referer": "https://whatboyswant.com/"}
        res = scraper.get(url, timeout=15, headers=headers)
        
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            w, h = img.size
            
            # Određujemo fokus prije smanjivanja
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

def scrape_multi_wbw():
    scraper = cloudscraper.create_scraper()
    news_items = []
    
    for cat in CATEGORIES:
        print(f"🚀 Obrađujem: {cat['name']}")
        try:
            response = scraper.get(cat['url'], timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tražimo slike (obično su u thumb-box klasi)
            items = soup.select('.thumb-box') or soup.find_all('a', href=True)
            
            for item in items:
                img = item.find('img')
                if not img: continue

                raw_url = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
                if "logo" in raw_url.lower() or not raw_url or "base64" in raw_url: continue
                
                # Uzimamo normalnu rezoluciju
                image_url = raw_url.replace('-th.', '-norm.')
                
                info = get_image_info(scraper, image_url)
                
                if info:
                    link = item.get('href') or item.find_parent('a').get('href', '#')
                    if link.startswith('/'): link = "https://whatboyswant.com" + link
                    
                    # NOVI PRISTUP NAZIVIMA PREMA TVOM ZAHTJEVU
                    news_items.append({
                        "source_title1": "Babes",
                        "source_title2": cat['name'].upper(),
                        "image_b64": info["b64"],
                        "w": info["w"],
                        "h": info["h"],
                        "focus_y": info["focus_y"],
                        "link": link
                    })
                    break # Uzmi samo prvu najnoviju sliku
            
            time.sleep(1)
        except Exception as e:
            print(f"❌ Greška na {cat['name']}: {e}")

    if news_items:
        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✅ JSON spreman s novim fokusima i nazivima!")

if __name__ == "__main__":
    scrape_multi_wbw()
