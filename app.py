if uploaded_file and api_key:
    img_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    st.image(uploaded_file, caption="الإيصال المرفوع", width=300)

    if st.button("🚀 تحليل المشتريات الآن"):
        with st.spinner('جاري قراءة الإيصال وتحليل البيانات...'):
            try:
                raw_output = analyze_receipt_with_ai(img_b64, api_key)
                
                # إظهار النص الخام للتأكد من القراءة (لأغراض التصحيح)
                with st.expander("إظهار النص المستخرج من الـ AI"):
                    st.write(raw_output)
                
                # تحويل النص إلى قائمة كائنات بطريقة أكثر مرونة
                items = []
                # تقسيم النص بناءً على الأسطر
                lines = raw_output.strip().split('\n')
                
                for line in lines:
                    # محاولة البحث عن اسم وسعر بأي تنسيق (اسم | سعر) أو (اسم : سعر)
                    match = re.search(r"(.+?)[|:]\s*([\d,]+\.?\d*)", line)
                    if match:
                        name = match.group(1).strip()
                        price_str = match.group(2).replace(',', '') # إزالة الفواصل لو وجدت
                        items.append({"name": name, "price": float(price_str)})
                
                if items:
                    st.session_state.current_items = items
                    st.success(f"تم استخراج {len(items)} منتجات بنجاح!")
                else:
                    st.warning("تمت القراءة ولكن لم نتمكن من تنسيق البيانات تلقائياً. تأكد من وضوح السعر في الصورة.")
                    st.info("النص المستخرج كان: " + raw_output)
                    
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحليل: {str(e)}")
