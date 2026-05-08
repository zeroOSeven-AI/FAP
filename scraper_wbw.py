import json
import cloudscraper
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time

def get_focus_y(w, h):
    ratio = round(w / h, 2)
    if ratio >= 1.6: return 0.35
    if 0.9 <= ratio <= 1.1: return 0.25
    return 0.5

def get_image_info(scraper, url):
    if not url or not url.startswith('http'): return None
    try:
        res = scraper.get(url, timeout=10)
        img = Image.open(BytesIO(res.content))
        w, h = img.size
        return {
            "url": url,
            "w": w,
            "h": h,
            "focus_y": get_focus_y(w, h)
        }
    except:
        return None

def scrape_wbw():
    url = "https://whatboyswant.com/babes/bottomless-babes"
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        print(f"🚀 Scraping WBW: {url}")
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        print(f"📡 Ukupno linkova: {len(all_links)}")

        news_items = []
        seen_images = set()

        for a in all_links:
            img = a.find('img')
            if not img: continue

            link = a['href']
            if link.startswith('/'): link = "https://whatboyswant.com" + link

            # Izvlačenje slike
            raw_img_url = (img.get('data-src') or img.get('data-lazy-src') or img.get('src') or "")
            if not raw_img_url or "base64" in raw_img_url: continue

            # --- TRIK ZA FULL SLIKU ---
            # Ako slika završava na -th.jpg, pokušavamo dobiti original
            image_url = raw_img_url.replace('-th.', '.') # Skida thumbnail sufiks
            if image_url.startswith('//'): image_url = 'https:' + image_url
            elif image_url.startswith('/'): image_url = 'https://whatboyswant.com' + image_url

            if image_url in seen_images: continue

            title = img.get('alt') or "Babe Picture"
            
            if len(news_items) < 15:
                # Filtriramo linkove koji vode na galerije (obično imaju broj na kraju)
                if any(char.isdigit() for char in link):
                    print(f"🔍 Provjera: {title[:20]}... | Full Image: {image_url[-30:]}")
                    
                    info = get_image_info(scraper, image_url)
                    # Ako "očišćena" slika ne radi, probaj originalnu
                    if not info:
                        info = get_image_info(scraper, raw_img_url)

                    if info and info['w'] > 150:
                        news_items.append({
                            "title": title.strip(),
                            "link": link,
                            "image_url": info["url"],
                            "w": info["w"],
                            "h": info["h"],
                            "focus_y": info["focus_y"],
                            "source_title1": "WBW",
                            "source_title2": "BOTTOMLESS",
                            "source_color": "#e91e63",
                            "flag": "🔞"
                        })
                        seen_images.add(image_url)
                        time.sleep(0.2)

        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        
        print(f"✨ USPJEH! Prikupljeno: {len(news_items)} stavki.")

    except Exception as e:
        print(f"❌ Greška: {e}")

if __name__ == "__main__":
    scrape_wbw()
