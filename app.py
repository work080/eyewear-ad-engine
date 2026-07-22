import streamlit as st

# 頁面設定：自動適應電腦與手機螢幕
st.set_page_config(page_title="品牌廣告視覺生成引擎", page_icon="👓", layout="centered")

st.title("👓 品牌廣告視覺生成引擎 (眼鏡專用版)")
st.caption("結合眼鏡型號、尺寸與特殊功能，自動生成「畫面優先」的廣告級 AI 提示詞")

# 1. 視覺邏輯字典（將眼鏡類型與特色轉換為視覺亮點）
VISUAL_MAP = {
    "偏光": "split-frame visual contrast showing harsh blinding reflections vs crystal clear glare-free vision through polarized lens",
    "無偏光": "crystal clear optical glass clarity with subtle natural reflections, pure transparent look",
    "老花眼鏡": "macro focus shot, sharp micro-text visible clearly through lens, warm soft reading ambient lighting",
    "護目鏡": "high-impact protective shield visual, wrap-around side defense, dust-proof airflow particles around frame",
    "輕量": "featherweight floating in mid-air, surrounded by delicate soft white floating feathers, weightless aerial effect",
    "柔軟": "extreme flexibility curvature, supple bending form, smooth natural wave contours, soft texture micro-details",
    "防霧": "visible clear airflow lines passing through lenses, sharp edge control, breathability visual stream",
    "耐用": "material micro cross-section, precision cut edges, high-impact resistant surface texture",
    "抗UV": "intense golden sunlight beaming, luminous protective edge light, high contrast shadow",
    "防水/水花": "dynamic water splashing droplets frozen in high speed, crystal clear fluid motion"
}

# 2. 表單介面
with st.form("ad_form"):
    st.subheader("1. 基本資訊與眼鏡類型")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        product_name = st.text_input("📦 商品名稱 / 品名", placeholder="例：極光系列 太陽眼鏡")
    with col_p2:
        model_number = st.text_input("🏷️ 型號", placeholder="例：EG-2026X")

    eyewear_type = st.radio(
        "👓 眼鏡主要功能類型",
        options=["偏光", "無偏光", "老花眼鏡", "護目鏡"],
        horizontal=True
    )

    st.subheader("2. 尺寸與重量規格（轉化為精密特寫細節）")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        total_width = st.text_input("總鏡寬 (mm)", placeholder="142")
        bridge_width = st.text_input("鼻寬 (mm)", placeholder="18")
    with col_s2:
        lens_width = st.text_input("單片鏡寬 (mm)", placeholder="55")
        temple_length = st.text_input("鏡腳長度 (mm)", placeholder="145")
    with col_s3:
        lens_height = st.text_input("單片鏡高 (mm)", placeholder="48")
        weight = st.text_input("重量 (g)", placeholder="18")

    st.subheader("3. 視覺特效與功能特點")
    selected_features = st.multiselect(
        "✨ 選擇視覺亮點（自動轉換為特效與氛圍）",
        options=["輕量", "柔軟", "防霧", "耐用", "抗UV", "防水/水花"],
        default=["輕量", "抗UV"]
    )

    custom_features = st.text_area(
        "📝 眼鏡與鏡片特殊功能填寫",
        placeholder="例如：防藍光鍍膜、記憶鈦金屬鏡腳、變色鏡片、防刮防油污層、鍍金雙樑設計..."
    )

    scene_setting = st.text_input("🏞️ 使用情境背景（選填）", placeholder="例如：清晨陽光照射的蔚藍海岸、極簡日系木質展台")

    submitted = st.form_submit_button("🚀 生成品牌廣告視覺 Prompt", type="primary", use_container_width=True)

# 3. 邏輯運算與 Prompt 生成
if submitted:
    if not product_name:
        st.warning("⚠️ 請先輸入商品名稱！")
    else:
        # 組合眼鏡類型與視覺特色
        visual_keys = [eyewear_type] + selected_features
        feature_prompts = [VISUAL_MAP[k] for k in visual_keys if k in VISUAL_MAP]
        
        # 處理自訂補充功能
        if custom_features:
            feature_prompts.append(f"special lens and frame details: {custom_features}")
            
        # 處理尺寸與重量規格，加入鏡框細節提示
        size_specs = []
        if total_width and lens_width and lens_height:
            size_specs.append(f"precision proportions with {total_width}mm frame width and {lens_width}x{lens_height}mm lens dimensions")
        if weight:
            size_specs.append(f"ultra-lightweight build weighing only {weight}g")
            
        spec_text = f"Custom engineered eyewear, {', '.join(size_specs)}." if size_specs else "Precision engineered eyewear with sharp geometry."

        visual_highlights = ", ".join(feature_prompts)
        env_prompt = scene_setting if scene_setting else "high-end luxury studio atmosphere with soft gradient background lighting"

        # 構建廣告級 Prompt
        full_prompt = (
            f"A high-end commercial advertising photograph for {product_name} (Model: {model_number if model_number else 'Exclusive'}). "
            f"The primary visual hero is the eyewear, dynamically angled with shallow depth of field. {spec_text} "
            f"Key visual highlight & optical effects: {visual_highlights}. "
            f"Lighting & Atmosphere: Luminous rim lighting on frame edges, high-contrast reflections, extreme macro detail on material texture. "
            f"Environment: {env_prompt}. "
            f"NO TEXT, no typography, no logo, pure visual advertising composition, photorealistic, 8k resolution, award-winning shot."
        )

        st.success("🎉 生成成功！點擊右上角按鈕即可複製 Prompt 貼至 AI 繪圖工具：")
        st.code(full_prompt, language="text")
