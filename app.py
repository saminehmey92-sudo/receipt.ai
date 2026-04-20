import streamlit as st
import base64
import requests
import re

# 1. إعدادات الهوية البصرية (ألوان WhatsApp و Cash App)
st.set_page_config(page_title="المحلل الذكي v3.0", page_icon="🟢", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; }
    .stButton>button { 
        background-color: #25D366; 
        color: white; 
        border-radius: 20px; 
        font-weight: bold; 
        width: 100%;
        border: none;
        height: 3em;
    }
    .stButton>button:hover { background-color: #128C7E; color: white; }
    .header-box { 
        background-color: #075E54; 
        padding: 20px; 
        border-radius: 15px; 
        color: white; 
        text-align: center;
        margin-bottom: 25px;
    }
    .metric-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #25D366;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>📸 نظام استخراج المرتجعات الذكي</h1><p>دقة فائقة باستخدام OpenAI Vision</p></div>', unsafe_allow_html=True)

# 2. إدارة مفتاح الـ API بأمان
# يحاول البرنامج أولاً القراءة من Secrets، وإذا لم يجدها يظهر حقل إدخال في الجانب
api_key = st.secrets.get("OPENAI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    if not api_key:
        api_key = st.text_input("أدخل OpenAI API Key الخاص بك:", type="password")
        st.warning("يرجى إدخال المفتاح لتفعيل قدرات الرؤية.")
    else:
        st.success("✅ تم ربط المفتاح السري بنجاح")
    st.write("---")
    st.info("هذا التطبيق يستخدم نموذج GPT-4o لتحليل الصور بدقة بشرية.")

# 3. واجهة رفع الملفات
uploaded_file = st.file_uploader("ارفع صورة الإيصال من المعرض (Gallery)", type=['jpg', 'jpeg', 'png'])

def analyze_receipt_with_ai(image_b64, key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Analyze this receipt image. Extract every purchased item and its price. Format the output strictly as: ItemName | Price. Example: Milk | 4.99. Do not include tax or totals, only individual items."
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }
        ],
        "max_tokens": 500
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

# 4. معالجة الصورة وعرض النتائج
if uploaded_file and api_key:
    # تحويل الصورة إلى Base64
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    st.image(uploaded_file, caption="الإيصال المرفوع", use_column_width=True)

    if st.button("🚀 تحليل المشتريات الآن"):
        with st.spinner('جاري قراءة الإيصال وتحليل البيانات...'):
            try:
                raw_output = analyze_receipt_with_ai(img_b64, api_key)
                
                # تحويل النص المستخرج إلى قائمة كائنات
                items = []
                for line in raw_output.split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        name = parts[0].strip()
                        # تنظيف السعر من أي رموز عملات
                        price_str = re.sub(r'[^\d.]', '', parts[1])
                        if price_str:
                            items.append({"name": name, "price": float(price_str)})
                
                st.session_state.current_items = items
                st.success("تم استخراج البيانات بنجاح!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحليل: {str(e)}")

# 5. عرض قائمة المرتجعات التفاعلية
if "current_items" in st.session_state and st.session_state.current_items:
    st.write("---")
    st.subheader("🛒 حدد المنتجات المراد إرجاعها:")
    
    total_refund = 0.0
    selected_count = 0
    
    for i, item in enumerate(st.session_state.current_items):
        # تصميم Checkbox لكل منتج
        if st.checkbox(f"{item['name']} — **${item['price']:.2f}**", key=f"item_{i}"):
            total_refund += item['price']
            selected_count += 1
    
    st.divider()
    
    # عرض النتيجة النهائية
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-container"><h4>المبلغ المسترد</h4><h2>${total_refund:.2f}</h2></div>', unsafe_allow_html=True)
    with col2:
        if total_refund > 0:
            if st.button("✅ تأكيد طلب المرتجع"):
                st.balloons()
                st.success(f"تم تسجيل طلب إرجاع لـ {selected_count} منتجات.")
