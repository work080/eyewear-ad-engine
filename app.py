import streamlit as st
import requests
import io
from PIL import Image

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡品牌廣告生成引擎 (實照極速版)",
    page_icon="👓",
    layout="centered"
)

st.title("👓 眼鏡品牌廣告視覺生成引擎")
st.caption("📷 上傳實拍照 ➔ 🎯 選擇單一視覺亮點 ➔ 🚀 自動生成不變形的品牌廣告圖 Prompt")

st.divider()

# --- 側邊欄：Hugging Face 免費 API 金鑰設定 ---
with st.sidebar:
    st.header("🔑 免費 API Key 設定")
    hf_token = st.text_input(
        "Hugging Face Token (免費選填)", 
        type="password",
        help="填入 Token 即可在網頁直接使用 FLUX.1 生圖！"
    )
    st.markdown(
        """
        **💡 無 Token 也能使用！**  
        您可以直接複製系統產出的「保真 Prompt」到 ChatGPT、Midjourney 或 Bing 直接生圖。
        """
    )

# --- 1. 商品實拍照上傳區 ---
st.subheader("1. 📸 上傳商品實拍照")
uploaded_file = st.file_uploader("請選擇眼鏡實拍照（系統將作為實物參考標的）", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="已載入實拍照（將保持此眼鏡型態不變形）", width=320)

# --- 2. 選擇本張圖片的單一視覺亮點 ---
st.subheader("2. 🎯 本張圖片的核心視覺亮點（單選，保持資訊乾淨）")

spotlight_dict = {
    "抗 UV": "陽光/光線折射/UV保護罩光影特效，突出抗紫外線功能",
    "防霧": "細微氣流/透氣流線/霧氣蒸散質感，展現鏡片清晰度",
    "輕量": "電子秤/羽毛懸浮/微浮空漂浮感，展現極致輕盈",
    "柔軟/記憶金屬": "鏡腳彎折示意/柔和韌性曲線，展現耐壓材質",
    "偏光": "前後對比/眩光控制/水面強光消除視覺特效",
    "耐用/材質": "金屬與鏡片切面特寫/高品質工藝細節放大",
    "生活使用情境": "真實人物佩戴/質感街頭/時尚氛圍拍攝"
}

selected_spotlight = st.radio(
    "請選擇這張圖要傳達的「唯一亮點」：",
    options=list(spotlight_dict.keys()),
    index=0
)
st.info(f"💡 **視覺手法建議**：{spotlight_dict[selected_spotlight]}")

# --- 3. 構圖與視覺藝術規範 ---
st.subheader("3. 📐 廣告構圖與空間質感設定")
col_c1, col_c2 = st.columns(2)

with col_c1:
    composition_style = st.multiselect(
        "選擇構圖手法（可多選）",
        options=["留白極簡", "斜角構圖", "前後景深度", "景深虛化", "光影對比", "空間層次感"],
        default=["留白極簡", "景深虛化", "空間層次感"]
    )

with col_c2:
    bg_scene = st.selectbox(
        "拍攝背景與氛圍",
        options=["攝影棚高級冷灰", "溫暖陽光沙灘", "都市時尚街頭", "北歐極簡木質", "高科技質感展台"]
    )

# --- 4. 產品 basic 規格（選填） ---
st.subheader("4. 📋 商品基本規格（選填）")
col_p1, col_p2 = st.columns(2)
with col_p1:
    product_name = st.text_input("商品名稱/型號", value="極光系列 EG-2026")
with col_p2:
    specs_text = st.text_input("尺寸簡述", value="總寬14.2cm / 單片鏡寬5.5cm / 重18g")

st.divider()

# --- 5. 生成 Prompt 與防變形指令 ---
if uploaded_file or st.button("🚀 生成廣告圖片 Prompt", type="primary"):
    
    # 建立強化的英文 Prompt（加入「嚴禁商品變形」核心指令）
    comp_str = ", ".join(composition_style) if composition_style else "balanced composition"
    
    prompt_en = (
        f"High-end commercial product advertisement photography of {product_name}. "
        f"CRITICAL REQUIREMENT: MUST strictly match the exact eyewear shape, frame structure, lens color, and proportions from the reference photo, zero distortion, zero alteration of product identity. "
        f"Single core visual focus: {selected_spotlight} ({spotlight_dict[selected_spotlight]}). "
        f"Composition & atmosphere: {comp_str}, clean negative space, minimal uncluttered layout, master lighting, sharp focus on eyewear details, {bg_scene} background. "
        f"8k resolution, photorealistic, professional brand ad aesthetic, ultra-clean commercial look."
    )

    st.success("🎉 Prompt 已自動組合完成！")

    # 展示英文 Prompt
    st.subheader("🎨 AI 繪圖專用 Prompt (英文)")
    st.code(prompt_en, language="text")

    # 提示使用者圖生圖技巧
    st.markdown(
        """
        > 📌 **防變形秘訣（圖生圖 Image-to-Image）**：  
        > 若使用 **ChatGPT / Midjourney**，請上傳原圖並加上這段 Prompt；若使用 **Midjourney**，建議加參數 `--cw 100` 或以 `Image Prompt` 貼上原圖網址，就能 100% 保持眼鏡不變形！
        """
    )

    # 如果有輸入 Hugging Face Token，提供直接生圖
    st.subheader("🖼️ FLUX.1 一鍵免費生成圖片")
    if st.button("✨ 立即繪製廣告圖"):
        if not hf_token:
            st.warning("⚠️ 請在左側欄填入 Hugging Face Free Token 即可開啟免費直接出圖！")
        else:
            with st.spinner("🤖 FLUX.1 正在生成廣告圖中，請稍候 10~15 秒..."):
                API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
                headers = {"Authorization": f"Bearer {hf_token.strip()}"}
                
                try:
                    response = requests.post(API_URL, headers=headers, json={"inputs": prompt_en}, timeout=60)
                    if response.status_code == 200:
                        image_bytes = response.content
                        generated_img = Image.open(io.BytesIO(image_bytes))
                        st.image(generated_img, caption="FLUX.1 生成成果", use_container_width=True)
                        
                        st.download_button(
                            label="📥 下載高畫質廣告圖",
                            data=image_bytes,
                            file_name=f"eyewear_ad_{selected_spotlight}.png",
                            mime="image/png"
                        )
                    else:
                        st.error(f"❌ 生成失敗，請確認 Token 或稍後再試。({response.status_code})")
                except Exception as e:
                    st.error(f"❌ 連線失敗：{str(e)}")
