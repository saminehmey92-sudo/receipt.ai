import streamlit as st
import base64
import requests
import re

# 1. إعدادات الصفحة (يجب أن تكون أول أمر بعد الاستيراد)
st.set_page_config(page_title="المحلل الذكي", page_icon="🟢")

st.title("🟢 نظام استخراج المرتجعات")

# 2. تعريف المتغيرات من الواجهة (هنا نقوم بتعريفها قبل استخدامها)
with st.sidebar:
    # محاولة جلب المفتاح من Secrets أو طلبه يدوياً
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("أدخل OpenAI API Key:", type="password")

uploaded_file = st.file_uploader("ارفع صورة الإيصال", type=['jpg', 'jpeg', 'png'])

# 3. دالة التحليل
def analyze_receipt(image_b64, key):
    headers = {"Authorization": f"Bearer {key}"}
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract items and prices. Format: Item | Price"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
    return response.json()['choices'][0]['message']['content']

# 4. الآن نستخدم الشرط (بعد أن تم تعريف المتغيرات بالأعلى)
if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    st.image(uploaded_file, width=300)

    if st.button("🚀 تحليل الآن"):
        with st.spinner('جاري التحليل...'):
            raw_output = analyze_receipt(img_b64, api_key)
            
            # عرض النتائج
            items = []
            for line in raw_output.split('\n'):
                match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                if match:
                    items.append({"name": match.group(1).strip(), "price": float(match.group(2))})
            
            st.session_state.current_items = items

# 5. عرض القائمة التفاعلية
if "current_items" in st.session_state:
    total = 0.0
    for i, item in enumerate(st.session_state.current_items):
        if st.checkbox(f"{item['name']} - ${item['price']}", key=f"it_{i}"):
            total += item['price']
    st.metric("إجمالي المرتجع", f"${total:.2f}")
