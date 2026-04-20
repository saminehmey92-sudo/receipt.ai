import streamlit as st
import base64
import requests
import re
from datetime import datetime, timedelta

# 1. إعدادات الواجهة (ألوان واضحة وخطوط بارزة)
st.set_page_config(page_title="مدير المرتجعات الاحترافي", page_icon="🟢", layout="wide")

st.markdown("""
    <style>
    /* تحسين الرؤية والتباين */
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #075E54 !important; font-weight: bold; }
    
    /* تصميم بطاقات المنتجات في القائمة النهائية */
    .refund-card { 
        background-color: #f1f1f1; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 8px solid #25D366; 
        margin-bottom: 15px;
        color: #000000;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .delete-btn { color: #cc0000; font-weight: bold; }
    
    /* الأزرار */
    .stButton>button { 
        background-color: #25D366 !important; 
        color: white !important; 
        border-radius: 8px; 
        font-weight: bold;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🟢 مدير المرتجعات الذكي")

# إدارة المفتاح
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("أدخل OpenAI API Key:", type="password")

# --- المدخلات الأساسية ---
col_u1, col_u2 = st.columns(2)
with col_u1:
    uploaded_file = st.file_uploader("1️⃣ ارفع صورة الإيصال", type=['jpg', 'jpeg', 'png'])
with col_u2:
    store_name = st.text_input("🏠 اسم المتجر (اختياري):", placeholder="مثلاً: Stater Bros")
    return_days = st.number_input("⏱️ مهلة الاسترجاع (أيام):", value=30)

# --- دالة التحليل ---
def analyze_receipt(image_b64, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Extract items and prices. Format: Item | Price"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]}]
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except: return "ERROR"

# --- المعالجة ---
if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    if st.button("🚀 تحليل الإيصال"):
        with st.spinner('جاري التحليل...'):
            raw_output = analyze_receipt(img_b64, api_key)
            items = []
            for line in raw_output.split('\n'):
                match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                if match:
                    items.append({
                        "name": match.group(1).strip(),
                        "price": float(match.group(2)),
                        "store": store_name if store_name else "متجر غير محدد",
                        "date_added": datetime.now(),
                        "expiry_date": datetime.now() + timedelta(days=return_days)
                    })
            st.session_state.temp_items = items

# --- القائمة المؤقتة (للتعديل والنقل) ---
if "temp_items" in st.session_state:
    st.subheader("📝 راجع البيانات قبل النقل")
    final_selection = []
    for i, item in enumerate(st.session_state.temp_items):
        c1, c2, c3 = st.columns([0.5, 3, 1.5])
        with c1: sel = st.checkbox("", key=f"s_{i}")
        with c2: name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}", label_visibility="collapsed")
        with c3: price = st.number_input(f"p_{i}", value=item['price'], key=f"price_{i}", label_visibility="collapsed")
        if sel: final_selection.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry_date']})
    
    if st.button("📥 نقل إلى قائمة المرتجعات النهائية"):
        if "refund_list" not in st.session_state: st.session_state.refund_list = []
        st.session_state.refund_list.extend(final_selection)
        st.success("تم النقل!")

# --- القائمة النهائية (الفرز، الحذف، العرض) ---
if "refund_list" in st.session_state and len(st.session_state.refund_list) > 0:
    st.divider()
    st.header("📋 قائمة المرتجعات النهائية")

    # خيارات الترتيب
    sort_option = st.selectbox("🔄 ترتيب حسب:", ["الأحدث مضافاً", "الوقت المتبقي للاسترجاع", "اسم المتجر"])
    
    if sort_option == "الوقت المتبقي للاسترجاع":
        st.session_state.refund_list.sort(key=lambda x: x['expiry'])
    elif sort_option == "اسم المتجر":
        st.session_state.refund_list.sort(key=lambda x: x['store'])

    # عرض العناصر مع خيار الحذف
    for i, item in enumerate(st.session_state.refund_list):
        days_left = (item['expiry'] - datetime.now()).days
        
        with st.container():
            col_content, col_del = st.columns([5, 1])
            with col_content:
                st.markdown(f"""
                <div class="refund-card">
                    <h3 style='margin:0;'>{item['name']} - ${item['price']:.2f}</h3>
                    <b>المتجر:</b> {item['store']} | <b>الوقت المتبقي:</b> {max(0, days_left)} يوم
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button(f"❌ إزالة", key=f"del_{i}"):
                    st.session_state.refund_list.pop(i)
                    st.rerun()

    total = sum(item['price'] for item in st.session_state.refund_list)
    st.metric("إجمالي مبلغ المرتجعات", f"${total:.2f}")
