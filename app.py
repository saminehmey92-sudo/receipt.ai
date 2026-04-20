import streamlit as st
import re
from PIL import Image
import easyocr
import numpy as np

# تهيئة القارئ في الذاكرة لمرة واحدة
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])

reader = load_reader()

# تنسيق الواجهة باللون الأخضر (WhatsApp/Cash App)
st.set_page_config(page_title="مدير الإيصالات", page_icon="🟢")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { background-color: #25D366; color: white; border-radius: 12px; font-weight: bold; width: 100%; }
    .stHeader { color: #075E54; }
    </style>
""", unsafe_allow_html=True)

st.title("🟢 رفع وتحليل الإيصالات")

# 1. خيار رفع الصورة من المعرض
uploaded_file = st.file_uploader("اختر صورة الإيصال من المعرض (Gallery)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # عرض الصورة المختارة
    image = Image.open(uploaded_file)
    st.image(image, caption="تم تحميل الصورة بنجاح", use_column_width=True)
    
    with st.spinner('جاري استخراج البيانات من الصورة...'):
        # تحويل الصورة إلى صيغة يفهمها القارئ
        img_array = np.array(image)
        result = reader.readtext(img_array)
        
        # تجميع النصوص
        extracted_text = "\n".join([res[1] for res in result])
        
        st.success("تمت القراءة بنجاح!")
        
        # عرض النص للتعديل
        clean_text = st.text_area("النص المستخرج (راجع الأسعار والأسماء):", extracted_text, height=150)
        
        if st.button("تحويل النص إلى قائمة مرتجعات"):
            items = []
            lines = clean_text.split('\n')
            for line in lines:
                # البحث عن أي رقم عشري (سعر)
                price_match = re.search(r"(\d+[\.,]\d{2})", line)
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))
                    # استخراج اسم المنتج (تجاهل الرموز)
                    name = re.sub(r'[^a-zA-Z\s]', '', line.replace(price_match.group(1), "")).strip()
                    if not name: name = "Item"
                    items.append({"name": name, "price": price})
            
            st.session_state.processed_items = items

# 2. عرض القائمة التفاعلية للمرتجعات
if "processed_items" in st.session_state:
    st.divider()
    st.subheader("✅ حدد بنود المرتجعات:")
    
    total_refund = 0.0
    selected_names = []
    
    for i, item in enumerate(st.session_state.processed_items):
        if st.checkbox(f"{item['name']} — ${item['price']}", key=f"check_{i}"):
            total_refund += item['price']
            selected_names.append(item['name'])
            
    st.divider()
    st.metric("إجمالي المبلغ المسترد", f"${total_refund:.2f}")
    
    if total_refund > 0:
        if st.button("تأكيد العملية"):
            st.balloons()
            st.success(f"تم إرسال طلب إرجاع لـ {len(selected_names)} منتجات.")
