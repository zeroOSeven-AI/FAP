import requests
from bs4 import BeautifulSoup
import json
import base64

# Popis kategorija i njihovih URL-ova (ovdje stavi stvarne linkove)
CATEGORIES = [
    {"name": "EDITORIAL", "url": "https://p-u-b-l-i-c-link.com/category/editorial"},
    {"name": "GLAMOUR", "url": "https://p-u-b-l-i-c-link.com/category/glamour"},
    {"name": "FITNESS", "url": "https://p-u-b-l-i-c-link.com/category/fitness"},
    {"name": "LIFESTYLE", "url": "https://p-u-b-l-i-c-link.com/category/lifestyle"},
    {"name": "PORTRAIT", "url": "https://p-u-b-l-i-c-link.com/category/portrait"},
    {"name": "ARTISTIC", "url": "https://p-u-b-l-i-c-link.com/category/artistic"}
]

def get_base64(url):
    try:
        return base64.b64encode(requests.get(url).content).decode('utf-8')
    except:
        return None

all_data = []

for cat in CATEGORIES:
    print(f"Scraping {cat['name']}...")
    try:
        response = requests.get(cat['url'], timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ovdje prilagodi selektore prema stranici koju koristiš
        article = soup.find('article') 
        if article:
            img_url = article.find('img')['src']
            link = article.find('a')['href']
            title = article.find('h2').text.strip() if article.find('h2') else "Selection"
            
            all_data.append({
                "source_title1": title[:15], # Ime ili kratki opis
                "source_title2": cat['name'], # KATEGORIJA koja ide u rozi bedž
                "image_b64": get_base64(img_url),
                "link": link
            })
    except Exception as e:
        print(f"Greška na {cat['name']}: {e}")

# Spremi u JSON
with open('wbw_news.json', 'w') as f:
    json.dump(all_data, f, indent=4)
