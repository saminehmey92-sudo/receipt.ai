import streamlit as st
import base64
import requests
import re
from datetime import datetime, timedelta

# --- 1. إعدادات التصميم الاحترافي (Mobile-First Design) ---
st.set_page_config(page_title="Return Manager Pro", page_icon="📲", layout="wide")

st.markdown("""
    <style>
    /* تحسين الخطوط والخلفية العامة */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; background-color: #f4f7f6; }

    /* حاوية التطبيق الرئيسية */
    .main-header {
        background: linear-gradient(135deg, #075E54 0%, #25D366 100%);
        padding: 2rem;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* بطاقات المشتريات المستخرجة */
    .edit-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
        transition: 0.3s;
    }
    .edit-card:hover { border-color: #25D366; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

    /* قائمة المرتجعات النهائية (Style الموبايل) */
    .final-card {
        background: white;
        padding: 18px;
        border-radius: 20px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-right: 8px solid #25D366;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    .price-tag {
        background: #e3fcef;
        color: #075E54;
        padding: 5px 12px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem;
    }

    /* أزرار عصرية */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5rem;
        background-color: #25D366 !important;
        color: white !important;
        font-size: 1.1rem;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4); }
    
    /* شريط الحالة الصغير */
    .status-badge {
        font-size: 0.8rem;
        padding: 3px 8px;
        border-radius: 5px;
        background: #eee;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

# الهيدر الاحترافي
st.markdown("""
    <div class="main-header">
        <h1>📲 Return Manager Pro</h1>
        <p>إدارة المرتجعات بذكاء واحترافية</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. الإعدادات الجانبية ---
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات الذكية")
    api_key = st.secrets.get("OPENAI_API_KEY", "") or st.text_input("OpenAI Key:", type="password")
    return_days = st.select_slider("مهلة الاسترجاع الافتراضية", options=[7, 14, 30, 60, 90], value=30)
    st.info("سيتم حساب تاريخ الانتهاء تلقائياً بناءً على اختيارك.")

# --- 3. منطقة الرفع والتحليل ---
col_upload, col_preview = st.columns([1, 1])

with col_upload:
    st.markdown("### 📸 خطوة 1: تصوير الإيصال")
    uploaded_file = st.file_uploader("", type=['jpg', 'jpeg', 'png'], help="ارفع صورة واضحة للإيصال")
    
    if uploaded_file and api_key:
        img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        if st.button("🔍 تحليل البيانات الآن"):
            with st.spinner('جاري المسح الضوئي للبيانات...'):
                # (دالة analyze_receipt_v4 هي نفسها من الكود السابق)
                def analyze_receipt_v4(image_b64, key):
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o",
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": "Identify Store Name and list items with prices. Format: STORE: [Name] ITEMS: Name | Price"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                        ]}]
                    }
                    try:
                        r = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                        return r.json()['choices'][0]['message']['content']
                    except: return "ERROR"

                raw_output = analyze_receipt_v4(img_b64, api_key)
                store_name = re.search(r"STORE:\s*(.*)", raw_output).group(1).strip() if "STORE" in raw_output else "متجر غير معروف"
                
                items = []
                for line in raw_output.split('\n'):
                    m = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                    if m and "STORE" not in line.upper():
                        items.append({
                            "name": m.group(1).strip(), "price": float(m.group(2)),
                            "store": store_name, "expiry": datetime.now() + timedelta(days=return_days)
                        })
                
                if items:
                    st.session_state.temp_items = items
                    st.session_state.current_store = store_name
                else:
                    st.error("لم نتمكن من قراءة البيانات، جرب صورة أوضح.")

with col_preview:
    if uploaded_file:
        st.image(uploaded_file, use_column_width=True)

# --- 4. واجهة المراجعة والتعديل (User Experience) ---
if "temp_items" in st.session_state and st.session_state.temp_items:
    st.markdown(f"### 📝 مراجعة مشتريات {st.session_state.current_store}")
    
    final_selection = []
    for i, item in enumerate(st.session_state.temp_items):
        with st.container():
            # تصميم بطاقة تعديل صغيرة
            st.markdown(f'<div class="edit-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([0.5, 3, 1.5])
            with c1: sel = st.checkbox("", key=f"s_{i}")
            with c2: name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}", label_visibility="collapsed")
            with c3: price = st.number_input(f"p_{i}", value=item['price'], format="%.2f", key=f"price_{i}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if sel:
                final_selection.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry']})
    
    if st.button("📥 نقل العناصر المختارة للقائمة النهائية"):
        if "refund_list" not in st.session_state: st.session_state.refund_list = []
        st.session_state.refund_list.extend(final_selection)
        del st.session_state.temp_items
        st.balloons()
        st.rerun()

# --- 5. القائمة النهائية (تصميم تطبيق موبايل) ---
if "refund_list" in st.session_state and st.session_state.refund_list:
    st.markdown("---")
    st.header("🛒 قائمة المرتجعات النشطة")
    
    # فلتر الترتيب
    sort_by = st.segmented_control("الترتيب حسب:", ["الأحدث", "الوقت المتبقي", "المتجر"], default="الأحدث")

    # منطق الترتيب
    if sort_by == "الوقت المتبقي": st.session_state.refund_list.sort(key=lambda x: x['expiry'])
    elif sort_option == "المتجر": st.session_state.refund_list.sort(key=lambda x: x['store'])

    for i, item in enumerate(st.session_state.refund_list):
        days_left = (item['expiry'] - datetime.now()).days
        color = "#25D366" if days_left > 5 else "#FF3B30" # أحمر إذا قارب على الانتهاء
        
        st.markdown(f"""
            <div class="final-card" style="border-right-color: {color}">
                <div>
                    <div style="font-size: 1.2rem; font-weight: bold;">{item['name']}</div>
                    <div style="color: #666; font-size: 0.9rem;">🏢 {item['store']}</div>
                    <div class="status-badge">⏳ متبقي: {max(0, days_left)} يوم</div>
                </div>
                <div class="price-tag">${item['price']:.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"حذف من القائمة", key=f"del_{i}"):
            st.session_state.refund_list.pop(i)
            st.rerun()

    total = sum(item['price'] for item in st.session_state.refund_list)
    st.markdown(f"""
        <div style="background: #075E54; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-top: 20px;">
            <span style="font-size: 1.2rem;">إجمالي المستردات المحتملة</span><br>
            <span style="font-size: 2.5rem; font-weight: bold;">${total:.2f}</span>
        </div>
    """, unsafe_allow_html=True)
