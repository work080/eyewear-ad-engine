import io
import zipfile
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡電商 ➔ AI 廣告視覺生成系統", page_icon="👓", layout="wide"
)

st.title("👓 眼鏡電商 ➔ 廣告視覺與賣點大片生成器")
st.caption(
    "📷 支援 JPG / PNG ➔ 🎨 自動生成「光束、氣流、羽毛飄浮、水花」等 7 大賣點視覺大片"
)

st.divider()

# --- 側邊欄：設定區 ---
with st.sidebar:
  st.header("⚙️ 品牌與尺寸設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可自動繪製 AI 視覺亮點背景！",
  )
  brand_logo_text = st.text_input("品牌 Logo 文字", value="SCVCN")

  st.subheader("📐 商品尺寸設定")
  glass_width = st.text_input("眼鏡總寬度", value="148mm")
  lens_height = st.text_input("鏡片高度", value="60mm")
  temple_len = st.text_input("鏡腳長度", value="125mm")

# --- 1. 多圖上傳區 ---
st.subheader("1. 📸 批量上傳商品實拍照（建議使用 JPG / PNG）")
uploaded_files = st.file_uploader(
    "請選擇眼鏡實拍照：",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if uploaded_files:
  st.success(f"已成功載入 {len(uploaded_files)} 張商品照片！")
  cols = st.columns(min(len(uploaded_files), 5))
  for idx, file in enumerate(uploaded_files):
    with cols[idx % 5]:
      try:
        img = Image.open(file)
        st.image(img, caption=f"商品 {idx+1}", use_container_width=True)
      except Exception:
        st.warning(f"商品 {idx+1} 格式錯誤")

st.divider()


# --- 2. 輔助函式 ---
def add_watermark_logo(img, text="SCVCN"):
  """在主圖加入質感品牌 Logo 標籤"""
  img_copy = img.copy().convert("RGBA")
  draw = ImageDraw.Draw(img_copy)
  w, h = img_copy.size

  box_w, box_h = int(w * 0.22), int(h * 0.07)
  margin = int(w * 0.04)
  draw.rectangle(
      [margin, margin, margin + box_w, margin + box_h], fill=(0, 0, 0, 200)
  )

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


def create_dimension_overlay(product_img, width_str, height_str, temple_str):
  """尺寸標示視覺圖"""
  img = product_img.copy().convert("RGBA")
  w, h = img.size
  draw = ImageDraw.Draw(img)

  color = (255, 70, 70, 255)
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

  try:
    font = ImageFont.truetype("arial.ttf", int(h * 0.045))
  except IOError:
    font = ImageFont.load_default()

  draw.text(
      (int(w * 0.35), int(h * 0.88)),
      f"Width: {width_str}",
      fill=(20, 20, 20, 255),
      font=font,
  )
  draw.text(
      (int(w * 0.05), int(h * 0.45)),
      f"Height: {height_str}",
      fill=(20, 20, 20, 255),
      font=font,
  )
  return img


# --- 3. 批量生成 7 大視覺亮點廣告大片 ---
st.subheader("2. 🚀 一鍵生成「視覺亮點」全套廣告大片")

if st.button("✨ 立即生成全套品牌視覺大片", type="primary"):
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
        st.markdown(f"### 👓 處理眼鏡素材：`{file.name}`")
        try:
          orig_img = Image.open(file).convert("RGBA")
        except Exception:
          st.error(f"❌ 檔案 {file.name} 格式解析失敗，請確認為 JPG 或 PNG。")
          continue

        # 網頁排版 (4 + 3 格)
        c1, c2, c3, c4 = st.columns(4)
        c5, c6, c7, c8 = st.columns(4)

        # 1. 主圖：黑火山岩展台 + 斜角空間層次
        with c1:
          st.caption("1️⃣ 品牌首圖 (展台 + 斜角構圖)")
          p1 = (
              "Commercial product stage backdrop, dark volcanic slate stone"
              " podium, dramatic rim lighting, cinematic depth of field, empty"
              " center"
          )
          bg1 = client.text_to_image(p1).convert("RGBA")

          bg_w, bg_h = bg1.size
          tw = int(bg_w * 0.52)
          th = int(tw * (orig_img.height / orig_img.width))
          resized = orig_img.resize((tw, th), Image.Resampling.LANCZOS)

          bg1.paste(resized, ((bg_w - tw) // 2, int(bg_h * 0.42)), mask=resized)
          img_main = add_watermark_logo(bg1, text=brand_logo_text)
          st.image(img_main, use_container_width=True)

        # 2. 抗UV / 偏光：強光光束 + 水花折射
        with c2:
          st.caption("2️⃣ 抗 UV / 偏光亮點 (強光束 + 水花折射)")
          p2 = (
              "Bright intense solar light beam spectrum passing through transparent"
              " water droplets, lens refraction light streaks, glare control"
              " visual effect, dark studio"
          )
          img_uv = client.text_to_image(p2)
          st.image(img_uv, use_container_width=True)

        # 3. 防霧 / 流線：動態風洞氣流
        with c3:
          st.caption("3️⃣ 防霧透氣亮點 (動態空氣流線)")
          p3 = (
              "Aerodynamic wind tunnel visual effect, white smooth smoke airflow"
              " lines swirling through air, high-speed motion trail, dark blue"
              " background"
          )
          img_fog = client.text_to_image(p3)
          st.image(img_fog, use_container_width=True)

        # 4. 極輕量：羽毛懸浮 + 漂浮微重力
        with c4:
          st.caption("4️⃣ 超輕量亮點 (羽毛懸浮 + 微重力漂浮)")
          p4 = (
              "Soft white feather floating in mid-air, levitation floating"
              " effect, zero gravity concept, clean soft lighting, ultra light"
              " feel"
          )
          img_light = client.text_to_image(p4)
          st.image(img_light, use_container_width=True)

        # 5. 耐用韌性：雙色鏡腳與機械切面放大
        with c5:
          st.caption("5️⃣ 耐用細節亮點 (雙色鏡腳機械特寫)")
          p5 = (
              "Macro close-up photography of neon yellow and black dual-color"
              " sports sunglass temples, precision engineered texture, sharp"
              " focus, metallic hinge details"
          )
          img_temple = client.text_to_image(p5)
          st.image(img_temple, use_container_width=True)

        # 6. 尺寸標示圖
        with c6:
          st.caption("6️⃣ 尺寸規格圖")
          img_dim = create_dimension_overlay(
              orig_img, glass_width, lens_height, temple_len
          )
          st.image(img_dim, use_container_width=True)

        # 7. 情境圖：真實人物 + 速度感景深
        with c7:
          st.caption("7️⃣ 動態使用情境 (戶外騎行 + 前後景深)")
          p7 = (
              "Professional cyclist wearing neon yellow athletic sunglasses"
              " riding fast on scenic highway, motion blur background, bright"
              " sunshine, action shot"
          )
          img_model = client.text_to_image(p7)
          st.image(img_model, use_container_width=True)

        # 打包儲存
        prefix = f"Product_{file_idx+1}"
        for img_obj, name in [
            (img_main, "01_Main_Logo.png"),
            (img_uv, "02_UV_LightBeam.png"),
            (img_fog, "03_Airflow_AntiFog.png"),
            (img_light, "04_Feather_Lightweight.png"),
            (img_temple, "05_Temple_Detail.png"),
            (img_dim, "06_Dimension_Specs.png"),
            (img_model, "07_Lifestyle_Action.png"),
        ]:
          buf = io.BytesIO()
          img_obj.convert("RGB").save(buf, format="PNG")
          zip_file.writestr(f"{prefix}/{name}", buf.getvalue())

        st.divider()

    st.success("🎉 全套視覺亮點廣告圖已生成完成！")
    st.download_button(
        label="📥 一鍵打包下載【全套廣告大片 (ZIP)】",
        data=all_zip_buffer.getvalue(),
        file_name="eyewear_visual_ad_pack.zip",
        mime="application/zip",
    )
