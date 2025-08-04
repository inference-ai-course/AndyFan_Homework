import requests, os
from bs4 import BeautifulSoup
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def get_latest_arxiv_ids(category='cs.CL', max_results=10):
    url = f"https://arxiv.org/list/{category}/new"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    id_tags = soup.find_all('a', title='Abstract')
    arxiv_ids = [tag.text.replace('arXiv:', '').strip() for tag in id_tags[:max_results]]
    return arxiv_ids


def download_pdf(arxiv_id, out_dir='pdfs'):
    url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f'{arxiv_id}.pdf')
    if not os.path.exists(pdf_path):
        r = requests.get(url)
        with open(pdf_path, 'wb') as f:
            f.write(r.content)
    return pdf_path

def pdf_to_images(pdf_path, out_dir='images'):
    import os
    from pdf2image import convert_from_path

    os.makedirs(out_dir, exist_ok=True) 
    poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
    images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    image_paths = []
    for idx, img in enumerate(images):
        image_path = os.path.join(out_dir, f"{os.path.basename(pdf_path).replace('.pdf','')}_page{idx+1}.png")
        img.save(image_path, 'PNG')
        image_paths.append(image_path)
    return image_paths

def ocr_image(image_path):
    custom_oem_psm_config = r'--oem 3 --psm 1'
    text = pytesseract.image_to_string(Image.open(image_path), config=custom_oem_psm_config)
    return text

def images_to_txt(image_paths, out_txt):
    with open(out_txt, 'w', encoding='utf-8') as f:
        for i, img in enumerate(image_paths):
            f.write(f"\n\n---- Page {i+1} ----\n")
            text = ocr_image(img)
            f.write(text)

def batch_pdf_to_txt(arxiv_ids, pdf_dir='pdfs', txt_dir='pdf_ocr'):
    os.makedirs(txt_dir, exist_ok=True)
    for arxiv_id in arxiv_ids:
        pdf_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
        images = pdf_to_images(pdf_path, out_dir=f'images/{arxiv_id}')
        out_txt = os.path.join(txt_dir, f"{arxiv_id}.txt")
        images_to_txt(images, out_txt)
        print(f"OCR done: {out_txt}")

# 主流程
arxiv_ids = get_latest_arxiv_ids('cs.CL', 5)
[download_pdf(i) for i in arxiv_ids]
batch_pdf_to_txt(arxiv_ids)
