import streamlit as st
import re
from PIL import Image

# إعدادات الواجهة
st.set_page_config(page_title="مدير الإيصالات الذكي", page_icon="📸")
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; }
    .stButton>button { background-color: #25D366; color: white; border-radius: 10px; height: 3em; font-weight: bold; }
    .main-header { color: #075E54; text-align: center; }
    .upload-box { border: 2px dashed #25D366; padding: 10px; border-radius: 10px; background: white; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📸 قارئ المرتجعات الذكي</h1>', unsafe_allow_html=True)

# 1. خيار الكاميرا ورفع الملفات
st.write("### 1. تصوير أو رفع الإيصال")
tab1, tab2 = st.tabs(["📷 استخدام الكاميرا", "📁 رفع من المعرض"])

uploaded_image = None

with tab1:
    # هذا الأمر يفتح كاميرا الموبايل مباشرة
    camera_photo = st.camera_input("التقط صورة واضحة للإيصال")
    if camera_photo:
        uploaded_image = camera_photo

with tab2:
    file_photo = st.file_uploader("اختر صورة الإيصال", type=['jpg', 'jpeg', 'png'])
    if file_photo:
        uploaded_image = file_photo

# 2. معالجة الصورة (OCR) - ملاحظة: سنستخدم الـ Text حالياً كمحاكاة حتى نربط الـ API
if uploaded_image:
    st.image(uploaded_image, caption="تم تحميل الإيصال بنجاح", use_column_width=True)
    st.success("تم التقاط الصورة! جاري استخراج البيانات...")
    
    # هنا سنضع نصاً افتراضياً كمحاكاة لما سيقرأه الـ API من الصورة
    # في الخطوة القادمة سنربط Google Vision أو OpenAI لقراءة النص الحقيقي
    st.info("💡 ملاحظة: النظام الآن يحلل الصورة (قريباً سيتم ربط OCR بالكامل)")

st.divider()

# 3. إدخال النص يدوياً (للتجربة الحالية)
raw_data = st.text_area("تعديل النص المستخرج (أو أدخله يدوياً):", 
                         "MILK 4.99\nBREAD 3.50\nCHICKEN 12.45")

if st.button("تحليل المشتريات واستخراج البنود"):
    lines = raw_data.strip().split('\n')
    items = []
    for line in lines:
        price_match = re.search(r"(\d+[\.,]\d{2})", line)
        if price_match:
            price = float(price_match.group(1).replace(',', '.'))
            name = line.replace(price_match.group(1), "").strip()
            items.append({"name": name, "price": price})
    
    st.session_state.receipt_items = items
    st.session_state.show_list = True

# 4. قائمة الاختيار (كما في الكود السابق)
if "show_list" in st.session_state and st.session_state.show_list:
    st.subheader("✅ حدد المرتجعات:")
    total_refund = 0.0
    for i, item in enumerate(st.session_state.receipt_items):
        if st.checkbox(f"{item['name']} - ${item['price']}", key=f"item_{i}"):
            total_refund += item['price']
    
    st.metric("إجمالي المبلغ المسترد", f"${total_refund:.2f}")
