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
                {
                    "type": "text", 
                    "text": "Extract items and prices. ONLY output lines in this format: ItemName | Price. Example: Apple | 1.50. Skip total, tax, and discounts."
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
    return response.json()['choices'][0]['message']['content']

if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    
    if st.button("🚀 تحليل المشتريات بدقة عالية"):
        with st.spinner('جاري التدقيق في الأسعار...'):
            raw_output = analyze_receipt(img_b64, api_key)
            
            items = []
            for line in raw_output.split('\n'):
                # هذا النمط البرمجي (Regex) يبحث عن آخر رقم عشري في السطر لضمان أنه السعر
                match = re.findall(r"([\d]+\.[\d]{2})", line)
                if match:
                    price = float(match[-1]) # يأخذ آخر رقم (السعر) ويتجاهل أي أرقام قبله
                    name = line.split('|')[0].replace('-', '').strip()
                    items.append({"name": name, "price": price})
            
            st.session_state.current_items = items

# عرض القائمة الخضراء التفاعلية
if "current_items" in st.session_state:
    st.markdown("### ✅ اختر الأصناف المراد إرجاعها:")
    total_refund = 0.0
    for i, item in enumerate(st.session_state.current_items):
        # تصميم أنيق لكل صنف
        col_item, col_price = st.columns([3, 1])
        with col_item:
            if st.checkbox(f"{item['name']}", key=f"it_{i}"):
                total_refund += item['price']
        with col_price:
            st.write(f"**${item['price']:.2f}**")
            
    st.divider()
    st.metric("إجمالي المبلغ المسترد", f"${total_refund:.2f}")
