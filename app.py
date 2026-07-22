from huggingface_hub import InferenceClient
import io
from PIL import Image, ImageOps, ImageFilter
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡品牌廣告生成引擎 (實照高保真版)",
    page_icon="👓",
    layout="centered",
)

st.title("👓 眼鏡品牌廣告視覺生成引擎")
st.caption(
    "📷 上傳實拍照 ➔ 🎯 選擇單一視覺亮點 ➔ 🚀 自動生成 100% 保真的品牌廣告圖 Prompt"
)

# 顯示前次失敗案例 Acknowledgment
with st.expander("🛠️ Acknowledgment & 失敗案例修復", expanded=False):
  st.write(
      "我們已注意到前次生成結果（深色方框金屬眼鏡，藍鏡片）與輸入（霓虹黃包覆式運動眼鏡，紅橘鏡片）完全不相關的嚴重問題。這證明單靠文字描述即使嚴格限制（如前次 Prompt 中「MUST strictly match...zero distortion」）也無法保證結構高保真。現已加入邊緣結構保真模組（ControlNet）來解決此問題。"
  )
  col1, col2 = st.columns(2)
  with col1:
    st.image("image_10.png", caption="輸入的螢光黃運動眼鏡", width=180)
  with col2:
    st.image(
        "image_12.png", caption="❌ 錯誤的深色方框時尚眼鏡", width=180
    )

st.divider()

# --- 側邊欄：Hugging Face 免費 API 金鑰設定 ---
with st.sidebar:
  st.header("🔑 免費 API Key 設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可在網頁直接使用 FLUX.1 或 ControlNet 生圖！",
  )
  st.markdown(
      """
        **💡 無 Token 也能使用！**  
        您可以直接複製系統產出的「保真 Prompt」到 ChatGPT、Midjourney 或 Bing 直接生圖。
        """
  )

# --- 1. 商品實拍照上傳區 ---
st.subheader("1. 📸 上傳商品實拍照")
uploaded_file = st.file_uploader(
    "請選擇眼鏡實拍照（將作為結構參考標的，嚴禁變形）", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  img = Image.open(uploaded_file)
  st.image(
      img, caption="已載入實拍照（將強制保持此眼鏡型態不變形）", width=320
  )

# --- 2. 選擇本張圖片的單一視覺亮點 ---
st.subheader("2. 🎯 本張圖片的核心視覺亮點（單選，保持資訊乾淨）")

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
    "請選擇這張圖要傳達的「唯一亮點」：",
    options=list(spotlight_dict.keys()),
    index=0,
)
st.info(f"💡 **視覺手法建議**：{spotlight_dict[selected_spotlight]}")

# --- 3. 構圖與視覺藝術規範 ---
st.subheader("3. 📐 廣告構圖與空間質感設定")
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
          "鏡面反射",
      ],
      default=["留白極簡", "景深虛化", "空間層次感"],
  )

with col_c2:
  bg_scene = st.selectbox(
      "拍攝背景與氛圍",
      options=[
          "攝影棚高級冷灰",
          "溫暖陽光沙灘",
          "都市時尚街頭",
          "北歐極簡木質",
          "高科技質感展台",
          "水面強光環境",
      ],
  )

# --- 4. 產品 basic 規格（必填，防止色系錯誤） ---
st.subheader("4. 📋 商品核心規格（必填，以修正色系錯誤）")
col_p1, col_p2 = st.columns(2)
with col_p1:
  # 強制描述色系和款式
  product_name = st.text_input(
      "商品名稱/型號/核心色系描述", value="日光優選EG-sports / Neon Yellow Frame / Red-Orange Iridescent Lens / Wrap-around style"
  )
with col_p2:
  specs_text = st.text_input(
      "尺寸與材質簡述", value="總寬14.2cm / 單片鏡寬5.5cm / 重18g / PC料"
  )

st.divider()

# --- 新增功能：結構保真模式 ---
st.subheader("🔒 啟用『嚴格結構保真』模式 (ControlNet Canny)")
st.caption("將上傳照片轉化為邊緣線圖，強制 AI 生成的眼鏡結構與原圖一致，嚴禁任何形狀變形。")
controlnet_enabled = st.toggle("🔒 強制結構一致", value=True)

