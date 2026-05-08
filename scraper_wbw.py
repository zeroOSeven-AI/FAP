import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup

def get_base64_image(scraper, url):
    try:
        res = scraper.get(url, timeout=10)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            # Smanjujemo sliku da JSON ne bude ogroman (max 800px širina)
            img.thumbnail((800, 800))
            buffered = BytesIO()
            img.convert('RGB').save(buffered, format="JPEG", quality=70)
            # Pretvaranje u Base64 string
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except:
        return None
    return None

def scrape_wbw():
    url = "https://whatboyswant.com/babes/bottomless-babes"
    scraper = cloudscraper.create_scraper()
    
    try:
        print(f"🚀 Scraping WBW (Base64 mode): {url}")
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        news_items = []
        seen_images = set()

        for a in links:
            img = a.find('img')
            if not img or len(news_items) >= 10: continue # Limitiramo na 10 zbog veličine JSON-a

            link = a['href']
            if link.startswith('/'): link = "https://whatboyswant.com" + link

            # Uzimamo 'norm' verziju slike
            raw_url = (img.get('data-src') or img.get('src') or "").replace('-th.', '-norm.')
            if not raw_url or "base64" in raw_url: continue
            if raw_url.startswith('//'): raw_url = 'https:' + raw_url
            elif raw_url.startswith('/'): raw_url = 'https://whatboyswant.com' + raw_url

            if raw_url in seen_images: continue

            print(f"📥 Kodiram sliku: {raw_url[:40]}...")
            b64_data = get_base64_image(scraper, raw_url)
            
            if b64_data:
                news_items.append({
                    "title": (img.get('alt') or "Babe Picture").strip(),
                    "link": link,
                    "image_b64": b64_data,
                    "source_title1": "WBW",
                    "source_title2": "BOTTOMLESS",
                    "source_color": "#e91e63",
                    "flag": "🔞"
                })
                seen_images.add(raw_url)

        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✅ JSON spreman sa {len(news_items)} zakodiranih slika.")

    except Exception as e:
        print(f"❌ Greška: {e}")

if __name__ == "__main__":
    scrape_wbw()
