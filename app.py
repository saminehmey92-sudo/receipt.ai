import streamlit as st
import base64
import requests
import re

# 1. الإعدادات والواجهة
st.set_page_config(page_title="مدير المرتجعات الذكي", page_icon="🟢")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { background-color: #25D366; color: white; border-radius: 12px; font-weight: bold; }
    .refund-card { background-color: #e3fcef; padding: 12px; border-radius: 8px; border-right: 5px solid #25D366; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🟢 معالج المرتجعات المرن")

# إدارة المفتاح
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("أدخل OpenAI API Key:", type="password")

uploaded_file = st.file_uploader("ارفع صورة الإيصال من المعرض", type=['jpg', 'jpeg', 'png'])

# 2. دالة الاتصال "المصفحة"
def analyze_receipt(image_b64, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract items and prices. Format: Item | Price. Return ONLY the list."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
        
        # التأكد من أن الاستجابة ناجحة وبتنسيق JSON
        if response.status_code != 200:
            return f"API_ERROR: {response.status_code} - {response.text}"
            
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

# 3. المعالجة
if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    
    if st.button("🚀 قراءة بيانات الإيصال"):
        with st.spinner('جاري تحليل الصورة...'):
            raw_output = analyze_receipt(img_b64, api_key)
            
            if "ERROR" in raw_output:
                st.error(f"فشل الاتصال: {raw_output}")
            else:
                items = []
                for line in raw_output.split('\n'):
                    match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                    if match:
                        items.append({"name": match.group(1).strip(), "price": float(match.group(2))})
                st.session_state.temp_items = items

# 4. مرحلة التعديل والتدقيق (تعديل السعر)
if "temp_items" in st.session_state:
    st.divider()
    st.subheader("📝 مراجعة وتعديل البيانات:")
    
    updated_items = []
    for i, item in enumerate(st.session_state.temp_items):
        col_check, col_name, col_price = st.columns([0.5, 3, 1.5])
        with col_check:
            selected = st.checkbox("", key=f"sel_{i}")
        with col_name:
            new_name = st.text_input(f"اسم {i}", item['name'], key=f"n_{i}", label_visibility="collapsed")
        with col_price:
            new_price = st.number_input(f"سعر {i}", value=item['price'], format="%.2f", key=f"p_{i}", label_visibility="collapsed")
        
        if selected:
            updated_items.append({"name": new_name, "price": new_price})

    if st.button("📥 نقل إلى قائمة المرتجعات"):
        if updated_items:
            st.session_state.refund_list = updated_items
            st.success("تم التجهيز!")
        else:
            st.warning("حدد عناصر أولاً")

# 5. عرض القائمة النهائية
if "refund_list" in st.session_state:
    st.divider()
    st.subheader("📋 القائمة النهائية للمرتجعات")
    total = sum(item['price'] for item in st.session_state.refund_list)
    
    for item in st.session_state.refund_list:
        st.markdown(f'<div class="refund-card"><b>{item["name"]}</b>: ${item["price"]:.2f}</div>', unsafe_allow_html=True)
    
    st.metric("الإجمالي المسترد", f"${total:.2f}")
    if st.button("✅ تأكيد وحفظ"):
        st.balloons()
