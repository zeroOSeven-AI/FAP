import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

# Tvoj popis kategorija
CATEGORIES = [
    {"name": "BIKINI", "url": "https://whatboyswant.com/babes/beach-bikini-babes"},
    {"name": "PARTY", "url": "https://whatboyswant.com/babes/party-babes"},
    {"name": "NON-NUDE", "url": "https://whatboyswant.com/babes/non-nude-babes"},
    {"name": "KISSING", "url": "https://whatboyswant.com/babes/kissing-babes"},
    {"name": "FIT GIRLS", "url": "https://whatboyswant.com/babes/fit-girls"},
    {"name": "COSPLAY", "url": "https://whatboyswant.com/babes/cosplay"}
]

# ============================================
# 🎯 FOCUS LOGIKA (Samo izračun, bez rezanja)
# ============================================
def get_focus_y(w, h):
    ratio = round(w / h, 2)
    # Ako je slika uspravna (portrait), spusti fokus niže (0.40 - 0.45)
    if ratio < 1.0:
        return 0.40
    # Ako je kvadratna
    if 1.0 <= ratio <= 1.2:
        return 0.35
    # Ako je široka (landscape)
    return 0.50

def get_image_data(scraper, url):
    if not url: return None
    try:
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https://whatboyswant.com' + url
        
        headers = {"Referer": "https://whatboyswant.com/"}
        res = scraper.get(url, timeout=15, headers=headers)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            w, h = img.size
            
            # Izračunaj fokus na temelju originalnih dimenzija
            focus_y = get_focus_y(w, h)
            
            # Smanji samo težinu datoteke za widget
            img.thumbnail((800, 800)) 
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
    return None

def scrape_multi_wbw():
    scraper = cloudscraper.create_scraper()
    news_items = []
    
    for cat in CATEGORIES:
        print(f"🚀 Obrađujem kategoriju: {cat['name']}")
        try:
            response = scraper.get(cat['url'], timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = soup.find_all('div', class_='thumb-box') or soup.find_all('a', href=True)
            
            for item in items:
                img = item.find('img')
                if not img: continue

                raw_url = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
                if "logo" in raw_url.lower() or not raw_url or "base64" in raw_url: continue
                
                image_url = raw_url.replace('-th.', '-norm.')
                
                print(f"📸 Analiziram sliku za {cat['name']}...")
                img_data = get_image_data(scraper, image_url)
                
                if img_data:
                    link = item.get('href') or item.find_parent('a').get('href', '#')
                    if link.startswith('/'): link = "https://whatboyswant.com" + link
                    
                    raw_title = (img.get('alt') or "Babe").strip()
                    clean_title = raw_title.split('|')[0].strip()[:15].upper()

                    news_items.append({
                        "source_title1": clean_title,
                        "source_title2": cat['name'],
                        "image_b64": img_data["b64"],
                        "w": img_data["w"],
                        "h": img_data["h"],
                        "focus_y": img_data["focus_y"], # Ovo ide u JSON
                        "link": link
                    })
                    break 
            
            time.sleep(1)

        except Exception as e:
            print(f"❌ Greška na {cat['name']}: {e}")

    if news_items:
        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✅ Gotovo! JSON sadrži focus_y za svaku sliku.")

if __name__ == "__main__":
    scrape_multi_wbw()
