import streamlit as st
import base64
import requests
import re
import io
from datetime import datetime, timedelta
from PIL import Image
import pillow_avif  # دعم AVIF
from pillow_heif import register_heif_opener # دعم آيفون HEIC

# تفعيل دعم HEIC
register_heif_opener()

# --- 1. إعدادات الواجهة (تحسينات الموبايل) ---
st.set_page_config(page_title="Return Manager Pro", page_icon="📲", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; background-color: #f4f7f6; }
    
    /* رأس الصفحة للموبايل */
    .main-header {
        background: linear-gradient(135deg, #075E54 0%, #25D366 100%);
        padding: 1.5rem; border-radius: 0 0 25px 25px;
        color: white; text-align: center; margin-bottom: 1.5rem;
    }

    /* بطاقات المرتجعات */
    .final-card {
        background: white; padding: 15px; border-radius: 18px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
        border-right: 6px solid #25D366; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .price-tag { background: #e3fcef; color: #075E54; padding: 4px 10px; border-radius: 8px; font-weight: bold; }
    
    /* أزرار ضخمة للموبايل */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.2rem;
        background-color: #25D366 !important; color: white !important; font-weight: bold;
    }
    
    .notification-setting {
        background: white; padding: 15px; border-radius: 15px; margin-bottom: 10px;
        border-left: 5px solid #075E54;
    }
    </style>
""", unsafe_allow_html=True)

# --- تهيئة مخازن البيانات ---
if "refund_list" not in st.session_state: st.session_state.refund_list = []
if "archived_refunds" not in st.session_state: st.session_state.archived_refunds = []
if "global_notifications" not in st.session_state: st.session_state.global_notifications = True

# --- 2. القائمة الرئيسية (بند التنبيهات أصبح أساسياً) ---
page = st.sidebar.radio("📱 القائمة الرئيسية", ["🏠 المرتجعات والمهام", "🔔 إدارة التنبيهات", "📊 السجل الشهري"])

# --- الصفحة الأولى: المرتجعات والمهام ---
if page == "🏠 المرتجعات والمهام":
    st.markdown('<div class="main-header"><h1>📲 Return Manager</h1><p>إدارة مرتجعاتك بذكاء</p></div>', unsafe_allow_html=True)
    
    # تنبيهات سريعة في الأعلى (فقط إذا كانت مفعلة عالمياً)
    if st.session_state.global_notifications:
        for it in st.session_state.refund_list:
            days = (it['expiry'] - datetime.now()).days
            if days <= 3 and it.get('notify', True):
                st.warning(f"⏰ تنبيه عاجل: {it['name']} تنتهي قريباً!")

    col_u, col_p = st.columns([1, 1])
    with col_u:
        uploaded_file = st.file_uploader("📸 ارفع إيصال (iPhone, AVIF, JPG)", type=['jpg', 'jpeg', 'png', 'webp', 'avif', 'heic'])
        if uploaded_file:
            api_key = st.secrets.get("OPENAI_API_KEY", "") or st.sidebar.text_input("OpenAI Key:", type="password")
            if api_key and st.button("🔍 تحليل الإيصال الآن"):
                try:
                    image = Image.open(uploaded_file)
                    if image.mode != "RGB": image = image.convert("RGB")
                    buf = io.BytesIO()
                    image.save(buf, format='JPEG', quality=90)
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o",
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": "Extract Store Name and items with prices. Format: STORE: [Name] ITEMS: Name | Price"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]}]
                    }
                    res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers).json()
                    raw = res['choices'][0]['message']['content']
                    store = re.search(r"STORE:\s*(.*)", raw).group(1) if re.search(r"STORE:\s*(.*)", raw) else "متجر غير معروف"
                    
                    items = []
                    for line in raw.split('\n'):
                        m = re.search(r"(.+?)\s*[|:]\s*(\d+\.\d{2})", line)
                        if m and "STORE" not in line.upper():
                            items.append({"name": m.group(1).strip(), "price": float(m.group(2)), "store": store, "expiry": datetime.now() + timedelta(days=30), "notify": True})
                    st.session_state.temp_items = items
                    st.session_state.current_store = store
                except: st.error("فشل التحليل، تأكد من وضوح الصورة.")

    # مراجعة وإضافة
    if "temp_items" in st.session_state:
        st.divider()
        st.subheader(f"📍 متجر: {st.session_state.current_store}")
        final = []
        for i, item in enumerate(st.session_state.temp_items):
            c1, c2, c3 = st.columns([0.5, 3, 1.5])
            with c1: sel = st.checkbox("", key=f"t_{i}")
            with c2: name = st.text_input(f"n_{i}", item['name'], key=f"nm_{i}")
            with c3: prc = st.number_input(f"p_{i}", value=item['price'], key=f"pr_{i}")
            if sel: final.append({"name": name, "price": prc, "store": item['store'], "expiry": item['expiry'], "notify": True})
        
        if st.button("📥 حفظ وتفعيل التنبيهات"):
            st.session_state.refund_list.extend(final)
            del st.session_state.temp_items
            st.rerun()

    # القائمة النشطة
    if st.session_state.refund_list:
        st.divider()
        for i, item in enumerate(st.session_state.refund_list):
            days = (item['expiry'] - datetime.now()).days
            st.markdown(f'<div class="final-card" style="border-right-color: {"#FF3B30" if days < 5 else "#25D366"}"><div><b>{item['name']}</b><br><small>🏢 {item['store']} | ⏳ {max(0, days)} يوم</small></div><div class="price-tag">${item['price']:.2f}</div></div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ استرداد", key=f"ok_{i}"):
                    item['refund_date'] = datetime.now()
                    st.session_state.archived_refunds.append(item)
                    st.session_state.refund_list.pop(i)
                    st.rerun()
            with col2:
                if st.button("❌ حذف", key=f"x_{i}"):
                    st.session_state.refund_list.pop(i)
                    st.rerun()

# --- الصفحة الثانية: إدارة التنبيهات (البند الجديد) ---
elif page == "🔔 إدارة التنبيهات":
    st.markdown('<div class="main-header"><h1>🔔 مركز التنبيهات</h1><p>تحكم في إشعارات هاتفك</p></div>', unsafe_allow_html=True)
    
    st.session_state.global_notifications = st.toggle("تفعيل الإشعارات العامة على الهاتف", value=st.session_state.global_notifications)
    st.info("عند تفعيل هذا الخيار، سيرسل التطبيق تنبيهات دورية لنظام تشغيل الموبايل.")
    
    st.divider()
    st.subheader("🛠️ تخصيص تنبيهات المهام")
    
    if not st.session_state.refund_list:
        st.info("لا توجد مهام نشطة لتخصيص تنبيهاتها.")
    else:
        for i, item in enumerate(st.session_state.refund_list):
            with st.container():
                st.markdown(f'<div class="notification-setting">', unsafe_allow_html=True)
                col_txt, col_tog = st.columns([3, 1])
                with col_txt:
                    st.write(f"**{item['name']}**")
                    st.caption(f"متجر: {item['store']} | ينتهي في: {item['expiry'].strftime('%Y-%m-%d')}")
                with col_tog:
                    item['notify'] = st.toggle("تنبيه", value=item.get('notify', True), key=f"tog_{i}")
                st.markdown('</div>', unsafe_allow_html=True)

# --- الصفحة الثالثة: السجل الشهري ---
elif page == "📊 السجل الشهري":
    st.markdown('<div class="main-header"><h1>📊 السجل المالي</h1><p>المبالغ التي نجحت في استردادها</p></div>', unsafe_allow_html=True)
    if not st.session_state.archived_refunds:
        st.info("السجل فارغ.")
    else:
        for item in st.session_state.archived_refunds:
            st.success(f"✅ {item['name']} - {item['store']} - ${item['price']}")
