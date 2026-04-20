import streamlit as st
import base64
import requests
import re

# إعدادات الواجهة (ألوان WhatsApp و Cash App)
st.set_page_config(page_title="مدير المرتجعات الذكي", page_icon="🟢")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { background-color: #25D366; color: white; border-radius: 12px; font-weight: bold; }
    .stTextInput>div>div>input { background-color: white; border: 1px solid #25D366; }
    .refund-card { background-color: #e3fcef; padding: 15px; border-radius: 10px; border-right: 5px solid #25D366; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🟢 معالج المرتجعات المرن")

# إدارة المفتاح من Secrets
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    with st.sidebar:
        api_key = st.text_input("أدخل OpenAI API Key:", type="password")

uploaded_file = st.file_uploader("ارفع صورة الإيصال من المعرض", type=['jpg', 'jpeg', 'png'])

def analyze_receipt(image_b64, key):
    headers = {"Authorization": f"Bearer {key}"}
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
    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
    return response.json()['choices'][0]['message']['content']

if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    
    if st.button("🚀 قراءة بيانات الإيصال"):
        with st.spinner('جاري تحليل الصورة...'):
            raw_output = analyze_receipt(img_b64, api_key)
            items = []
            for line in raw_output.split('\n'):
                match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                if match:
                    items.append({"name": match.group(1).strip(), "price": float(match.group(2))})
            st.session_state.temp_items = items

# 1. مرحلة التدقيق والتعديل
if "temp_items" in st.session_state:
    st.divider()
    st.subheader("📝 راجع وعدل البيانات المستخرجة:")
    
    updated_items = []
    for i, item in enumerate(st.session_state.temp_items):
        col1, col2, col3 = st.columns([0.5, 3, 1.5])
        with col1:
            selected = st.checkbox("", key=f"sel_{i}")
        with col2:
            new_name = st.text_input(f"المنتج {i+1}", item['name'], key=f"name_{i}")
        with col3:
            new_price = st.number_input(f"السعر {i+1}", value=item['price'], format="%.2f", key=f"price_{i}")
        
        if selected:
            updated_items.append({"name": new_name, "price": new_price})

    if st.button("📥 نقل العناصر المختارة إلى قائمة المرتجعات"):
        if updated_items:
            st.session_state.refund_list = updated_items
            st.success(f"تم نقل {len(updated_items)} عنصر إلى القائمة!")
        else:
            st.warning("يرجى تحديد عنصر واحد على الأقل.")

# 2. عرض قائمة المرتجعات النهائية
if "refund_list" in st.session_state:
    st.divider()
    st.subheader("📋 قائمة المرتجعات النهائية")
    
    total_refund = 0.0
    for item in st.session_state.refund_list:
        st.markdown(f"""
            <div class="refund-card">
                <b>{item['name']}</b> <br> 
                <span style="color: #075E54;">المبلغ: ${item['price']:.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        total_refund += item['price']
    
    st.metric("إجمالي مبلغ الإرجاع", f"${total_refund:.2f}")
    
    if st.button("✅ تأكيد القائمة النهائية"):
        st.balloons()
        st.success("تم حفظ قائمة المرتجعات بنجاح.")
