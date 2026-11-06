import json
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# URL-ovi za 4 glavne kategorije
URLS = {
    "LATEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=time&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "BEST": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=standard&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "MOST_COMMENTS": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=comments&category%5B0%5D=2&gender%5B0%5D=1&trans=without",
    "RANDOM": "https://www.amateri.com/en/albums/?listingType=thumbListing&sort=rand&category%5B0%5D=2&gender%5B0%5D=1&trans=without"
}

def get_focus_y(w, h):
    ratio = w / h
    if ratio < 0.8: return 0.30
    elif ratio < 1.0: return 0.38
    elif ratio < 1.3: return 0.45
    else: return 0.50

def get_image_info(page, url):
    if not url: return None
    try:
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https://www.amateri.com' + url
        
        # Preuzimamo sliku direktno kroz već otvorenu Playwright stranicu (dijeli sjednicu i kolačiće)
        response = page.request.get(url, headers={"Referer": "https://www.amateri.com/"}, timeout=15000)
        if response.status == 200:
            img_bytes = response.body()
            img = Image.open(BytesIO(img_bytes))
            w, h = img.size
            focus_y = get_focus_y(w, h)
            img.thumbnail((600, 600)) 
            buffered = BytesIO()
            img.convert('RGB').save(buffered, format="JPEG", quality=75)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"b64": f"data:image/jpeg;base64,{img_str}", "w": w, "h": h, "focus_y": focus_y}
    except Exception as e:
        print(f"   ⚠ Greška pri obradi slike: {e}")
    return None

def fetch_albums_from_page(page, url):
    try:
        print(f"🌐 Otvaram URL: {url[:60]}...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Pauza za Cloudflare provjeru ako se pojavi
        page.wait_for_timeout(4000)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        album_items = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/album/' in href and not any(x in href for x in ['/albums', 'upload', 'search']):
                img = link.find('img')
                if img:
                    album_url = "https://www.amateri.com" + href if href.startswith('/') else href
                    raw_img
