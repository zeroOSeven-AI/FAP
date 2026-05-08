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

def get_base64_image(scraper, url):
    if not url: return None
    try:
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https://whatboyswant.com' + url
        
        headers = {"Referer": "https://whatboyswant.com/"}
        res = scraper.get(url, timeout=15, headers=headers)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            img.thumbnail((800, 800)) 
            buffered = BytesIO()
            img.convert('RGB').save(buffered, format="JPEG", quality=75)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"Greška kod kodiranja slike: {e}")
        return None
    return None

def scrape_multi_wbw():
    # Koristimo CLOUDSCRAPER da prođemo zaštitu
    scraper = cloudscraper.create_scraper()
    news_items = []
    
    for cat in CATEGORIES:
        print(f"🚀 Obrađujem kategoriju: {cat['name']}")
        try:
            response = scraper.get(cat['url'], timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Koristimo tvoju dobitnu formulu za traženje elemenata
            items = soup.find_all('div', class_='thumb-box') or soup.find_all('a', href=True)
            
            found_in_cat = False
            for item in items:
                img = item.find('img')
                if not img: continue

                # Uzimamo pravu sliku (data-src je ključan)
                raw_url = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
                if "logo" in raw_url.lower() or not raw_url or "base64" in raw_url: continue
                
                # Forsiramo kvalitetniju verziju
                image_url = raw_url.replace('-th.', '-norm.')
                
                print(f"📸 Skidam sliku iz {cat['name']}...")
                b64_data = get_base64_image(scraper, image_url)
                
                if b64_data:
                    link = item.get('href') or item.find_parent('a').get('href', '#')
                    if link.startswith('/'): link = "https://whatboyswant.com" + link
                    
                    # Čistimo naslov
                    raw_title = (img.get('alt') or "Babe").strip()
                    clean_title = raw_title.split('|')[0].strip()[:15].upper()

                    news_items.append({
                        "source_title1": clean_title,
                        "source_title2": cat['name'],
                        "image_b64": b64_data,
                        "link": link
                    })
                    found_in_cat = True
                    break # Uzimamo samo PRVU (najnoviju) sliku iz svake kategorije
            
            if not found_in_cat:
                print(f"⚠️ Nije pronađena slika u kategoriji: {cat['name']}")
            
            time.sleep(1) # Kratka pauza

        except Exception as e:
            print(f"❌ Greška na {cat['name']}: {e}")

    # Spremanje rezultata
    if news_items:
        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✅ Gotovo! Prikupljeno {len(news_items)} kategorija.")
    else:
        print("💀 JSON je i dalje prazan. Provjeri jesu li linkovi ispravni.")

if __name__ == "__main__":
    scrape_multi_wbw()
