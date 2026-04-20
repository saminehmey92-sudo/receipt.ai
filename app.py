import streamlit as st
import base64
import requests
import re
import io
from datetime import datetime, timedelta
from PIL import Image

# --- 1. إعدادات الواجهة الاحترافية ---
st.set_page_config(page_title="Return Manager Pro", page_icon="📲", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; background-color: #f4f7f6; }
    
    .main-header {
        background: linear-gradient(135deg, #075E54 0%, #25D366 100%);
        padding: 2.5rem;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .edit-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
    }

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

    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5rem;
        background-color: #25D366 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>📲 Return Manager Pro</h1><p>نظام ذكي يدعم جميع صيغ الصور (AVIF, PNG, JPG)</p></div>', unsafe_allow_html=True)

# --- 2. الإعدادات الجانبية ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.secrets.get("OPENAI_API_KEY", "") or st.text_input("أدخل مفتاح OpenAI:", type="password")
    return_days = st.select_slider("مهلة الاسترجاع الافتراضية", options=[7, 14, 30, 45, 60, 90], value=30)

# --- 3. منطقة الرفع والتحليل (دعم AVIF) ---
col_u, col_p = st.columns([1, 1])

with col_u:
    st.markdown("### 📸 الخطوة 1: تصوير أو رفع الإيصال")
    # تم إضافة avif و webp و heic للقائمة
    uploaded_file = st.file_uploader("", type=['jpg', 'jpeg', 'png', 'webp', 'avif', 'heic'])

    if uploaded_file and api_key:
        try:
            # استخدام Pillow لفتح الصورة ومعالجتها (لحل مشكلة AVIF)
            image = Image.open(uploaded_file)
            
            # تحويل الصورة إلى RGB (ضروري لصيغ AVIF و PNG التي تحتوي على شفافية)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            # حفظ الصورة في الذاكرة بصيغة JPEG ليرسلها التطبيق لـ OpenAI
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            if st.button("🔍 تحليل البيانات"):
                with st.spinner('جاري المسح الضوئي وتحويل الصيغة...'):
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o",
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": "Identify Store Name and list all items with prices. Format: STORE: [Name] ITEMS: Name | Price"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]}]
                    }
                    
                    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                    raw_output = response.json()['choices'][0]['message']['content']
                    
                    store_match = re.search(r"STORE:\s*(.*)", raw_output)
                    detected_store = store_match.group(1).strip() if store_match else "متجر غير معروف"
                    
                    items = []
                    for line in raw_output.split('\n'):
                        m = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                        if m and "STORE" not in line.upper():
                            items.append({
                                "name": m.group(1).strip(),
                                "price": float(m.group(2)),
                                "store": detected_store,
                                "expiry": datetime.now() + timedelta(days=return_days)
                            })
                    
                    if items:
                        st.session_state.temp_items = items
                        st.session_state.current_store = detected_store
                    else:
                        st.error("لم نتمكن من قراءة المنتجات. حاول رفع صورة أوضح.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الصورة: {str(e)}")

with col_p:
    if uploaded_file:
        st.image(uploaded_file, use_column_width=True, caption="المستند المرفوع")

# --- 4. واجهة التعديل ---
if "temp_items" in st.session_state and st.session_state.temp_items:
    st.divider()
    st.subheader(f"📝 مراجعة: {st.session_state.current_store}")
    
    final_sel = []
    for i, item in enumerate(st.session_state.temp_items):
        st.markdown('<div class="edit-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([0.5, 3, 1.5])
        with c1: sel = st.checkbox("", key=f"s_{i}")
        with c2: name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}", label_visibility="collapsed")
        with c3: price = st.number_input(f"p_{i}", value=item['price'], format="%.2f", key=f"price_{i}", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        if sel: final_sel.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry']})
    
    if st.button("📥 حفظ في القائمة النهائية"):
        if "refund_list" not in st.session_state: st.session_state.refund_list = []
        st.session_state.refund_list.extend(final_sel)
        del st.session_state.temp_items
        st.rerun()

# --- 5. القائمة النهائية ---
if "refund_list" in st.session_state and st.session_state.refund_list:
    st.divider()
    st.header("🛒 المرتجعات النشطة")
    
    sort_by = st.radio("الترتيب حسب:", ["الأحدث", "الوقت المتبقي", "المتجر"], horizontal=True)
    if sort_by == "الوقت المتبقي": st.session_state.refund_list.sort(key=lambda x: x['expiry'])
    elif sort_by == "المتجر": st.session_state.refund_list.sort(key=lambda x: x['store'])

    for i, item in enumerate(st.session_state.refund_list):
        days_left = (item['expiry'] - datetime.now()).days
        status_color = "#25D366" if days_left > 5 else "#FF3B30"
        
        col_card, col_del = st.columns([5, 1])
        with col_card:
            st.markdown(f"""
                <div class="final-card" style="border-right-color: {status_color}">
                    <div>
                        <div style="font-size: 1.1rem; font-weight: bold;">{item['name']}</div>
                        <div style="color: #666; font-size: 0.8rem;">🏢 {item['store']} | ⏳ متبقي: {max(0, days_left)} يوم</div>
                    </div>
                    <div class="price-tag">${item['price']:.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        with col_del:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.refund_list.pop(i)
                st.rerun()

    total = sum(item['price'] for item in st.session_state.refund_list)
    st.markdown(f'<div style="background:#075E54;color:white;padding:20px;border-radius:15px;text-align:center;font-size:1.5rem;">الإجمالي: <b>${total:.2f}</b></div>', unsafe_allow_html=True)
