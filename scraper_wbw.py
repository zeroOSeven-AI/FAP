import json
import re
import cloudscraper
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup

# ============================================
# 🎯 FOCUS LOGIKA
# ============================================
def get_focus_y(w, h):
    ratio = round(w / h, 2)
    if ratio >= 1.6: return 0.35
    if 0.9 <= ratio <= 1.1: return 0.25
    return 0.5

def get_image_info(scraper, url):
    if not url or not url.startswith('http'): return None
    try:
        # Koristimo cloudscraper i za slike
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
    # cloudscraper zaobilazi Cloudflare zaštitu
    scraper = cloudscraper.create_scraper()
    
    try:
        print(f"🚀 Scraping WBW: {url}...")
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Na WBW-u su artikli obično u .post-item ili .post-thumbnail klasama
        articles = soup.select('article, .post-item, .entry-content')
        
        news_items = []
        for art in articles:
            link_tag = art.find('a', href=True)
            img_tag = art.find('img')
            
            if not link_tag or not img_tag: continue

            # Često koriste data-src za lazy loading slika
            image_url = img_tag.get('data-src') or img_tag.get('src') or ""
            # Makni nepotrebne parametre iz URL-a slike ako postoje (npr. ?w=100)
            image_url = image_url.split('?')[0] 
            
            title = img_tag.get('alt') or art.get_text(strip=True) or "WBW Content"
            link = link_tag['href']
            if not link.startswith('http'):
                link = "https://whatboyswant.com" + link

            if image_url and len(news_items) < 15:
                info = get_image_info(scraper, image_url)
                if info:
                    print(f"✅ Dodano: {title[:30]}...")
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

        with open('wbw_news.json', 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=4)
        print(f"✨ Spremljeno {len(news_items)} stavki u wbw_news.json")

    except Exception as e:
        print(f"❌ Greška: {e}")

if __name__ == "__main__":
    scrape_wbw()
