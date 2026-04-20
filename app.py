import streamlit as st
import re
import numpy as np
from PIL import Image
import easyocr

# إعداد قارئ النصوص (OCR) - يدعم الإنجليزية حالياً لزيادة الدقة
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

st.set_page_config(page_title="قاريء الإيصالات الذكي", page_icon="📸")
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; }
    .stButton>button { background-color: #25D366; color: white; border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📸 قراءة المرتجعات الحقيقية")

# التقاط الصورة
camera_photo = st.camera_input("التقط صورة واضحة للإيصال")

if camera_photo:
    # معالجة الصورة
    image = Image.open(camera_photo)
    st.image(image, caption="تم التقاط الصورة", use_column_width=True)
    
    with st.spinner('جاري قراءة البيانات بدقة...'):
        # تحويل الصورة إلى مصفوفة رقمية للقارئ
        img_array = np.array(image)
        result = reader.readtext(img_array)
        
        # تجميع النص المستخرج
        extracted_text = "\n".join([res[1] for res in result])
        
        st.success("تمت القراءة!")
        
        # عرض النص المستخرج للتعديل إذا لزم الأمر
        raw_data = st.text_area("النص المستخرج (يمكنك تعديله):", extracted_text, height=200)

        # منطق تحليل البنود والأسعار
        if st.button("تحويل النص إلى قائمة مشتريات"):
            lines = raw_data.strip().split('\n')
            items = []
            for line in lines:
                # البحث عن الأسعار (أرقام بها فاصلة عشرية)
                price_match = re.search(r"(\d+[\.,]\d{2})", line)
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))
                    # تنظيف اسم المنتج من الرموز
                    name = re.sub(r'[^a-zA-Z\s]', '', line.replace(price_match.group(1), "")).strip()
                    if not name: name = "منتج غير معروف"
                    items.append({"name": name, "price": price})
            
            st.session_state.receipt_items = items
            st.session_state.show_list = True

# عرض قائمة المرتجعات
if "show_list" in st.session_state and st.session_state.show_list:
    st.write("---")
    st.subheader("✅ حدد المرتجعات من القائمة:")
    total_refund = 0.0
    for i, item in enumerate(st.session_state.receipt_items):
        if st.checkbox(f"{item['name']} - ${item['price']}", key=f"item_{i}"):
            total_refund += item['price']
    
    st.metric("إجمالي المبلغ المسترد", f"${total_refund:.2f}")
