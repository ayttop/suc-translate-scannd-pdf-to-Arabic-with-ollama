import os
import json
import fitz
import pytesseract
from ollama import Client
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pytesseract import Output
from pathlib import Path
import arabic_reshaper
# ملاحظة: تم إيقاف استخدام get_display بناءً على طلبك
# from bidi.algorithm import get_display 

# 1. حل مشكلة الصور الضخمة
Image.MAX_IMAGE_PIXELS = None 

# 2. إعداد اتصال Ollama
ollama_client = Client(host='http://127.0.0.1:11434')
file_path = Path(__file__).parent

def ollama_send(text):
    """ترجمة احترافية من الموديل مباشرة"""
    if not text.strip() or len(text) < 2: return None
    try:
        res = ollama_client.chat(model='translategemma:12b', messages=[
            {
                'role': 'user', 
                'content': f"Translate the following text to Arabic. Provide ONLY the translation. Text: {text}"
            }
        ])
        translated = res['message']['content'].strip()
        
        # تنظيف أي نصوص إضافية بالإنجليزية قد يضعها الذكاء الاصطناعي
        if "translation" in translated.lower() or "here is" in translated.lower():
            lines = translated.split('\n')
            translated = " ".join([l for l in lines if not any(w in l.lower() for w in ["here is", "translation", "sure"])])
        
        return translated
    except:
        return None

def wrap_text(text, font, max_width):
    """تقسيم النص لأسطر تتناسب مع عرض المربع لمنع تداخل النصوص"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        # حساب عرض النص الحالي بالبكسل
        if font.getlength(test_line) <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def fix_arabic_line(text):
    """ربط الحروف العربية فقط دون عكس الاتجاه"""
    if not text: return ""
    # ربط الحروف ببعضها (reshape) لتظهر "كلمات" وليس "حروف مقطعة"
    reshaped_text = arabic_reshaper.reshape(text)
    # تم إلغاء get_display هنا
    return reshaped_text

def main():
    # التأكد من تشغيل Ollama
    try:
        ollama_client.list()
    except:
        print("Ollama is not running!")
        return

    # تحميل الإعدادات من ملف الـ JSON
    with open(file_path / "config.json", "r", encoding="utf-8") as f:
        data_config = json.load(f)

    pytesseract.pytesseract.tesseract_cmd = data_config['path']
    pdf_doc = fitz.open(data_config['target_path'])
    output_filename = f"Translated_Fixed_{Path(data_config['target_path']).stem}.pdf"
    
    total_pages = len(pdf_doc)
    translated_pdf = fitz.open()
    font_path = "C:/Windows/Fonts/arial.ttf"

    for i in range(total_pages):
        print(f"Processing Page {i+1} / {total_pages}...")
        page = pdf_doc[i]
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)
        
        ocr_data = pytesseract.image_to_data(img, output_type=Output.DICT)
        
        blocks = {}
        for j in range(len(ocr_data["text"])):
            txt = ocr_data["text"][j].strip()
            if txt:
                b_num = ocr_data["block_num"][j]
                if b_num not in blocks:
                    blocks[b_num] = {"text": [], "left": [], "top": [], "width": [], "height": []}
                blocks[b_num]["text"].append(txt)
                blocks[b_num]["left"].append(ocr_data["left"][j])
                blocks[b_num]["top"].append(ocr_data["top"][j])
                blocks[b_num]["width"].append(ocr_data["width"][j])
                blocks[b_num]["height"].append(ocr_data["height"][j])

        for b_id in blocks:
            b = blocks[b_id]
            full_text = " ".join(b["text"])
            
            # حساب إحداثيات الكتلة
            min_l, min_t = min(b["left"]), min(b["top"])
            max_r = max([l + w for l, w in zip(b["left"], b["width"])])
            max_b = max([t + h for t, h in zip(b["top"], b["height"])])
            block_width = max_r - min_l
            
            translated = ollama_send(full_text)
            
            if translated:
                # 1. مسح النص القديم بلون الخلفية
                bg_color = img.getpixel((min_l, min_t))
                draw.rectangle([min_l, min_t, max_r, max_b], fill=bg_color)
                
                # 2. إعداد حجم الخط (Scaling)
                original_h = max_b - min_t
                font_size = max(14, int(original_h * 0.7))
                if font_size > 55: font_size = 45 # سقف للحجم لضمان التنسيق
                
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except:
                    font = ImageFont.load_default()

                # 3. تقسيم النص المترجم لأسطر (التفاف النص)
                lines = wrap_text(translated, font, block_width)
                
                # 4. رسم الأسطر (ربط الحروف فقط)
                current_y = min_t
                for line in lines:
                    final_line = fix_arabic_line(line)
                    
                    # بما أننا ألغينا عكس الاتجاه، سنرسم من جهة اليسار min_l 
                    # أو اليمين حسب الحاجة، هنا سنرسم من اليسار بشكل طبيعي
                    draw.text((min_l, current_y), final_line, fill="black", font=font)
                    
                    # النزول للسطر التالي
                    current_y += font_size + 5

        # حفظ الصفحة في ملف مؤقت ثم دمجها في PDF
        temp_img = f"temp_page_{i}.jpg"
        img.save(temp_img, quality=95)
        new_page = translated_pdf.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(new_page.rect, filename=temp_img)
        
        if os.path.exists(temp_img):
            os.remove(temp_img)

    # حفظ الملف النهائي
    translated_pdf.save(output_filename)
    translated_pdf.close()
    print(f"تم الانتهاء! الملف الناتج: {output_filename}")

if __name__ == "__main__":
    main()