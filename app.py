import io
import zipfile
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import streamlit as st

# 容錯載入 rembg
try:
  from rembg import remove

  REMBG_AVAILABLE = True
except Exception:
  REMBG_AVAILABLE = False

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡電商 ➔ 全套 6 大商業主圖批量生成器",
    page_icon="👓",
    layout="wide",
)

st.title("👓 眼鏡電商 ➔ 批量多圖 & 全套 6 大廣告主圖生成引擎")
st.caption(
    "📷 上傳多張商品圖 ➔ 🚀 自動產出：品牌首圖 / 鼻墊特寫 / 鏡腳特寫 / 尺寸圖 / 重量圖 /"
    " 情境圖 ➔ 一鍵打包下載！"
)

st.divider()

# --- 側邊欄：API 與品牌設定 ---
with st.sidebar:
  st.header("⚙️ 品牌與 API 設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可自動生成 AI 情境背景與特寫！",
  )
  brand_logo_text = st.text_input("品牌 Logo 文字", value="SCVCN")
  st.markdown("---")
  st.info(
      "💡 **套圖包含**：\n1. 品牌展台首圖\n2. 鼻墊結構特寫\n3. 鏡腳細節特寫\n4. 尺寸規格標示圖\n5."
      " 極輕重量圖表\n6. 戶外情境配戴圖"
  )

