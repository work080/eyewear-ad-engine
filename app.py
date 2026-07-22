import io
from huggingface_hub import InferenceClient
from PIL import Image
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡電商 ➔ AI 商業攝影背景生成器",
    page_icon="📸",
    layout="centered",
)

st.title("📸 眼鏡廣告 ➔ 高階商業攝影背景生成器")
st.caption(
    "💡 拒絕商品變形！用 AI 生成頂級商品展台背景 ➔ 疊加實拍照 ➔ 100% 保真出大片"
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

# --- 1. 選擇商品風格與展台氛圍 ---
st.subheader("1. 🎨 選擇廣告背景風格與氛圍")

col1, col2 = st.columns(2)

with col1:
  scene_style = st.selectbox(
      "展台與材質主題",
      options=[
          "粗獷黑火山岩石 (運動風/戶外)",
          "極速光束與科技感展示台 (競技感)",
          "高級攝影棚水面波紋反射 (抗UV/偏光)",
          "北歐極簡水泥與日光光影 (生活質感)",
          "高科技微光懸浮舞台 (極輕量)",
      ],
  )

with col2:
  lighting_style = st.selectbox(
      "商業攝影光影手法",
      options=[
          "戲劇化輪廓側光 (High Contrast Rim Lighting)",
          "柔和自然晨光與植物陰影 (Soft Natural Sunlight)",
          "霓虹賽博朋克光影 (Cyberpunk Neon Glow)",
          "頂級冷灰工作室均勻光 (Clean Studio Lighting)",
      ],
  )

# 風景描述對照字典
scene_prompts = {
    "粗獷黑火山岩石 (運動風/戶外)": (
        "rough dark volcanic rock podium, dark textured slate stone base"
    ),
    "極速光束與科技感展示台 (競技感)": (
        "futuristic metallic display stage with glowing speed light trails"
    ),
    "高級攝影棚水面波紋反射 (抗UV/偏光)": (
        "shallow water surface with gentle ripples, subtle reflection"
    ),
    "北歐極簡水泥與日光光影 (生活質感)": (
        "minimalist concrete block display podium, soft window sunlight shadows"
    ),
    "高科技微光懸浮舞台 (極輕量)": (
        "sleek black frosted glass display pedestal, dark ambient lighting"
    ),
}

st.divider()

# --- 2. 生成 Prompt 與背景圖 ---
st.subheader("2. 🚀 生成純背景商業 Prompt")

prompt_en = (
    "Commercial product display backdrop photography. Empty podium in center"
    f" for product placement. Style: {scene_prompts[scene_style]}. Lighting:"
    f" {lighting_style}. Shallow depth of field, blurred background, crisp"
    " focus on empty center pedestal, cinematic mood, 8k resolution, award"
    " winning advertising photography, NO sunglasses, NO people, clean empty"
    " stage."
)

st.code(prompt_en, language="text")

st.info(
    "💡 **最佳電商出圖流程**：\n1. 用下方按鈕生成優質背景圖\n2. 點擊【下載背景圖】\n3. 在"
    " Canva / Photoshop 貼上您去背後的眼鏡實拍照，即刻完成 100% 真實廣告！"
)

# 生圖按鈕
st.subheader("🖼️ 一鍵生成頂級商業背景")
if st.button("✨ 立即繪製廣告背景圖", type="primary"):
  if not hf_token:
    st.warning("⚠️ 請在左側欄填入 Hugging Face Free Token！")
  else:
    with st.spinner("🤖 FLUX.1 正在為您繪製高階商業展台背景..."):
      try:
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
        )
        generated_img = client.text_to_image(prompt_en)

        st.success("🎉 背景生成成功！請將實拍照去背後合成至中央展台。")
        st.image(
            generated_img,
            caption="商業展示背景（已預留中央商品位置）",
            use_container_width=True,
        )

        # 下載圖檔
        buf = io.BytesIO()
        generated_img.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="📥 下載高畫質背景圖",
            data=byte_im,
            file_name="commercial_background.png",
            mime="image/png",
        )
      except Exception as e:
        st.error(f"❌ 生成失敗，請檢查 Token 是否正確：{str(e)}")
