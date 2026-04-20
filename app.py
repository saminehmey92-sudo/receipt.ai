import streamlit as st
import re

# 1. إعدادات الهوية البصرية (اللون الأخضر المطلوب)
st.set_page_config(page_title="Receipt Manager", page_icon="💸")
custom_style = """
    <style>
    .stApp { background-color: #f0f2f5; }
    .stButton>button { background-color: #25D366; color: white; border-radius: 20px; border: none; }
    .stCheckbox { color: #075E54; }
    .header-box { background-color: #075E54; padding: 20px; border-radius: 10px; color: white; text-align: center; }
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# واجهة التطبيق
st.markdown('<div class="header-box"><h1>مشروع مدير الإيصالات الذكي</h1></div>', unsafe_allow_html=True)

# 2. منطقة إدخال البيانات (الـ API والنص)
with st.sidebar:
    st.header("الإعدادات")
    api_key = st.text_input("أدخل مفتاح API (OpenAI/HuggingFace)", type="password")
    st.write("---")
    st.success("الهوية البصرية: WhatsApp Green Active")

# 3. محاكاة تحليل الإيصال (المرحلة الثانية)
st.subheader("📄 بيانات الإيصال")
raw_data = st.text_area("أدخل نص الإيصال هنا (مثال: Stater Bros)", 
                         "MILK GALLON 4.99\nBREAD WHOLE 3.50\nCHICKEN BREAST 12.45\nAPPLES FUJI 2.10")

if st.button("تحليل المشتريات"):
    # دالة الاستخراج باستخدام Regex
    pattern = r"(.+?)\s+([\d,]+\.\d{2})"
    items = []
    lines = raw_data.strip().split('\n')
    
    st.write("### حدد المنتجات التي ترغب في إرجاعها:")
    
    total_refund = 0.0
    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            name = match.group(1).strip()
            price = float(match.group(2))
            
            # عرض كل بند مع اختيار (Checkbox)
            if st.checkbox(f"{name} - ${price}", key=f"item_{i}"):
                total_refund += price
    
    st.divider()
    st.metric(label="إجمالي المبلغ المسترد", value=f"${total_refund:.2f}")
    
    if total_refund > 0:
        st.info(f"سيتم تجهيز طلب المرتجعات لمبلغ {total_refund} دولار.")
