import streamlit as st
import base64
import requests
import re
from datetime import datetime, timedelta

# 1. إعدادات الواجهة والتباين العالي
st.set_page_config(page_title="مدير المرتجعات الذكي", page_icon="🟢", layout="wide")

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
    .stButton>button { background-color: #25D366 !important; color: white !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🟢 مدير المرتجعات الذكي (التعرف التلقائي)")

# إدارة المفتاح
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("أدخل OpenAI API Key:", type="password")

# مدخلات إضافية
with st.sidebar:
    st.header("⚙️ إعدادات الاسترجاع")
    return_days = st.number_input("مهلة الاسترجاع الافتراضية (أيام):", value=30)

uploaded_file = st.file_uploader("1️⃣ ارفع صورة الإيصال ليتم تحليلها تلقائياً", type=['jpg', 'jpeg', 'png'])

# 2. دالة التحليل مع استخراج اسم المتجر
def analyze_receipt_v4(image_b64, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": """Analyze this receipt. 
                    1. Identify the Store Name from the top.
                    2. List all items and prices.
                    Format the output strictly as:
                    STORE: [Store Name]
                    ITEMS:
                    ItemName | Price"""
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except: return "ERROR"

# 3. المعالجة الذكية للبيانات
if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    if st.button("🚀 تحليل الإيصال واستخراج المتجر"):
        with st.spinner('جاري فحص المتجر والمنتجات...'):
            raw_output = analyze_receipt_v4(img_b64, api_key)
            
            # استخراج اسم المتجر والمنتجات عبر Regex
            store_match = re.search(r"STORE:\s*(.*)", raw_output)
            detected_store = store_match.group(1).strip() if store_match else "متجر غير معروف"
            
            items = []
            # استخراج المنتجات بعد كلمة ITEMS:
            lines = raw_output.split('\n')
            for line in lines:
                item_match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                if item_match and "STORE" not in line:
                    items.append({
                        "name": item_match.group(1).strip(),
                        "price": float(item_match.group(2)),
                        "store": detected_store,
                        "expiry": datetime.now() + timedelta(days=return_days)
                    })
            st.session_state.temp_items = items

# 4. مرحلة التعديل والنقل
if "temp_items" in st.session_state:
    st.subheader(f"📝 مراجعة مشتريات متجر: {st.session_state.temp_items[0]['store']}")
    final_selection = []
    for i, item in enumerate(st.session_state.temp_items):
        c1, c2, c3 = st.columns([0.5, 3, 1.5])
        with c1: sel = st.checkbox("", key=f"s_{i}")
        with c2: name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}", label_visibility="collapsed")
        with c3: price = st.number_input(f"p_{i}", value=item['price'], format="%.2f", key=f"price_{i}", label_visibility="collapsed")
        if sel: final_selection.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry']})
    
    if st.button("📥 إضافة المختار إلى قائمة المرتجعات"):
        if "refund_list" not in st.session_state: st.session_state.refund_list = []
        st.session_state.refund_list.extend(final_selection)
        st.success(f"تمت إضافة العناصر من {st.session_state.temp_items[0]['store']}")

# 5. القائمة النهائية (ترتيب، حذف، عرض)
if "refund_list" in st.session_state and len(st.session_state.refund_list) > 0:
    st.divider()
    st.header("📋 القائمة النهائية للمرتجعات")
    
    sort_option = st.selectbox("🔄 ترتيب حسب:", ["الأحدث مضافاً", "الوقت المتبقي", "اسم المتجر"])
    
    if sort_option == "الوقت المتبقي":
        st.session_state.refund_list.sort(key=lambda x: x['expiry'])
    elif sort_option == "اسم المتجر":
        st.session_state.refund_list.sort(key=lambda x: x['store'])

    for i, item in enumerate(st.session_state.refund_list):
        days_left = (item['expiry'] - datetime.now()).days
        with st.container():
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
    st.metric("إجمالي المرتجع", f"${total:.2f}")