# --- 1. 多圖上傳區 ---
st.subheader("1. 📸 批量上傳商品實拍照（可一次選擇多張）")
uploaded_files = st.file_uploader(
    "請選擇一張或多張眼鏡實拍照：",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
  st.success(f"已成功載入 {len(uploaded_files)} 張商品照片！")
  cols = st.columns(min(len(uploaded_files), 5))
  for idx, file in enumerate(uploaded_files):
    with cols[idx % 5]:
      st.image(Image.open(file), caption=f"商品 {idx+1}", use_container_width=True)

st.divider()

# --- 2. 輔助繪圖與文字函式 ---


def add_watermark_logo(img, text="SCVCN"):
  """在圖片左上角加上品牌 Logo標籤"""
  img_copy = img.copy().convert("RGBA")
  draw = ImageDraw.Draw(img_copy)
  w, h = img_copy.size

  # 繪製半透明 Logo 底框
  box_w, box_h = int(w * 0.25), int(h * 0.08)
  margin = int(w * 0.04)
  draw.rectangle(
      [margin, margin, margin + box_w, margin + box_h], fill=(0, 0, 0, 180)
  )

  # 標示 Logo 文字
  try:
    font = ImageFont.truetype("arial.ttf", int(box_h * 0.5))
  except IOError:
    font = ImageFont.load_default()

  draw.text(
      (margin + int(box_w * 0.15), margin + int(box_h * 0.2)),
      text,
      fill=(255, 255, 255, 255),
      font=font,
  )
  return img_copy


def create_dimension_image(product_img):
  """生成尺寸標示圖表"""
  img = product_img.copy().convert("RGBA")
  w, h = img.size
  draw = ImageDraw.Draw(img)

  # 繪製尺寸指示線 (鏡框寬度與鏡腳長度)
  color = (255, 50, 50, 255)
  # 橫向總寬標示線
  draw.line(
      [(int(w * 0.1), int(h * 0.85)), (int(w * 0.9), int(h * 0.85))],
      fill=color,
      width=4,
  )
  draw.line(
      [(int(w * 0.1), int(h * 0.82)), (int(w * 0.1), int(h * 0.88))],
      fill=color,
      width=4,
  )
  draw.line(
      [(int(w * 0.9), int(h * 0.82)), (int(w * 0.9), int(h * 0.88))],
      fill=color,
      width=4,
  )

  # 加上尺寸文字標籤
  try:
    font = ImageFont.truetype("arial.ttf", int(h * 0.045))
  except IOError:
    font = ImageFont.load_default()

  draw.text(
      (int(w * 0.38), int(h * 0.88)),
      "Total Width: 148mm",
      fill=(20, 20, 20, 255),
      font=font,
  )
  draw.text(
      (int(w * 0.05), int(h * 0.45)),
      "Lens Height: 60mm",
      fill=(20, 20, 20, 255),
      font=font,
  )

  return img


def create_weight_image(product_img):
  """生成重量圖表"""
  img = product_img.copy().convert("RGBA")
  w, h = img.size
  draw = ImageDraw.Draw(img)

  # 繪製極輕重量徽章
  badge_box = [int(w * 0.65), int(h * 0.1), int(w * 0.92), int(h * 0.35)]
  draw.ellipse(badge_box, fill=(255, 215, 0, 230), outline=(255, 255, 255), width=3)

  try:
    font_large = ImageFont.truetype("arial.ttf", int(h * 0.06))
    font_small = ImageFont.truetype("arial.ttf", int(h * 0.03))
  except IOError:
    font_large = font_small = ImageFont.load_default()

  draw.text(
      (int(w * 0.72), int(h * 0.16)),
      "28g",
      fill=(0, 0, 0, 255),
      font=font_large,
  )
  draw.text(
      (int(w * 0.69), int(h * 0.25)),
      "Ultra Light",
      fill=(0, 0, 0, 255),
      font=font_small,
  )

  return img


# --- 3. 批量生成邏輯 ---
st.subheader("3. 🚀 一鍵批量生成 6 大電商套圖")

if st.button("✨ 開始生成所有眼鏡的全套商業圖", type="primary"):
  if not uploaded_files:
    st.error("⚠️ 請先上傳至少一張眼鏡實拍照！")
  elif not hf_token:
    st.warning("⚠️ 請在左側欄填入 Hugging Face Free Token！")
  else:
    client = InferenceClient(
        model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
    )

    all_zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        all_zip_buffer, "a", zipfile.ZIP_DEFLATED, False
    ) as zip_file:

      for file_idx, file in enumerate(uploaded_files):
        st.markdown(
            f"### 👓 正在處理第 {file_idx+1} 款眼鏡：`{file.name}`"
        )
        orig_img = Image.open(file)

        # 自動去背
        if REMBG_AVAILABLE:
          nobg_img = remove(orig_img).convert("RGBA")
        else:
          nobg_img = orig_img.convert("RGBA")

        # 開闢 6 個展示欄位
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m4, col_m5, col_m6 = st.columns(3)

        # 1. 首圖 (含 Logo + 合成背景)
        with col_m1:
          st.caption("1️⃣ 品牌展台首圖 (含 Logo)")
          bg_prompt = (
              "Commercial product display backdrop with a sleek podium in"
              " center, dark volcanic rock texture, studio rim light, 8k"
          )
          bg_img = client.text_to_image(bg_prompt).convert("RGBA")

          # 縮放與貼合
          bg_w, bg_h = bg_img.size
          tw = int(bg_w * 0.5)
          th = int(tw * (nobg_img.height / nobg_img.width))
          resized_nobg = nobg_img.resize((tw, th), Image.Resampling.LANCZOS)

          comp_head = bg_img.copy()
          comp_head.paste(
              resized_nobg,
              ((bg_w - tw) // 2, int(bg_h * 0.45)),
              mask=resized_nobg,
          )
          final_head = add_watermark_logo(comp_head, text=brand_logo_text)
          st.image(final_head, use_container_width=True)

        # 2. 鼻墊特寫圖
        with col_m2:
          st.caption("2️⃣ 鼻墊結構特寫圖")
          nose_prompt = (
              "Macro close-up photography of comfortable silicone nose pads of"
              " athletic sunglasses, sharp details, studio lighting"
          )
          nose_img = client.text_to_image(nose_prompt)
          st.image(nose_img, use_container_width=True)

        # 3. 鏡腳特寫圖
        with col_m3:
          st.caption("3️⃣ 鏡腳雙色質感特寫圖")
          temple_prompt = (
              "Extreme macro close-up of dual-color black and neon yellow"
              " sunglass temples, anti-slip texture, high-tech engineering"
              " details"
          )
          temple_img = client.text_to_image(temple_prompt)
          st.image(temple_img, use_container_width=True)

        # 4. 尺寸標示圖表
        with col_m4:
          st.caption("4️⃣ 眼鏡尺寸標示圖")
          dim_img = create_dimension_image(orig_img)
          st.image(dim_img, use_container_width=True)

        # 5. 極輕重量圖表
        with col_m5:
          st.caption("5️⃣ 極輕重量規格圖")
          weight_img = create_weight_image(orig_img)
          st.image(weight_img, use_container_width=True)

        # 6. 模特兒配戴情境圖
        with col_m6:
          st.caption("6️⃣ 戶外運動情境配戴圖")
          model_prompt = (
              "Professional cyclist wearing neon yellow wraparound sports"
              " sunglasses riding on scenic mountain road, bright sunny day,"
              " action camera shot, realistic"
          )
          model_img = client.text_to_image(model_prompt)
          st.image(model_img, use_container_width=True)

        # 打包至 Zip 壓縮檔
        prefix = f"Glasses_{file_idx+1}"

        for img_obj, name in [
            (final_head, "01_Main_Logo.png"),
            (nose_img, "02_Nose_Pads.png"),
            (temple_img, "03_Temples.png"),
            (dim_img, "04_Dimensions.png"),
            (weight_img, "05_Weight.png"),
            (model_img, "06_Model_Lifestyle.png"),
        ]:
          buf = io.BytesIO()
          img_obj.convert("RGB").save(buf, format="PNG")
          zip_file.writestr(f"{prefix}/{name}", buf.getvalue())

        st.divider()

    st.success("🎉 所有圖片已生成完畢！")

    # 提供全套 Zip 打包下載按鈕
    st.download_button(
        label="📦 一鍵下載所有眼鏡的【全套電商圖包 (ZIP)】",
        data=all_zip_buffer.getvalue(),
        file_name="eyewear_full_ecommerce_pack.zip",
        mime="application/zip",
    )
