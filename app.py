# 3. المعالجة الذكية للبيانات مع حماية ضد القوائم الفارغة
if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    if st.button("🚀 تحليل الإيصال واستخراج المتجر"):
        with st.spinner('جاري فحص المتجر والمنتجات...'):
            raw_output = analyze_receipt_v4(img_b64, api_key)
            
            # استخراج اسم المتجر بأمان
            store_match = re.search(r"STORE:\s*(.*)", raw_output)
            detected_store = store_match.group(1).strip() if store_match else "متجر غير معروف"
            
            items = []
            lines = raw_output.split('\n')
            for line in lines:
                # نمط البحث عن الاسم والسعر
                item_match = re.search(r"(.+?)[|:]\s*([\d.]+)", line)
                if item_match and "STORE" not in line.upper():
                    items.append({
                        "name": item_match.group(1).strip(),
                        "price": float(item_match.group(2)),
                        "store": detected_store,
                        "expiry": datetime.now() + timedelta(days=return_days)
                    })
            
            # حماية: لا نحفظ في session_state إلا إذا وجدنا منتجات فعلاً
            if items:
                st.session_state.temp_items = items
                st.session_state.detected_store_name = detected_store
            else:
                st.error("❌ لم نتمكن من قراءة المنتجات. تأكد أن الصورة واضحة وتحتوي على أسعار.")

# 4. مرحلة التعديل والنقل (مع حماية ضد IndexError)
if "temp_items" in st.session_state and st.session_state.temp_items:
    # استخدام اسم المتجر المحفوظ بأمان
    display_store = st.session_state.get('detected_store_name', 'غير معروف')
    st.subheader(f"📝 مراجعة مشتريات متجر: {display_store}")
    
    final_selection = []
    for i, item in enumerate(st.session_state.temp_items):
        c1, c2, c3 = st.columns([0.5, 3, 1.5])
        with c1: sel = st.checkbox("", key=f"s_{i}")
        with c2: name = st.text_input(f"n_{i}", item['name'], key=f"name_{i}", label_visibility="collapsed")
        with c3: price = st.number_input(f"p_{i}", value=item['price'], format="%.2f", key=f"price_{i}", label_visibility="collapsed")
        if sel: final_selection.append({"name": name, "price": price, "store": item['store'], "expiry": item['expiry']})
    
    if st.button("📥 إضافة المختار إلى قائمة المرتجعات"):
        if "refund_list" not in st.session_state: st.session_state.refund_list = []
        st.session_state.refund_list.extend(final_selection)
        st.success("تمت الإضافة!")
