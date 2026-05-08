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
    # Forsiramo browser identitet
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        print(f"🚀 Scraping WBW: {url}")
        response = scraper.get(url, timeout=30)
        
        # Debug: Ispisujemo dio HTML-a u logove da vidimo što GitHub vidi
        print(f"📡 Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # WBW često drži slike u 'article' tagovima ili 'div' s klasom 'thumb'
        # Tražimo sve linkove, pa ćemo filtrirati one koji imaju slike unutra
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} links total. Filtering...")

        news_items = []
        seen_links = set()

        for a in links:
            img = a.find('img')
            link = a['href']
            
            # Ako link nije potpun, spoji ga
            if link.startswith('/'):
                link = "https://whatboyswant.com" + link

            # Filtriramo samo postove/galerije
            if "/post/" not in link or link in seen_links:
                continue
            
            if img:
                # Izvlačenje slike - redoslijed po važnosti
                image_url = (img.get('data-src') or 
                             img.get('data-lazy-src') or 
                             img.get('src') or 
                             "")
                
                if not image_url or "base64" in image_url: 
                    continue

                if image_url.startswith('//'): image_url = 'https:' + image_url
                elif image_url.startswith('/'): image_url = 'https://whatboyswant.com' + image_url

                title = img.get('alt') or "WBW Content"
                
                if len(news_items) < 15:
                    print(f"🔍 Obrada: {title[:20]} | Image: {image_url[:40]}")
                    info = get_image_info(scraper, image_url)
                    if info:
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
                        seen_links.add(link)
                        # Mala pauza da ne budemo preagresivni
                        time.sleep(0.5)

        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        
        print(f"✨ Završeno! Prikupljeno: {len(news_items)}")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    scrape_wbw()
