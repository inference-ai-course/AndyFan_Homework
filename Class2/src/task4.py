import requests, json, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import pytesseract
import trafilatura
from io import BytesIO

# 设置 tesseract 路径（Windows 下）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



def fetch_paper_links():
    url = "https://arxiv.org/list/cs.CL/pastweek?show=250"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for dt in soup.find_all("dt"):
        id_link = dt.find("a", title="Abstract")
        if id_link:
            abs_url = "https://arxiv.org" + id_link["href"]
            links.append(abs_url)
    return links[:10]

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=800,900")
    chrome_options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def screenshot_abstract(driver, url):
    driver.get(url)
    # 等待页面加载
    time.sleep(1.2)
    # 定位摘要区域
    abs_elem = driver.find_element("css selector", "blockquote.abstract")
    abs_png = abs_elem.screenshot_as_png
    return Image.open(BytesIO(abs_png))


def clean_abs_page(url):
    resp = requests.get(url)
    # 用 trafilatura 提取全文（有时结构化更方便还是用 bs4）
    extracted = trafilatura.extract(resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("h1", class_="title").text.replace("Title:", "").strip()
    authors = soup.find("div", class_="authors").text.replace("Authors:", "").strip()
    date = soup.find("div", class_="dateline").text.strip()
    abstract = soup.find("blockquote", class_="abstract").text.replace("Abstract:","").strip()
    return title, authors, date, abstract


def ocr_image(image):
    text = pytesseract.image_to_string(image)
    return text.strip()

def main():
    links = fetch_paper_links()
    print(f"Total papers: {len(links)}")
    driver = get_driver()
    records = []
    for idx, url in enumerate(links):
        print(f"Processing {idx+1}/{len(links)}: {url}")
        title, authors, date, abstract = clean_abs_page(url)
        img = screenshot_abstract(driver, url)
        ocr_abs = ocr_image(img)
        record = {
            "url": url,
            "title": title,
            "authors": authors,
            "date": date,
            "abstract": abstract,
            "ocr_abstract": ocr_abs
        }
        records.append(record)
        # 避免被 arxiv 封锁，适当 sleep
        if len(records) >= 10: break
    # 保存为 json
    with open("arxiv_clean.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    driver.quit()

if __name__ == "__main__":
    main()
