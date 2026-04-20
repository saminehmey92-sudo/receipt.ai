import streamlit as st
import cv2
import numpy as np
from PIL import Image
import easyocr
import re

# تهيئة القارئ
@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

reader = get_reader()

st.title("🟢 قارئ المرتجعات المطور")

camera_photo = st.camera_input("التقط صورة للإيصال (حاول تقريب الكاميرا)")

if camera_photo:
    # 1. تحويل الصورة لمعالجتها
    file_bytes = np.asarray(bytearray(camera_photo.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    # 2. تحسين جودة الصورة (تحويل لرمادي + زيادة التباين)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    st.image(enhanced_img, caption="الصورة بعد المعالجة البرمجية", width=300)
    
    with st.spinner('جاري التحليل العميق...'):
        # 3. القراءة من الصورة المحسنة
        results = reader.readtext(enhanced_img)
        extracted_text = "\n".join([res[1] for res in results])
        
        st.write("### النص الذي تم رصده:")
        # تنظيف النص المستخرج ليعرض المشتريات فقط
        clean_text = st.text_area("تعديل النص المستخرج:", extracted_text, height=150)
        
        if st.button("تحويل إلى قائمة اختيار"):
            items = []
            lines = clean_text.split('\n')
            for line in lines:
                # محاولة صيد أي سعر
                price_match = re.search(r"(\d+[\.,]\d{2})", line)
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))
                    # تنظيف الاسم من الأرقام والرموز
                    name = re.sub(r'[^a-zA-Z\s]', '', line.replace(price_match.group(1), "")).strip()
                    if not name: name = "Item"
                    items.append({"name": name, "price": price})
            
            st.session_state.items = items

# عرض القائمة التفاعلية
if "items" in st.session_state:
    st.write("---")
    total = 0.0
    for i, item in enumerate(st.session_state.items):
        if st.checkbox(f"{item['name']} - ${item['price']}", key=f"sel_{i}"):
            total += item['price']
    
    st.metric("إجمالي المرتجع", f"${total:.2f}")
    if total > 0:
        st.success("اضغط 'تأكيد' لإتمام العملية")
