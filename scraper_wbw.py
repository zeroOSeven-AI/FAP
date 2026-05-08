import json
import cloudscraper
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup

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
    scraper = cloudscraper.create_scraper()
    
    try:
        print(f"🚀 Scraping WBW: {url}...")
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # WBW koristi 'a' tagove s klasom 'thumb-container' ili slike unutar 'grid-item'
        # Pokušat ćemo pronaći sve linkove koji vode na pojedinačne galerije/postove
        items = soup.find_all('a', href=True)
        
        news_items = []
        seen_links = set()

        for a in items:
            img = a.find('img')
            if not img: continue
            
            link = a['href']
            # Izbjegavamo duplikate i linkove koji nisu postovi
            if link in seen_links or not link.startswith('https://whatboyswant.com/post/'):
                continue
            
            # Izvlačenje slike - provjeravamo sve moguće izvore (lazy loading)
            image_url = img.get('data-src') or img.get('src') or img.get('data-lazy-src') or ""
            
            # Ako je URL slike relativan, popravi ga
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/') and not image_url.startswith('//'):
                image_url = 'https://whatboyswant.com' + image_url

            title = img.get('alt') or "WBW Content"
            
            if image_url and len(news_items) < 15:
                print(f"🔍 Provjera slike: {image_url[:50]}...")
                info = get_image_info(scraper, image_url)
                if info:
                    print(f"✅ Dodano: {title[:30]}")
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

        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✨ Gotovo! Spremljeno {len(news_items)} stavki.")

    except Exception as e:
        print(f"❌ Greška: {e}")

if __name__ == "__main__":
    scrape_wbw()
