import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="品牌廣告視覺生成引擎 (眼鏡專用版)",
    page_icon="👓",
    layout="centered"
)

st.title("👓 品牌廣告視覺生成引擎 (眼鏡專用版)")
st.caption("結合眼鏡型號、尺寸與特殊功能，自動生成「畫面優先」的廣告級 AI 提示詞")

st.divider()

# --- 1. 基本資訊與眼鏡類型 ---
st.subheader("1. 基本資訊與眼鏡類型")
col1, col2 = st.columns(2)
with col1:
    product_name = st.text_input("📦 商品名稱 / 品名", placeholder="例：極光系列 太陽眼鏡")
with col2:
    model_num = st.text_input("🏷️ 型號", placeholder="例：EG-2026X")

# 1. 改為複選，新增：變色片、雪鏡、運動型護目鏡、折疊眼鏡
func_types = st.multiselect(
    "👓 眼鏡主要功能類型（可複選）",
    options=["偏光", "無偏光", "老花眼鏡", "護目鏡", "變色片", "雪鏡", "運動型護目鏡", "折疊眼鏡"],
    default=["偏光"]
)

# --- 2. 尺寸與重量規格 ---
st.subheader("2. 尺寸與重量規格（轉化為精密特寫細節）")
col_s1, col_s2, col_s3 = st.columns(3)

# 2. 尺寸單位全部更換為 cm
with col_s1:
    total_width = st.text_input("總鏡寬 (cm)", value="14.2")
with col_s2:
    lens_width = st.text_input("單片鏡寬 (cm)", value="5.5")
with col_s3:
    lens_height = st.text_input("單片鏡高 (cm)", value="4.8")

col_s4, col_s5, col_s6 = st.columns(3)
with col_s4:
    bridge_width = st.text_input("鼻寬 (cm)", value="1.8")
with col_s5:
    temple_len = st.text_input("鏡腳長度 (cm)", value="14.5")
with col_s6:
    weight = st.text_input("重量 (g)", value="18")

# --- 3. 視覺特效與功能特點 ---
st.subheader("3. 視覺特效與功能特點")

# 3. 新增：濾藍光、防紫外線、防刮、感光變色
visual_highlights = st.multiselect(
    "✨ 選擇視覺亮點（自動轉換為特效與氛圍）",
    options=[
        "輕量", "抗UV", "濾藍光", "防紫外線", "防刮", "感光變色", 
        "高透光", "耐衝擊", "防霧", "反光鏡面", "記憶金屬"
    ],
    default=["輕量", "抗UV", "濾藍光"]
)

extra_features = st.text_area(
    "📝 眼鏡與鏡片特殊功能補充說明",
    placeholder="例如：高科技記憶鈦金屬鏡框、100% 阻隔有害光、適合戶外極限運動...",
    height=80
)

# --- 4. 使用背景與情境（修復與優化） ---
st.subheader("4. 🏞️ 使用背景與情境（選填）")
bg_presets = st.multiselect(
    "快速選擇拍攝場景氛圍",
    options=["陽光海灘", "都市街頭", "商務辦公室", "雪地極光", "戶外騎行/運動", "攝影棚極簡高光", "夜間駕駛"],
    default=["陽光海灘"]
)
custom_bg = st.text_input("或自訂特定場景描述", placeholder="例如：北歐雪山日出時的金色光影，極致科技質感背景")

# --- 5. 提示詞生成邏輯 ---
st.divider()

if st.button("🚀 生成 AI 廣告圖片提示詞 (Prompt)", type="primary"):
    # 組合類型與背景
    type_str = ", ".join(func_types) if func_types else "通用眼鏡"
    highlights_str = ", ".join(visual_highlights) if visual_highlights else ""
    
    bg_list = list(bg_presets)
    if custom_bg.strip():
        bg_list.append(custom_bg.strip())
    bg_combined = ", ".join(bg_list) if bg_list else "極簡商業攝影棚"

    # 生成英文提示詞 (適用於 Midjourney / Flux / DALL-E / Gemini)
    prompt_en = f"Commercial product photography for eyewear ({product_name if product_name else 'sunglasses'}, model {model_num if model_num else 'Pro'}). "
    prompt_en += f"Eyewear types: {type_str}. "
    
    if highlights_str:
        prompt_en += f"Key visual characteristics & special effects: {highlights_str}. "
    
    # 尺寸特寫轉化 (cm)
    prompt_en += f"Precise specifications: total width {total_width}cm, lens size {lens_width}x{lens_height}cm, bridge {bridge_width}cm, temple {temple_len}cm, ultralight {weight}g. "
    
    prompt_en += f"Setting & background atmosphere: {bg_combined}. "
    
    if extra_features.strip():
        prompt_en += f"Additional features: {extra_features.strip()}. "

    prompt_en += "Macro close-up shot, crystal clear lenses, high-end studio lighting, sharp focus, 8k resolution, professional advertising quality, hyper-realistic."

    # 中文輔助說明
    prompt_zh = f"【商品名稱】{product_name} ({model_num})\n"
    prompt_zh += f"【功能類型】{type_str}\n"
    prompt_zh += f"【尺寸規格】總寬 {total_width}cm / 鏡寬 {lens_width}cm / 鏡高 {lens_height}cm / 鼻寬 {bridge_width}cm / 鏡腳 {temple_len}cm / 重 {weight}g\n"
    prompt_zh += f"【視覺亮點】{highlights_str}\n"
    prompt_zh += f"【背景場景】{bg_combined}\n"
    if extra_features.strip():
        prompt_zh += f"【補充功能】{extra_features.strip()}\n"

    st.success("🎉 生成成功！請複製以下提示詞使用：")
    
    st.subheader("🎨 AI 繪圖 Prompt (英文 - Midjourney / Flux)")
    st.code(prompt_en, language="text")
    
    st.subheader("📋 廣告文案亮點摘要 (中文)")
    st.text_area("可直接作為社群貼文或文案參考：", value=prompt_zh, height=180)
