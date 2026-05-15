import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import os
import requests

async def fetch_page_data(url):
    data = {
        "title": "",
        "text_content": "",
        "images": []
    }
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
        )
        page = await context.new_page()
        
        try:
            # 타임아웃을 30초로 설정하고 대기
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 페이지 아래로 스크롤하여 지연 로딩되는 이미지 로드 유도 (간단한 스크롤)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목 추출 (og:title 우선)
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                data["title"] = og_title.get('content').strip()
            elif soup.title:
                data["title"] = soup.title.string.strip()
            
            # 텍스트 추출 (og:description 우선)
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                data["text_content"] = og_desc.get('content').strip() + " "
            
            # 불필요한 태그 제거
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = soup.get_text(separator=' ')
            text = re.sub(r'\s+', ' ', text).strip()
            data["text_content"] += text[:3000]
            
            # 이미지 추출
            images = []
            
            # og:image 우선 추가
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                images.append(og_image.get('content'))
                
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src and src.startswith('http'):
                    images.append(src)
            
            # 중복 제거 및 최대 10개로 제한
            data["images"] = list(dict.fromkeys(images))[:10]
            
        except Exception as e:
            print(f"Error fetching URL: {e}")
        finally:
            await browser.close()
            
    return data

def download_images(image_urls, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    saved_paths = []
    
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                ext = 'jpg'
                if '.png' in url.lower(): ext = 'png'
                elif '.webp' in url.lower(): ext = 'webp'
                
                filename = f"img_{i:03d}.{ext}"
                filepath = os.path.join(save_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                saved_paths.append(filepath)
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            
    return saved_paths

if __name__ == "__main__":
    # 테스트용
    url = "https://www.coupang.com/"
    data = asyncio.run(fetch_page_data(url))
    print(f"Title: {data['title']}")
    print(f"Images found: {len(data['images'])}")
