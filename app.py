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

# --- 1. إعدادات الواجهة والتصميم ---
st.set_page_config(page_title="Return Manager Pro", page_icon="📲", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; background-color: #f4f7f6; }
    .main-header {
        background: linear-gradient(135deg, #075E54 0%, #25D366 100%);
        padding: 2rem; border-radius: 0 0 30px 30px;
        color: white; text-align: center; margin-bottom: 2rem;
    }
    .final-card {
        background: white; padding: 15px; border-radius: 20px; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center;
        border-right: 8px solid #25D366; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .price-tag { background: #e3fcef; color: #075E54; padding: 5px 12px; border-radius: 10px; font-weight: bold; }
    .stButton>button { border-radius: 12px; font-weight: bold; transition: 0.3s; }
    /* تنسيق زر تم الاسترداد */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background-color: #e3fcef !important; color: #075E54 !important; border: 1px solid #25D366 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- تهيئة مخازن البيانات ---
if "refund_list" not in st.session_state: st.session_state.refund_list = []
if "archived_refunds" not in st.session_state: st.session_state.archived_refunds = []

# --- 2. التنقل بين الصفحات ---
page = st.sidebar.selectbox("القائمة الرئيسية", ["🏠 الإضافات النشطة", "📊 سجل الاستردادات الشهرية"])

# --- الصفحة الأولى: الإضافات النشطة ---
if page == "🏠 الإضافات النشطة":
    st.markdown('<div class="main-header"><h1>📲 Return Manager Pro</h1><p>إدارة المرتجعات النشطة</p></div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        api_key = st.secrets.get("OPENAI_API_KEY", "") or st.text_input("أدخل مفتاح OpenAI:", type="password")
        return_days = st.select_slider("مهلة الاسترجاع", options=[7, 14, 30, 45, 60, 90], value=30)

    col_u, col_p = st.columns([1, 1])
    with col_u:
        uploaded_file = st.file_uploader("📸 ارفع الإيصال", type=['jpg', 'jpeg', 'png', 'webp', 'avif', 'heic'])
        if uploaded_file and api_key:
            try:
                image = Image.open(uploaded_file)
                if image.mode != "RGB": image = image.convert("RGB")
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG', quality=95)
                img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
                if st.button("🔍 تحليل الإيصال"):
                    with st.spinner('جاري التحليل...'):
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        payload = {
                            "model": "gpt-4o",
                            "messages": [{"role": "user", "content": [
                                {"type": "text", "text": "Extract Store Name and items with prices. Format: STORE: [Name] ITEMS: Name | Price"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]}]
                        }
                        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                        res_json = response.json()
                        if 'choices' in res_json:
                            raw_output = res_json['choices'][0]['message']['content']
                            store_match = re.search(r"STORE:\s*(.*)", raw_output)
                            detected_store = store_match.group(1).strip() if store_match else "متجر غير معروف"
                            items = []
                            for line in raw_output.split('\n'):
                                m = re.search(r"(.+?)\s*[|:]\s*(\d+\.\d{2})", line)
                                if m and "STORE" not in line.upper():
                                    items.append({"name": m.group(1).strip(), "price": float(m.group(2)), "store": detected_store, "expiry": datetime.now() + timedelta(days=return_days)})
                            if items:
                                st.session_state.temp_items = items
                                st.session_state.current_store = detected_store
            except Exception as e: st.error(f"خطأ: {e}")

    with col_p:
        if uploaded_file: st.image(uploaded_file, use_column_width=True)

    # مراجعة المشتريات
    if "temp_items" in st.session_state:
        st.divider()
        st.subheader(f"📝 مراجعة: {st.session_state.current_store}")
        final_sel = []
        for i, item in enumerate(st.session_state.temp_items):
            c1, c2, c3 = st.columns([0.5, 3, 1.5])
            with c1: sel = st.checkbox("", key=f"tmp_{i}")
            with c2: name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}")
            with c3: price = st.number_input(f"p_{i}", value=item['price'], key=f"price_{i}")
            if sel: final_sel.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry'], "added_date": datetime.now()})
        
        if st.button("📥 إضافة للقائمة النشطة"):
            st.session_state.refund_list.extend(final_sel)
            del st.session_state.temp_items
            st.rerun()

    # عرض القائمة النشطة
    if st.session_state.refund_list:
        st.divider()
        st.header("🛒 المرتجعات النشطة")
        for i, item in enumerate(st.session_state.refund_list):
            days_left = (item['expiry'] - datetime.now()).days
            st.markdown(f"""
                <div class="final-card">
                    <div><b>{item['name']}</b><br><small>🏢 {item['store']} | ⏳ متبقي {max(0, days_left)} يوم</small></div>
                    <div class="price-tag">${item['price']:.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # أزرار الإجراءات بجانب بعضها
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("✅ تم الاسترداد", key=f"done_{i}"):
                    # إضافة للأرشيف مع تاريخ اليوم
                    archived_item = item.copy()
                    archived_item["refund_date"] = datetime.now()
                    st.session_state.archived_refunds.append(archived_item)
                    # حذف من النشطة
                    st.session_state.refund_list.pop(i)
                    st.success(f"تم نقل {item['name']} إلى السجل الشهري!")
                    st.rerun()
            with btn_col2:
                if st.button("❌ حذف", key=f"del_{i}"):
                    st.session_state.refund_list.pop(i)
                    st.rerun()

# --- الصفحة الثانية: سجل الاستردادات الشهرية ---
elif page == "📊 سجل الاستردادات الشهرية":
    st.markdown('<div class="main-header"><h1>📊 سجل الاستردادات</h1><p>تتبع نجاحك المالي شهرياً</p></div>', unsafe_allow_html=True)
    
    if not st.session_state.archived_refunds:
        st.info("لا توجد مبالغ مستردة مؤرشفة بعد. اضغط على 'تم الاسترداد' في القائمة الرئيسية.")
    else:
        # تجميع البيانات حسب الشهر
        monthly_data = {}
        for item in st.session_state.archived_refunds:
            month_key = item['refund_date'].strftime("%B %Y") # مثال: April 2026
            if month_key not in monthly_data: monthly_data[month_key] = []
            monthly_data[month_key].append(item)
        
        for month, items in monthly_data.items():
            with st.expander(f"📅 شهر {month}", expanded=True):
                month_total = sum(it['price'] for it in items)
                st.metric("إجمالي المستردات لهذا الشهر", f"${month_total:.2f}")
                
                # عرض جدول بالتفاصيل
                st.table([{
                    "التاريخ": it['refund_date'].strftime("%Y-%m-%d"),
                    "المتجر": it['store'],
                    "المادة": it['name'],
                    "المبلغ": f"${it['price']:.2f}"
                } for it in items])
        
        if st.button("🗑️ مسح السجل بالكامل"):
            st.session_state.archived_refunds = []
            st.rerun()