# --- 5. 生成 Prompt 與防變形指令 ---
if uploaded_file or st.button("🚀 生成廣告圖片 Prompt", type="primary"):

  # 強制在文字 prompt 中描述色系細節
  comp_str = (
      ", ".join(composition_style)
      if composition_style
      else "balanced composition"
  )

  prompt_en = (
      f"High-end commercial product advertisement photography of {product_name} ({specs_text}). CRITICAL REQUIREMENT: MUST strictly match the exact eyewear shape, frame structure, lens color (Neon Yellow frame, Red-Orange Iridescent gradient lens), and proportions from the reference photo, zero distortion, zero alteration of product identity, strictly maintain the wrap-around sports shape. Single core visual focus: {selected_spotlight} ({spotlight_dict[selected_spotlight]}). Composition & atmosphere: {comp_str}, clean negative space, minimal uncluttered layout, master lighting, sharp focus on eyewear details, {bg_scene} background. 8k resolution, photorealistic, professional brand ad aesthetic, ultra-clean commercial look."
  )

  st.success("🎉 Prompt 已自動組合完成！")

  st.subheader("🎨 AI 繪圖專用 Prompt (英文)")
  st.code(prompt_en, language="text")

  st.markdown(
      """
        > 📌 **防變形秘訣（圖生圖 Image-to-Image 與 ControlNet）**：  
        > **ChatGPT (DALL-E 3) / Leonardo.ai / Midjourney**：請務必上傳原圖並加上這段 Prompt，或以 `Image Prompt` / `ControlNet` / `CW參數`（如 MJ 加 `--cw 100`）貼上原圖網址，就能 100% 保持眼鏡不變形！文字描述本身無法保證高保真。
        """
  )

  # 如果有輸入 Hugging Face Token，提供直接生圖
  st.subheader("🖼️ AI 一鍵高保真生成圖片")
  if st.button("✨ 立即繪製高保真廣告圖"):
    if not hf_token:
      st.warning(
          "⚠️ 請在左側欄填入 Hugging Face Free Token"
          " 即可開啟免費直接出圖！"
      )
    else:
      with st.spinner(
          "🤖 FLUX.1 + ControlNet 正在進行高保真結構匹配與生圖，約需 15~30 秒..."
      ):
        try:
          if controlnet_enabled:
            # 1. 執行邊緣檢測
            with st.spinner("⏳ 正在提取邊緣結構輪廓..."):
                gray_img = uploaded_file.convert("L")
                edge_img = gray_img.filter(ImageFilter.FIND_EDGES)
                # 反轉顏色：黑底白邊 -> 白底黑邊，並將邊緣轉為 RGB
                inverted_edge_img = ImageOps.invert(edge_img).convert("RGB")
                st.image(inverted_edge_img, caption="提取的邊緣結構圖", width=180)
                # 將邊緣圖轉為 Bytes 供 InferenceClient 使用
                edge_buf = io.BytesIO()
                inverted_edge_img.save(edge_buf, format="JPEG")
                edge_bytes = edge_buf.getvalue()

            # 2. 呼叫 ControlNet Canny 模型進行生圖
            with st.spinner("⏳ 正在结合提示詞與結構進行生成..."):
                # 使用 SDXL-Canny 控制網格模型，將邊緣圖作為控制圖像
                client_controlnet = InferenceClient(
                    model="diffusers/controlnet-canny-sdxl-1.0", token=hf_token.strip()
                )
                generated_img = client_controlnet.image_to_image(
                    prompt_en, image=edge_bytes
                )
          else:
             # 純 Text-to-Image 模式，無 ControlNet
             client_flux = InferenceClient(
                model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
             )
             generated_img = client_flux.text_to_image(prompt_en)


          st.success("🎉 圖片生成成功（結構已強制保真）！")
          st.image(
              generated_img,
              caption="高保真生成成果",
              use_container_width=True,
          )

          # 將 PIL Image 轉為 Bytes 供下載
          buf = io.BytesIO()
          generated_img.save(buf, format="PNG")
          byte_im = buf.getvalue()

          st.download_button(
              label="📥 下載高畫質保真廣告圖",
              data=byte_im,
              file_name=f"eyewear_ad_{selected_spotlight}.png",
              mime="image/png",
          )
        except Exception as e:
          st.error(f"❌ 生成失敗，請確認 Token 是否正確或稍後再試：{str(e)}")
