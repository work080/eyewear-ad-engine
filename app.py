import io
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFilter
from rembg import remove  # 自動去背套件
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡電商 ➔ AI 一鍵商業攝影合成引擎",
    page_icon="👓",
    layout="centered",
)

st.title("👓 眼鏡電商 ➔ 一鍵自動合成商業大片引擎")
st.caption(
    "📷 上傳實拍照 ➔ 🚀 AI 自動去背 + 生成展台 + 圖層合成 ➔ 直接下載完稿大片！"
)

st.divider()

# --- 側邊欄：Hugging Face 免費 API 金鑰設定 ---
with st.sidebar:
  st.header("🔑 免費 API Key 設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可在網頁直接生成背景與合成圖！",
  )
  st.markdown(
      """
        ---
        **💡 提示**：  
        如專案部署遇到 `rembg` 錯誤，請確認您的 `requirements.txt` 檔案中有加上 `rembg` 與 `onnxruntime`。
        """
  )

# --- 1. 商品實拍照上傳區 ---
st.subheader("1. 📸 上傳商品實拍照")
uploaded_file = st.file_uploader(
    "請選擇眼鏡實拍照（系統將自動進行 AI 去背）", type=["jpg", "jpeg", "png"]
)

img_uploaded = None
if uploaded_file is not None:
  img_uploaded = Image.open(uploaded_file)
  st.image(
      img_uploaded,
      caption="已載入商品實拍照",
      width=260,
  )

# --- 2. 選擇展台與拍攝風格 ---
st.subheader("2. 🎨 選擇展台背景風格與光影")

col1, col2 = st.columns(2)

with col1:
  scene_style = st.selectbox(
      "展台與材質主題",
      options=[
          "粗獷黑火山岩石 (運動/戶外)",
          "極速光束與科技感展台 (競技感)",
          "高級水面波紋與陽光折射 (抗UV/偏光)",
          "北歐極簡水泥與日光光影 (生活質感)",
          "高科技微光懸浮舞台 (極輕量)",
      ],
  )

with col2:
  lighting_style = st.selectbox(
      "商業攝影光影手法",
      options=[
          "戲劇化輪廓側光 (High Contrast Rim Lighting)",
          "柔和自然晨光 (Soft Natural Sunlight)",
          "霓虹賽博朋克光影 (Cyberpunk Neon Glow)",
          "頂級冷灰工作室均勻光 (Clean Studio Lighting)",
      ],
  )

scene_prompts = {
    "粗獷黑火山岩石 (運動/戶外)": (
        "rough dark volcanic rock podium, dark slate base"
    ),
    "極速光束與科技感展台 (競技感)": (
        "futuristic metallic display stage with glowing red and white light"
        " tracks, empty pedestal in middle"
    ),
    "高級水面波紋與陽光折射 (抗UV/偏光)": (
        "shallow water surface with gentle ripples, sunlight refraction on"
        " pedestal"
    ),
    "北歐極簡水泥與日光光影 (生活質感)": (
        "minimalist concrete block display podium, soft window sunlight shadow"
    ),
    "高科技微光懸浮舞台 (極輕量)": (
        "sleek black frosted glass pedestal, dark ambient lighting"
    ),
}

backdrop_prompt = (
    "Commercial product display backdrop photography. Clean empty round"
    f" pedestal stage in center. Background style: {scene_prompts[scene_style]}."
    f" Lighting: {lighting_style}. Shallow depth of field, blurred background,"
    " crisp focus on center pedestal, 8k resolution, NO sunglasses, NO text,"
    " clean empty stage."
)

st.divider()

# --- 3. 一鍵自動去背與合成 ---
st.subheader("3. 🚀 自動去背 + 背景生成 + 陰影合成")

if st.button("✨ 一鍵產出 100% 真實廣告合成大片", type="primary"):
  if not img_uploaded:
    st.error("⚠️ 請先上傳眼鏡實拍照！")
  elif not hf_token:
    st.warning("⚠️ 請在左側欄填入 Hugging Face Free Token！")
  else:
    try:
      # Step 1: AI 背景生成
      with st.spinner("🤖 [1/3] 正在繪製高階展台背景..."):
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
        )
        bg_image = client.text_to_image(backdrop_prompt).convert("RGBA")

      # Step 2: 實拍照自動去背
      with st.spinner("✂️ [2/3] 正在進行眼鏡實拍照 AI 精準去背..."):
        nobg_product = remove(img_uploaded).convert("RGBA")

      # Step 3: 自動尺寸對齊與融合圖層合成
      with st.spinner("🎯 [3/3] 正在調整比例、添加接觸陰影與圖層合成..."):
        bg_w, bg_h = bg_image.size

        # 縮放眼鏡尺寸（使其約佔背景寬度的 48%）
        target_w = int(bg_w * 0.48)
        aspect_ratio = nobg_product.height / nobg_product.width
        target_h = int(target_w * aspect_ratio)
        resized_product = nobg_product.resize(
            (target_w, target_h), Image.Resampling.LANCZOS
        )

        # 計算放置於展台中央的座標
        pos_x = (bg_w - target_w) // 2
        pos_y = int(bg_h * 0.45)  # 垂直置於展台對應區域

        # 製作擬真陰影圖層 (接地陰影)
        shadow_layer = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow_layer)
        shadow_box = [
            pos_x + int(target_w * 0.1),
            pos_y + target_h - int(target_h * 0.15),
            pos_x + int(target_w * 0.9),
            pos_y + target_h + int(target_h * 0.1),
        ]
        draw.ellipse(shadow_box, fill=(0, 0, 0, 140))
        shadow_layer = shadow_layer.filter(
            ImageFilter.GaussianBlur(radius=int(target_w * 0.05))
        )

        # 合成：背景 ➔ 陰影 ➔ 真實眼鏡
        final_composite = Image.alpha_composite(bg_image, shadow_layer)
        final_composite.paste(
            resized_product, (pos_x, pos_y), mask=resized_product
        )

      st.success("🎉 廣告大片已自動合成完成！100% 保留實拍照細節！")
      st.image(
          final_composite,
          caption="🏆 合成完稿大片（真實商品 + AI 展台背景）",
          use_container_width=True,
      )

      # 下載圖檔轉換
      buf = io.BytesIO()
      final_composite.convert("RGB").save(buf, format="JPEG", quality=95)
      byte_im = buf.getvalue()

      st.download_button(
          label="📥 下載完成版廣告大片 (HD)",
          data=byte_im,
          file_name="final_eyewear_ad.jpg",
          mime="image/jpeg",
      )

    except Exception as e:
      st.error(f"❌ 處理過程發生錯誤：{str(e)}")
