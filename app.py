import streamlit as st
import base64
import requests
import re
from datetime import datetime, timedelta

# --- 1. الإعدادات الأولية (يجب أن تكون في البداية) ---
st.set_page_config(page_title="مدير المرتجعات الذكي", page_icon="🟢", layout="wide")

# تصميم الواجهة (ألوان WhatsApp و Cash App) لضمان وضوح الرؤية
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .refund-card { 
        background-color: #f9f9f9; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 10px solid #25D366; 
        margin-bottom: 10px;
        color: #000000;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #25D366 !important; color: white !important; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

st.title("🟢 مدير المرتجعات الذكي")

# --- 2. تعريف المتغيرات والمدخلات (قبل أي شروط if) ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("أدخل OpenAI API Key:", type="password")
    
    return_days = st.number_input("مهلة الاسترجاع (أيام):", value=30)

uploaded_file = st.file_uploader("1️⃣ ارفع صورة الإيصال هنا", type=['jpg', 'jpeg', 'png'])

# --- 3. الدوال البرمجية ---
def analyze_receipt_v4(image_b64, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": "Analyze this receipt. 1. Identify Store Name. 2. List items and prices. Format: STORE: [Name] then ITEMS: Name | Price"
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except:
        return "ERROR"

# --- 4. معالجة البيانات (بعد تعريف المتغيرات) ---
if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    st.image(uploaded_file, width=300, caption="الإيصال المرفوع")

    if st.button("🚀 تحليل الإيصال واستخراج المتجر"):
        with st.spinner('جاري تحليل البيانات...'):
            raw_output = analyze_receipt_v4(img_b64, api_key)
            
            # استخراج المتجر والمنتجات
            store_match = re.search(r"STORE:\s*(.*)", raw_output)
            detected_store = store_match.group(1).strip() if store_match else "متجر غير معروف"
            
            items = []
            for line in raw_output.split('\n'):
                item_match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                if item_match and "STORE" not in line.upper():
                    items.append({
                        "name": item_match.group(1).strip(),
                        "price": float(item_match.group(2)),
                        "store": detected_store,
                        "expiry": datetime.now() + timedelta(days=return_days)
                    })
            
            if items:
                st.session_state.temp_items = items
                st.session_state.current_store = detected_store
            else:
                st.error("لم نتمكن من قراءة المنتجات. حاول رفع صورة أوضح.")

# --- 5. واجهة التعديل والنقل ---
if "temp_items" in st.session_state and st.session_state.temp_items:
    st.divider()
    st.subheader(f"📝 مراجعة مشتريات: {st.session_state.current_store}")
    
    final_selection = []
    for i, item in enumerate(st.session_state.temp_items):
        c1, c2, c3 = st.columns([0.5, 3, 1.5])
        with c1: 
            sel = st.checkbox("", key=f"s_{i}")
        with c2: 
            name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}", label_visibility="collapsed")
        with c3: 
            price = st.number_input(f"p_{i}", value=item['price'], format="%.2f", key=f"price_{i}", label_visibility="collapsed")
        
        if sel:
            final_selection.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry']})
    
    if st.button("📥 نقل المختار إلى القائمة النهائية"):
        if "refund_list" not in st.session_state: 
            st.session_state.refund_list = []
        st.session_state.refund_list.extend(final_selection)
        st.success("تمت الإضافة بنجاح!")
        # مسح القائمة المؤقتة بعد النقل
        del st.session_state.temp_items
        st.rerun()

# --- 6. القائمة النهائية ---
if "refund_list" in st.session_state and len(st.session_state.refund_list) > 0:
    st.divider()
    st.header("📋 قائمة المرتجعات النهائية")
    
    for i, item in enumerate(st.session_state.refund_list):
        days_left = (item['expiry'] - datetime.now()).days
        col_card, col_del = st.columns([5, 1])
        with col_card:
            st.markdown(f"""
                <div class="refund-card">
                    <h3 style='margin:0;'>{item['name']} - ${item['price']:.2f}</h3>
                    <b>المتجر:</b> {item['store']} | <b>المتبقي:</b> {max(0, days_left)} يوم
                </div>
            """, unsafe_allow_html=True)
        with col_del:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.refund_list.pop(i)
                st.rerun()

    total = sum(item['price'] for item in st.session_state.refund_list)
    st.metric("إجمالي مبلغ المرتجعات", f"${total:.2f}")
