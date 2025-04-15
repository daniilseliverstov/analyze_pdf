import json

import requests
import pytesseract
from PIL import Image
import io
import fitz
import numpy as np
import cv2


def is_scan(page):
    text = page.get_text()
    if len(text.strip()) > 50:
        return False

    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))

    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    black_pixels = np.sum(threshold == 0)
    total_pixels = threshold.size
    black_ratio = black_pixels / total_pixels

    return black_ratio > 0.01


def process_scan_with_mistral(image_bytes):
    api_key = "HolLl3QLtJscvjJDrCPo96wvHifYrfwK"
    url = "https://api.mistral.ai/v1/ocr"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "image/png"
    }

    response = requests.post(url, headers=headers, data=image_bytes)
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print(f"Ошибка OCR: {response.status_code} - {response.text}")
        return ""


def analyze_certificate(text):
    certificate_data = {}

    if "сертификат качества" in text.lower() or "certificate of quality" in text.lower():
        certificate_data["type"] = "quality_certificate"

    if "стандарт" in text.lower():
        certificate_data["standard"] = True

    if "соответствие" in text.lower():
        certificate_data["compliance"] = True

    return certificate_data if certificate_data else None


def process_pdf(file_path):
    doc = fitz.open(file_path)
    results = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        result = {"page": page_num + 1, "type": None, "text": None, "certificate_data": None}

        if is_scan(page):
            result["type"] = "scan"
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")

            ocr_text = process_scan_with_mistral(img_bytes)
            result["text"] = ocr_text

            cert_data = analyze_certificate(ocr_text)
            if cert_data:
                result["certificate_data"] = cert_data
        else:
            result["type"] = "text"
            result["text"] = page.get_text()

        results.append(result)

    return results


def save_results_to_json(results, output_file=None):
    if not output_file:
        source = results["metadata"]["source_file"].split("/")[-1].split(".")[0]
        date = results["metadata"]["processing_date"].split()[0]
        output_file = f"pdf_analysis_{source}_{date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return output_file


pdf_path = "exa.pdf"
analysis_results = process_pdf(pdf_path)


for result in analysis_results:
    print(f"\nСтраница {result['page']}:")
    print(f"Тип: {result['type']}")
    if result['certificate_data']:
        print("Найден сертификат качества!")
        print("Данные сертификата:", result['certificate_data'])
    print(f"Текст (первые 100 символов): {result['text'][:100]}...")

