import io
from huggingface_hub import InferenceClient
from PIL import Image
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡品牌廣告生成引擎", page_icon="👓", layout="centered"
)

st.title("👓 眼鏡品牌廣告視覺生成引擎")
st.caption(
    "📷 上傳實拍照 ➔ 🎯 設定細節防亂印 Logo ➔ 🚀 自動生成高質感廣告 Prompt 與 AI 圖片"
)

st.divider()

# --- 側邊欄：Hugging Face 免費 API 金鑰設定 ---
with st.sidebar:
  st.header("🔑 免費 API Key 設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可在網頁直接使用 FLUX.1 生圖！",
  )
  st.markdown(
      """
        **💡 無 Token 也能使用！**  
        複製系統產出的 Prompt，直接貼到 ChatGPT、Midjourney 或 Bing 即可生圖。
        """
  )

# --- 1. 商品實拍照上傳區 ---
st.subheader("1. 📸 上傳商品實拍照")
uploaded_file = st.file_uploader(
    "請選擇眼鏡實拍照（系統作為風格與構圖參考）", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  img = Image.open(uploaded_file)
  st.image(img, caption="已載入實拍照", width=320)

# --- 2. 選擇本張圖片的單一視覺亮點 ---
st.subheader("2. 🎯 本張圖片的核心視覺亮點")

spotlight_dict = {
    "抗 UV": "陽光/光線折射/UV保護罩光影特效，突出抗紫外線功能",
    "防霧": "細微氣流/透氣流線/霧氣蒸散質感，展現鏡片清晰度",
    "輕量": "電子秤/羽毛懸浮/微浮空漂浮感，展現極致輕盈",
    "柔軟/記憶金屬": "鏡腳彎折示意/柔和韌性曲線，展現耐壓材質",
    "偏光": "前後對比/眩光控制/水面強光消除視覺特效",
    "耐用/材質": "金屬與鏡片切面特寫/高品質工藝細節放大",
    "生活使用情境": "真實人物佩戴/質感街頭/時尚氛圍拍攝",
}

selected_spotlight = st.radio(
    "請選擇主要訴求：", options=list(spotlight_dict.keys()), index=0
)

# --- 3. 構圖與背景質感設定 ---
st.subheader("3. 📐 構圖與空間質感設定")
col_c1, col_c2 = st.columns(2)

with col_c1:
  composition_style = st.multiselect(
      "選擇構圖手法（可多選）",
      options=[
          "留白極簡",
          "斜角構圖",
          "前後景深度",
          "景深虛化",
          "光影對比",
          "空間層次感",
      ],
      default=["留白極簡", "景深虛化"],
  )

with col_c2:
  bg_scene = st.selectbox(
      "拍攝背景與氛圍",
      options=[
          "粗獷岩石/地質質感 (運動風)",
          "攝影棚高級冷灰",
          "溫暖陽光沙灘",
          "都市時尚街頭",
          "北歐極簡木質",
          "高科技質感展台",
      ],
  )

# --- 4. 產品真實細節控制 (防止 AI 亂印假 Logo 與塗裝錯誤) ---
st.subheader("4. 🎨 產品細節與防亂印 Logo 設定")

col_d1, col_d2 = st.columns(2)
with col_d1:
  frame_detail = st.text_input(
      "鏡框與鏡腳細節描述",
      value=(
          "Neon yellow athletic frame, black and neon-yellow dual-color"
          " temples"
      ),
  )
with col_d2:
  lens_detail = st.text_input(
      "鏡片細節描述", value="Red-orange iridescent reflective visor lens"
  )

clean_logo_toggle = st.checkbox("🚫 強制移除假 Logo / 文字標籤", value=True)

st.divider()

# --- 5. 生成 Prompt 與生圖 ---
if uploaded_file or st.button("🚀 生成廣告圖片 Prompt", type="primary"):

  comp_str = (
      ", ".join(composition_style)
      if composition_style
      else "balanced composition"
  )

  # 建立基礎 Prompt
  prompt_en = (
      f"High-end commercial product advertisement photography of wraparound"
      f" sports sunglasses. Frame details: {frame_detail}. Lens details:"
      f" {lens_detail}. Core visual focus: {selected_spotlight}"
      f" ({spotlight_dict[selected_spotlight]}). Atmosphere: {comp_str},"
      f" {bg_scene} background. Master studio lighting, 8k resolution,"
      " photorealistic, sharp focus on product."
  )

  # 若勾選避開 Logo，加入負面防護關鍵字
  if clean_logo_toggle:
    prompt_en += (
        ", NO text, NO brand logo, NO writing on frame, clean blank surface"
    )

  st.success("🎉 Prompt 已自動組合完成！")

  st.subheader("🎨 AI 繪圖專用 Prompt (英文)")
  st.code(prompt_en, language="text")

  st.info(
      "💡 **專業行銷小技巧**：此 Prompt 已加入 `NO text, NO brand logo`"
      " 負面排除指令，能大幅避免 AI 印出隨機英文標籤。"
  )

  # 線上生圖區塊
  st.subheader("🖼️ FLUX.1 免費線上生圖")
  if st.button("✨ 立即繪製廣告圖"):
    if not hf_token:
      st.warning("⚠️ 請在左側欄填入 Hugging Face Free Token！")
    else:
      with st.spinner("🤖 FLUX.1 正在生成廣告圖中，請稍候 10~20 秒..."):
        try:
          client = InferenceClient(
              model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
          )
          generated_img = client.text_to_image(prompt_en)

          st.success("🎉 圖片生成成功！")
          st.image(
              generated_img,
              caption="FLUX.1 生成成果",
              use_container_width=True,
          )

          # 下載圖檔轉換
          buf = io.BytesIO()
          generated_img.save(buf, format="PNG")
          byte_im = buf.getvalue()

          st.download_button(
              label="📥 下載廣告圖",
              data=byte_im,
              file_name="eyewear_ad.png",
              mime="image/png",
          )
        except Exception as e:
          st.error(f"❌ 生成失敗，請檢查 Token 是否正確：{str(e)}")
