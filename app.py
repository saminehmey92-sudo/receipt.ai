import streamlit as st
import re

# إعدادات الواجهة والألوان
st.set_page_config(page_title="مدير الإيصالات", page_icon="🟢")
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; }
    .stButton>button { background-color: #25D366; color: white; width: 100%; border-radius: 10px; }
    .main-header { color: #075E54; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🟢 نظام إدارة المرتجعات</h1>', unsafe_allow_html=True)

# 1. إدخال البيانات
raw_data = st.text_area("أدخل نص الإيصال هنا:", 
                         "MILK 4.99\nBREAD 3.50\nCHICKEN 12.45", height=150)

# 2. منطق تحليل البيانات وحفظها في الذاكرة (Session State)
if st.button("تحليل المشتريات"):
    lines = raw_data.strip().split('\n')
    items = []
    for line in lines:
        price_match = re.search(r"(\d+[\.,]\d{2})", line)
        if price_match:
            price = float(price_match.group(1).replace(',', '.'))
            name = line.replace(price_match.group(1), "").strip()
            items.append({"name": name, "price": price})
    
    # حفظ القائمة في ذاكرة المتصفح
    st.session_state.receipt_items = items
    st.session_state.show_list = True

# 3. عرض القائمة إذا تم التحليل بنجاح
if "show_list" in st.session_state and st.session_state.show_list:
    st.write("---")
    st.subheader("✅ اختر المنتجات المراد إرجاعها:")
    
    total_refund = 0.0
    selected_items = []

    for i, item in enumerate(st.session_state.receipt_items):
        # استخدام Checkbox لكل منتج
        is_selected = st.checkbox(f"{item['name']} - ${item['price']}", key=f"item_{i}")
        if is_selected:
            total_refund += item['price']
            selected_items.append(item['name'])
    
    st.divider()
    
    # عرض النتائج بشكل جذاب (الأخضر المميز)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("إجمالي المرتجع", f"${total_refund:.2f}")
    with col2:
        if total_refund > 0:
            st.success(f"تم تحديد {len(selected_items)} أصناف")

    if total_refund > 0:
        if st.button("تأكيد عملية الإرجاع"):
            st.balloons()
            st.info(f"جاري معالجة إرجاع: {', '.join(selected_items)}")
