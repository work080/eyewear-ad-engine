import streamlit as st
import requests
import io
from PIL import Image

# 頁面基本設定
st.set_page_config(
    page_title="品牌廣告視覺生成引擎 (眼鏡專用版)",
    page_icon="👓",
    layout="centered"
)

st.title("👓 品牌廣告視覺生成引擎 (眼鏡專用版)")
st.caption("結合眼鏡規格與 AI 繪圖（FLUX.1），自動生成廣告圖片與英文 Prompt")

st.divider()

# --- 側邊欄：Hugging Face 免費 API 金鑰設定 ---
with st.sidebar:
    st.header("🔑 免費 API Key 設定")
    hf_token = st.text_input(
        "Hugging Face Token (免費)", 
        type="password",
        help="填入 Token 即可開啟免費直接生圖功能！"
    )
    st.markdown(
        """
        **如何取得免費 Token？（約 30 秒）**
        1. 註冊/登入 [Hugging Face](https://huggingface.co/)
        2. 進入 [Access Tokens 頁面](https://huggingface.co/settings/tokens)
        3. 點擊 **Create new token** $\\rightarrow$ 選擇 **Read** 權限，複製 Token 貼到此處即可！
        """
    )

# --- 1. 基本資訊與眼鏡類型 ---
st.subheader("1. 基本資訊與眼鏡類型")
col1, col2 = st.columns(2)
with col1:
    product_name = st.text_input("📦 商品名稱 / 品名", placeholder="例：極光系列 太陽眼鏡")
with col2:
    model_num = st.text_input("🏷️ 型號", placeholder="例：EG-2026X")

func_types = st.multiselect(
    "👓 眼鏡主要功能類型（可複選）",
    options=["偏光", "無偏光", "老花眼鏡", "護目鏡", "變色片", "雪鏡", "運動型護目鏡", "折疊眼鏡"],
    default=["偏光"]
)

# --- 2. 尺寸與重量規格 (cm) ---
st.subheader("2. 尺寸與重量規格（轉化為精密特寫細節）")
col_s1, col_s2, col_s3 = st.columns(3)

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

# --- 4. 使用背景與情境 ---
st.subheader("4. 🏞️ 使用背景與情境（選填）")
bg_presets = st.multiselect(
    "快速選擇拍攝場景氛圍",
    options=["陽光海灘", "都市街頭", "商務辦公室", "雪地極光", "戶外騎行/運動", "攝影棚極簡高光", "夜間駕駛"],
    default=["陽光海灘"]
)
custom_bg = st.text_input("或自訂特定場景描述", placeholder="例如：北歐雪山日出時的金色光影，極致科技質感背景")

# --- 5. 提示詞與生圖邏輯 ---
st.divider()

# 組合英文提示詞
type_str = ", ".join(func_types) if func_types else "eyewear"
highlights_str = ", ".join(visual_highlights) if visual_highlights else ""

bg_list = list(bg_presets)
if custom_bg.strip():
    bg_list.append(custom_bg.strip())
bg_combined = ", ".join(bg_list) if bg_list else "professional commercial studio photography"

prompt_en = f"Commercial product photo of eyewear ({product_name if product_name else 'sunglasses'}, model {model_num if model_num else 'Pro'}). "
prompt_en += f"Type: {type_str}. "
if highlights_str:
    prompt_en += f"Visual features: {highlights_str}. "
prompt_en += f"Dimensions: total width {total_width}cm, lens {lens_width}x{lens_height}cm, bridge {bridge_width}cm, temple {temple_len}cm, weight {weight}g. "
prompt_en += f"Setting background: {bg_combined}. "
if extra_features.strip():
    prompt_en += f"Extra details: {extra_features.strip()}. "
prompt_en += "Macro close-up shot, crystal clear lenses, high-end studio lighting, sharp focus, 8k resolution, hyper-realistic, advertising style."

# 顯示產出的 Prompt
st.subheader("🎨 AI 繪圖 Prompt (英文)")
st.code(prompt_en, language="text")

# 生圖按鈕
st.subheader("🖼️ AI 一鍵生成圖片 (FLUX.1)")

if st.button("🚀 生成 AI 廣告圖片", type="primary"):
    if not hf_token:
        st.warning("⚠️ 請先在左側欄（Sidebar）填入您的 Hugging Face Free Token 才能啟用免費出圖功能喔！")
    else:
        with st.spinner("🤖 FLUX.1 模型正在為您繪製高畫質眼鏡廣告圖，約需 10 ~ 20 秒..."):
            API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
            headers = {"Authorization": f"Bearer {hf_token.strip()}"}
            
            try:
                response = requests.post(
                    API_URL, 
                    headers=headers, 
                    json={"inputs": prompt_en},
                    timeout=60
                )
                
                if response.status_code == 200:
                    image_bytes = response.content
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    st.success("🎉 圖片生成成功！")
                    st.image(image, caption=f"FLUX.1 生成成果：{product_name}", use_container_width=True)
                    
                    # 提供下載按鈕
                    st.download_button(
                        label="📥 下載高畫質廣告圖片",
                        data=image_bytes,
                        file_name=f"eyewear_{model_num if model_num else 'ad'}.png",
                        mime="image/png"
                    )
                elif response.status_code == 503:
                    st.error("⏳ 模型正在初始化中（冷啟動），請稍等 15 秒後再試一次！")
                else:
                    st.error(f"❌ 生成失敗 (錯誤碼 {response.status_code})：{response.text}")
            except Exception as e:
                st.error(f"❌ 連線發生錯誤：{str(e)}")
