import json
import cloudscraper
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup

def get_base64_image(scraper, url):
    try:
        # Šaljemo headere i ovdje da budemo sigurni
        headers = {"Referer": "https://whatboyswant.com/"}
        res = scraper.get(url, timeout=15, headers=headers)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content))
            
            # Smanjujemo na razumnu veličinu za widget, ali čuvamo kvalitetu
            img.thumbnail((1000, 1000)) 
            buffered = BytesIO()
            # Povećana kvaliteta na 85 (manja kompresija)
            img.convert('RGB').save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"Greška kod kodiranja slike: {e}")
        return None

def scrape_wbw():
    url = "https://whatboyswant.com/babes/bottomless-babes"
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tražimo sve kontejnere koji sadrže slike
        items = soup.find_all('div', class_='thumb-box') or soup.find_all('a', href=True)
        news_items = []
        seen_images = set()

        for item in items:
            img = item.find('img')
            if not img or len(news_items) >= 8: continue

            # KLJUČ: Tražimo pravu sliku u različitim atributima (data-src je obično prava)
            raw_url = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ""
            
            # Ako je premala slika ili logo, preskačemo
            if "logo" in raw_url.lower() or not raw_url: continue
            
            # Forsiramo 'norm' verziju (visoka rezolucija)
            image_url = raw_url.replace('-th.', '-norm.')
            if image_url.startswith('//'): image_url = 'https:' + image_url
            elif image_url.startswith('/'): image_url = 'https://whatboyswant.com' + image_url

            if image_url in seen_images: continue

            print(f"📸 Obrađujem: {image_url}")
            b64_data = get_base64_image(scraper, image_url)
            
            if b64_data:
                link = item.get('href') or item.find_parent('a')['href']
                if link.startswith('/'): link = "https://whatboyswant.com" + link
                
                news_items.append({
                    "title": (img.get('alt') or "Babe").strip(),
                    "link": link,
                    "image_b64": b64_data,
                    "source_title1": "WBW",
                    "source_title2": "BOTTOMLESS",
                    "source_color": "#e91e63",
                    "flag": "🔞"
                })
                seen_images.add(image_url)

        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print("✅ Gotovo!")

    except Exception as e:
        print(f"❌ Greška: {e}")

if __name__ == "__main__":
    scrape_wbw()
