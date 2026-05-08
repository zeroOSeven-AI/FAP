import requests
from bs4 import BeautifulSoup
import json
import base64
import time

# Tvoj popis kategorija s linkovima
CATEGORIES = [
    {"name": "BIKINI", "url": "https://whatboyswant.com/babes/beach-bikini-babes"},
    {"name": "PARTY", "url": "https://whatboyswant.com/babes/party-babes"},
    {"name": "NON-NUDE", "url": "https://whatboyswant.com/babes/non-nude-babes"},
    {"name": "KISSING", "url": "https://whatboyswant.com/babes/kissing-babes"},
    {"name": "FIT GIRLS", "url": "https://whatboyswant.com/babes/fit-girls"},
    {"name": "COSPLAY", "url": "https://whatboyswant.com/babes/cosplay"}
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_base64(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        return base64.b64encode(res.content).decode('utf-8')
    except:
        return None

all_data = []

for cat in CATEGORIES:
    print(f"Hvatam kategoriju: {cat['name']}...")
    try:
        response = requests.get(cat['url'], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pronalazimo prvu (najnoviju) objavu u toj kategoriji
        # Na WBW su objave obično unutar div-a s klasom 'post-box' ili slično
        post = soup.select_one('.post-box, article, .item') 
        
        if post:
            link_tag = post.find('a')
            img_tag = post.find('img')
            
            if link_tag and img_tag:
                link = link_tag['href']
                if not link.startswith('http'):
                    link = "https://whatboyswant.com" + link
                
                img_url = img_tag.get('src') or img_tag.get('data-src')
                
                # Čišćenje naslova (uzimamo alt tekst slike ili naslov objave)
                title = img_tag.get('alt', 'Selection').split('|')[0].strip()
                
                all_data.append({
                    "source_title1": title[:12].upper(), # Ime cure
                    "source_title2": cat['name'],        # KATEGORIJA za rozi bedž
                    "image_b64": get_base64(img_url),
                    "link": link
                })
        
        # Mala pauza da nas ne blokiraju
        time.sleep(1)
        
    except Exception as e:
        print(f"Greška na {cat['name']}: {e}")

# Spremanje u tvoj glavni JSON file
with open('wbw_news.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print("Gotovo! JSON je spreman.")
