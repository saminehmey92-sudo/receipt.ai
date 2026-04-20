import streamlit as st
import base64
import requests
import re

st.set_page_config(page_title="المحلل الذكي", page_icon="🟢")

st.title("🟢 نظام استخراج المرتجعات")

with st.sidebar:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("أدخل OpenAI API Key:", type="password")

uploaded_file = st.file_uploader("ارفع صورة الإيصال", type=['jpg', 'jpeg', 'png'])

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
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        res_json = response.json()
        
        # فحص وجود خطأ في الاستجابة
        if "error" in res_json:
            return f"API_ERROR: {res_json['error']['message']}"
            
        return res_json['choices'][0]['message']['content']
    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    st.image(uploaded_file, width=300)

    if st.button("🚀 تحليل الآن"):
        with st.spinner('جاري التحليل...'):
            raw_output = analyze_receipt(img_b64, api_key)
            
            # فحص إذا كان هناك خطأ تقني
            if "API_ERROR" in raw_output or "SYSTEM_ERROR" in raw_output:
                st.error(raw_output)
            else:
                items = []
                for line in raw_output.split('\n'):
                    match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                    if match:
                        items.append({"name": match.group(1).strip(), "price": float(match.group(2))})
                
                if items:
                    st.session_state.current_items = items
                    st.success("تم استخراج البيانات!")
                else:
                    st.warning("لم يتم العثور على بيانات واضحة. تأكد من جودة الصورة.")

if "current_items" in st.session_state:
    st.write("---")
    total = 0.0
    for i, item in enumerate(st.session_state.current_items):
        if st.checkbox(f"{item['name']} - ${item['price']}", key=f"it_{i}"):
            total += item['price']
    st.metric("إجمالي المرتجع", f"${total:.2f}")
