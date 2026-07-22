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
    "📷 支援批量上傳 ➔ 🎨 自動生成「光束、氣流、羽毛飄浮、水花」等 7 大賣點視覺大片"
)

st.divider()

# --- 側邊欄：設定區 ---
with st.sidebar:
  st.header("⚙️ 品牌與尺寸設定")
  hf_token = st.text_input(
      "Hugging Face Token (免費選填)",
      type="password",
      help="填入 Token 即可使用 AI 繪圖；不填則自動啟動專業內建底圖！",
  )
  brand_logo_text = st.text_input("品牌 Logo 文字", value="SCVCN")

  st.subheader("📐 商品尺寸與規格設定 (cm / g)")
  glass_width = st.text_input("鏡框總寬度", value="14.8 cm")
  lens_height = st.text_input("鏡片高度", value="6.0 cm")
  bridge_width = st.text_input("鼻寬 (Bridge Width)", value="2.0 cm")
  temple_len = st.text_input("鏡腳長度", value="12.5 cm")
  glass_weight = st.text_input("商品重量", value="28g")

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


def safe_generate_image(client, prompt, fallback_color=(25, 25, 30)):
  """安全生成圖片：若 API 失敗或未授權，自動轉為內建專業攝影棚底圖"""
  if client is not None:
    try:
      return client.text_to_image(prompt).convert("RGBA")
    except Exception:
      pass

  # 容錯備用底圖 (1024x1024)
  img = Image.new("RGBA", (1024, 1024), fallback_color + (255,))
  draw = ImageDraw.Draw(img)
  draw.rectangle(
      [100, 100, 924, 924], outline=(70, 70, 80, 255), width=6
  )
  try:
    font = ImageFont.truetype("arial.ttf", 36)
  except IOError:
    font = ImageFont.load_default()
  draw.text((120, 120), "STUDIO VISUAL BACKDROP", fill=(150, 150, 160, 200), font=font)
  return img


def create_specs_overlay(
    product_img, width_str, height_str, bridge_str, temple_str, weight_str
):
  """尺寸與規格標示視覺圖 (包含總寬、高、鼻寬、鏡腳長、重量)"""
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
    font_large = ImageFont.truetype("arial.ttf", int(h * 0.04))
    font_small = ImageFont.truetype("arial.ttf", int(h * 0.035))
  except IOError:
    font_large = font_small = ImageFont.load_default()

  draw.text(
      (int(w * 0.28), int(h * 0.88)),
      f"Total Width: {width_str}",
      fill=(20, 20, 20, 255),
      font=font_large,
  )
  draw.text(
      (int(w * 0.05), int(h * 0.40)),
      f"Lens Height: {height_str}",
      fill=(20, 20, 20, 255),
      font=font_small,
  )
  draw.text(
      (int(w * 0.05), int(h * 0.46)),
      f"Bridge Width: {bridge_str}",
      fill=(20, 20, 20, 255),
      font=font_small,
  )
  draw.text(
      (int(w * 0.05), int(h * 0.52)),
      f"Temple Len: {temple_str}",
      fill=(20, 20, 20, 255),
      font=font_small,
  )
  draw.text(
      (int(w * 0.05), int(h * 0.58)),
      f"Weight: {weight_str}",
      fill=(220, 40, 40, 255),
      font=font_large,
  )

  return img


# --- 3. 批量生成 7 大視覺亮點廣告大片 ---
st.subheader("2. 🚀 一鍵生成「視覺亮點」全套廣告大片")

if st.button("✨ 立即生成全套品牌視覺大片", type="primary"):
  if not uploaded_files:
    st.error("⚠️ 請先上傳至少一張眼鏡實拍照！")
  else:
    client = None
    if hf_token.strip():
      try:
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell", token=hf_token.strip()
        )
      except Exception:
        client = None

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
          bg1 = safe_generate_image(
              client, p1, fallback_color=(20, 20, 25)
          ).convert("RGBA")

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
          img_uv = safe_generate_image(client, p2, fallback_color=(15, 30, 45))
          st.image(img_uv, use_container_width=True)

        # 3. 防霧 / 流線：動態風洞氣流
        with c3:
          st.caption("3️⃣ 防霧透氣亮點 (動態空氣流線)")
          p3 = (
              "Aerodynamic wind tunnel visual effect, white smooth smoke airflow"
              " lines swirling through air, high-speed motion trail, dark blue"
              " background"
          )
          img_fog = safe_generate_image(client, p3, fallback_color=(20, 35, 50))
          st.image(img_fog, use_container_width=True)

        # 4. 極輕量：羽毛懸浮 + 漂浮微重力
        with c4:
          st.caption("4️⃣ 超輕量亮點 (羽毛懸浮 + 微重力漂浮)")
          p4 = (
              "Soft white feather floating in mid-air, levitation floating"
              " effect, zero gravity concept, clean soft lighting, ultra light"
              " feel"
          )
          img_light = safe_generate_image(
              client, p4, fallback_color=(40, 40, 45)
          )
          st.image(img_light, use_container_width=True)

        # 5. 耐用韌性：雙色鏡腳與機械切面放大
        with c5:
          st.caption("5️⃣ 耐用細節亮點 (雙色鏡腳機械特寫)")
          p5 = (
              "Macro close-up photography of neon yellow and black dual-color"
              " sports sunglass temples, precision engineered texture, sharp"
              " focus, metallic hinge details"
          )
          img_temple = safe_generate_image(
              client, p5, fallback_color=(30, 30, 30)
          )
          st.image(img_temple, use_container_width=True)

        # 6. 尺寸與重量規格圖
        with c6:
          st.caption("6️⃣ 尺寸與重量規格標示圖")
          img_dim = create_specs_overlay(
              orig_img,
              glass_width,
              lens_height,
              bridge_width,
              temple_len,
              glass_weight,
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
          img_model = safe_generate_image(
              client, p7, fallback_color=(20, 40, 30)
          )
          st.image(img_model, use_container_width=True)

        # 打包儲存
        prefix = f"Product_{file_idx+1}"
        for img_obj, name in [
            (img_main, "01_Main_Logo.png"),
            (img_uv, "02_UV_LightBeam.png"),
            (img_fog, "03_Airflow_AntiFog.png"),
            (img_light, "04_Feather_Lightweight.png"),
            (img_temple, "05_Temple_Detail.png"),
            (img_dim, "06_Dimensions_Specs.png"),
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
