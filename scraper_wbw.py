import requests
from bs4 import BeautifulSoup
import json
import base64
import time

CATEGORIES = [
    {"name": "BIKINI", "url": "https://whatboyswant.com/babes/beach-bikini-babes"},
    {"name": "PARTY", "url": "https://whatboyswant.com/babes/party-babes"},
    {"name": "NON-NUDE", "url": "https://whatboyswant.com/babes/non-nude-babes"},
    {"name": "KISSING", "url": "https://whatboyswant.com/babes/kissing-babes"},
    {"name": "FIT GIRLS", "url": "https://whatboyswant.com/babes/fit-girls"},
    {"name": "COSPLAY", "url": "https://whatboyswant.com/babes/cosplay"}
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
}

def get_base64(url):
    if not url: return None
    try:
        # Ako je URL slike relativan, dodaj domenu
        if url.startswith('//'): url = "https:" + url
        elif not url.startswith('http'): url = "https://whatboyswant.com" + url
            
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return base64.b64encode(res.content).decode('utf-8')
    except:
        return None
    return None

all_data = []

for cat in CATEGORIES:
    print(f"Hvatam kategoriju: {cat['name']}...")
    try:
        response = requests.get(cat['url'], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # WBW specifična klasa za objavu je obično 'video-block' ili 'post'
        post = soup.find('div', class_='video-block') or soup.find('div', class_='post')
        
        if post:
            link_tag = post.find('a')
            img_tag = post.find('img')
            title_tag = post.find('div', class_='post-title') or post.find('span')
            
            if link_tag and img_tag:
                # 1. Link do objave
                link = link_tag['href']
                if not link.startswith('http'):
                    link = "https://whatboyswant.com" + link
                
                # 2. URL slike (gledamo src, data-src ili alt)
                img_url = img_tag.get('data-src') or img_tag.get('src')
                
                # 3. Naslov/Ime
                name = "SELECTION"
                if title_tag:
                    name = title_tag.get_text(strip=True)
                elif img_tag.get('alt'):
                    name = img_tag.get('alt').split('|')[0].strip()

                all_data.append({
                    "source_title1": name[:12].upper(),
                    "source_title2": cat['name'],
                    "image_b64": get_base64(img_url),
                    "link": link
                })
                print(f"✅ Uspješno skupljeno: {cat['name']}")
        else:
            print(f"❌ Nisam našao post za: {cat['name']}")
        
        time.sleep(1.5) # Malo duža pauza da budemo sigurni
        
    except Exception as e:
        print(f"Greška na {cat['name']}: {e}")

# Provjera prije spremanja
if all_data:
    with open('wbw_news.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)
    print(f"Gotovo! JSON spremljen sa {len(all_data)} stavki.")
else:
    print("Kritična greška: Nijedna kategorija nije skupljena!")
