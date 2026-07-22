import io
from huggingface_hub import InferenceClient
from PIL import Image
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡電商 ➔ AI 商業廣告生成工作室",
    page_icon="👓",
    layout="centered",
)

st.title("👓 眼鏡電商 AI 商業廣告生成工作室")
st.caption(
    "📷 上傳實拍照 ➔ 📋 填寫商品資訊 ➔ 🎯 選擇賣點與風格 ➔ 🚀 一鍵產出 Prompt"
    " 與展台背景"
)

st.divider()

# --- 側邊欄：Hugging Face 免費 API 金鑰設定 ---
with st.sidebar:
  st.header("🔑 免費 API Key 設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可在網頁直接生成背景圖！",
  )
  st.markdown(
      """
        ---
        **💡 提示**：
        若無 Token，仍可上傳圖片並填寫資訊，系統會為您自動組裝英文 Prompt！
        """
  )

# --- 1. 商品實拍照上傳區 ---
st.subheader("1. 📸 上傳商品實拍照")
uploaded_file = st.file_uploader(
    "請選擇眼鏡實拍照（做為視覺對照與合成素材）", type=["jpg", "jpeg", "png"]
)

img_uploaded = None
if uploaded_file is not None:
  img_uploaded = Image.open(uploaded_file)
  st.image(
      img_uploaded,
      caption="已載入商品實拍照",
      width=300,
  )

# --- 2. 商品資訊與規格填寫（完整恢復） ---
st.subheader("2. 📋 填寫商品資訊與細節規格")

col_p1, col_p2 = st.columns(2)
with col_p1:
  product_name = st.text_input(
      "商品名稱 / 型號",
      value="EG-Sports 包覆式極速運動太陽眼鏡",
  )
  frame_detail = st.text_input(
      "鏡框與鏡腳細節描述",
      value="Neon yellow athletic frame, black and neon-yellow dual-color temples",
  )

with col_p2:
  lens_detail = st.text_input(
      "鏡片款式與特色",
      value="Red-orange iridescent reflective one-piece shield lens",
  )
  specs_text = st.text_input(
      "材質 / 尺寸 / 備註",
      value="PC 防爆鏡片 / 抗 UV400 / 極輕量 28g",
  )

# --- 3. 核心賣點與商業場景設定 ---
st.subheader("3. 🎯 選擇核心賣點與廣告背景風格")

spotlight_dict = {
    "抗 UV / 偏光強光": "陽光/光線折射/保護罩光影特效，突出抗紫外線與防眩光",
    "防霧 / 透氣流線": "細微氣流/透氣孔線條/霧氣蒸散質感，展現清晰視覺",
    "超輕量 / 無負擔": "羽毛懸浮/微浮空懸浮感/極致輕盈展台",
    "記憶金屬 / 耐壓韌性": "柔和韌性曲線/機械結構切面特寫",
    "戶外運動 / 質感情境": "粗獷黑火山岩石/大地質感/戶外競技氛圍",
}

selected_spotlight = st.selectbox(
    "請選擇這組廣告的主要視覺賣點：",
    options=list(spotlight_dict.keys()),
    index=0,
)

col_s1, col_s2 = st.columns(2)
with col_s1:
  scene_style = st.selectbox(
      "展台與背景主題",
      options=[
          "粗獷黑火山岩石 (運動/戶外)",
          "極速光束與科技感展台 (競技感)",
          "水面波紋與陽光折射 (抗UV/偏光)",
          "北歐極簡水泥與光影 (質感生活)",
          "高科技微光懸浮舞台 (極輕量)",
      ],
  )

with col_s2:
  lighting_style = st.selectbox(
      "商業光影手法",
      options=[
          "戲劇化輪廓側光 (High Contrast Rim Lighting)",
          "柔和自然晨光 (Soft Natural Sunlight)",
          "霓虹賽博朋克光影 (Cyberpunk Neon Glow)",
          "頂級冷灰工作室均勻光 (Clean Studio Lighting)",
      ],
  )

scene_prompts = {
    "粗獷黑火山岩石 (運動/戶外)": "rough dark volcanic rock podium, dark slate base",
    "極速光束與科技感展台 (競技感)": "futuristic metallic stage with glowing speed light trails",
    "水面波紋與陽光折射 (抗UV/偏光)": "shallow water surface with gentle ripples, sunlight refraction",
    "北歐極簡水泥與光影 (質感生活)": "minimalist concrete block display podium, soft window shadows",
    "高科技微光懸浮舞台 (極輕量)": "sleek black frosted glass pedestal, dark ambient lighting",
}

clean_logo_toggle = st.checkbox("🚫 自動加上負面指令（避免 AI 印出亂碼假 Logo）", value=True)

st.divider()

# --- 4. 自動組裝 Prompt 與圖片生成 ---
st.subheader("4. 🚀 產出專屬 Prompt 與商業展台生成")

# 組合商品完整描述 Prompt (適合帶去 MJ / ChatGPT)
full_product_prompt = (
    f"Commercial product photography of {product_name}. Frame: {frame_detail}. Lens: {lens_detail}. "
    f"Key feature highlight: {selected_spotlight} ({spotlight_dict[selected_spotlight]}). "
    f"Background: {scene_prompts[scene_style]}, lighting: {lighting_style}. "
    f"8k resolution, photorealistic, sharp details, master lighting."
)
if clean_logo_toggle:
  full_product_prompt += ", NO text, NO brand logo, clean frame surface"

# 組合純背景 Prompt (適合網頁直接生成底圖)
backdrop_prompt = (
    f"Commercial product display backdrop photography. Empty podium in center for product placement. "
    f"Style: {scene_prompts[scene_style]}. Lighting: {lighting_style}. "
    f"Shallow depth of field, blurred background, crisp focus on empty center pedestal, "
    f"8k resolution, cinematic mood, NO sunglasses, clean empty stage."
)

st.write("#### 🎨 方案 A：完整商品 Prompt（可複製至 Midjourney / ChatGPT）")
st.code(full_product_prompt, language="text")

st.write("#### 📸 方案 B：純商業展台 Prompt（供網頁線上生成背景圖）")
st.code(backdrop_prompt, language="text")

# 生圖按鈕
if st.button("✨ 立即生成專屬商業展台背景", type="primary"):
  if not hf_token:
    st.warning("⚠️ 請在左側欄填入 Hugging Face Free Token 即可線上生成！")
  else:
    with st.spinner("🤖 FLUX.1 正在依據您的商品主題繪製商業展台..."):
      try:
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
        )
        generated_bg = client.text_to_image(backdrop_prompt)

        st.success("🎉 背景生成成功！")

        if img_uploaded is not None:
          st.subheader("🖼️ 素材對比與合成預覽")
          col_a, col_b = st.columns(2)
          with col_a:
            st.image(
                img_uploaded,
                caption=f"1️⃣ 您的實拍照：{product_name}",
                use_container_width=True,
            )
          with col_b:
            st.image(
                generated_bg,
                caption="2️⃣ AI 為您生成的匹配展台背景",
                use_container_width=True,
            )
        else:
          st.image(
              generated_bg,
              caption="AI 生成展台背景",
              use_container_width=True,
          )

        # 下載背景圖檔
        buf = io.BytesIO()
        generated_bg.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="📥 下載高畫質展台背景圖",
            data=byte_im,
            file_name=f"backdrop_{product_name}.png",
            mime="image/png",
        )
      except Exception as e:
        st.error(f"❌ 生成失敗，請檢查 Token 是否正確：{str(e)}")
