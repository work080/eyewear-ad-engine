import io
import zipfile
from huggingface_hub import InferenceClient
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# 頁面基本設定
st.set_page_config(
    page_title="眼鏡電商 ➔ AI 廣告視覺生成系統", page_icon="👓", layout="wide"
)

st.title("👓 眼鏡電商 ➔ 廣告視覺與賣點大片生成器")
st.caption("📷 支援批量去背 ➔ 🎨 自動將商品去背合成至 7 大賣點情境大片")

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


# --- 2. 輔助函式：去背與合成 ---
def remove_white_background(img):
  """將商品白底去背轉為透明 RGBA"""
  img = img.convert("RGBA")
  arr = np.array(img)
  r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
  # 偵測接近白色的背景並轉為透明
  white_mask = (r > 215) & (g > 215) & (b > 215)
  arr[white_mask, 3] = 0
  return Image.fromarray(arr, "RGBA")


def composite_glass_on_bg(bg_img, cutout_img, scale=0.55, y_offset=0):
  """將去背眼鏡完美合成到背景圖中央"""
  bg = bg_img.copy().convert("RGBA")
  bg_w, bg_h = bg.size

  target_w = int(bg_w * scale)
  w_percent = target_w / float(cutout_img.size[0])
  target_h = int(float(cutout_img.size[1]) * w_percent)
  resized_glass = cutout_img.resize(
      (target_w, target_h), Image.Resampling.LANCZOS
  )

  paste_x = (bg_w - target_w) // 2
  paste_y = (bg_h - target_h) // 2 + y_offset

  bg.paste(resized_glass, (paste_x, paste_y), mask=resized_glass)
  return bg


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
  """安全生成背景圖：若 API 失敗或未授權，自動轉為內建專業攝影棚底圖"""
  if client is not None:
    try:
      return client.text_to_image(prompt).convert("RGBA")
    except Exception:
      pass

  img = Image.new("RGBA", (1024, 1024), fallback_color + (255,))
  draw = ImageDraw.Draw(img)
  draw.rectangle(
      [100, 100, 924, 924], outline=(70, 70, 80, 255), width=6
  )
  try:
    font = ImageFont.truetype("arial.ttf", 36)
  except IOError:
    font = ImageFont.load_default()
  draw.text(
      (120, 120),
      "STUDIO COMMERCIAL BACKDROP",
      fill=(150, 150, 160, 200),
      font=font,
  )
  return img


def create_specs_overlay(
    product_img, width_str, height_str, bridge_str, temple_str, weight_str
):
  """尺寸與規格標示視覺圖"""
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
st.subheader("2. 🚀 一鍵去背與合成全套廣告大片")

if st.button("✨ 立即去背並合成全套大片", type="primary"):
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

        # 執行自動去背
        cutout_img = remove_white_background(orig_img)

        # 網頁排版 (4 + 3 格)
        c1, c2, c3, c4 = st.columns(4)
        c5, c6, c7, c8 = st.columns(4)

        # 1. 主圖：黑火山岩展台 + 合成眼鏡 + Logo
        with c1:
          st.caption("1️⃣ 品牌首圖 (展台合成)")
          p1 = (
              "Commercial product stage backdrop, dark volcanic slate stone"
              " podium, dramatic rim lighting, cinematic depth of field, empty"
              " center"
          )
          bg1 = safe_generate_image(client, p1, fallback_color=(20, 20, 25))
          composed_1 = composite_glass_on_bg(bg1, cutout_img, scale=0.55)
          img_main = add_watermark_logo(composed_1, text=brand_logo_text)
          st.image(img_main, use_container_width=True)

        # 2. 抗UV / 偏光：強光光束 + 水花折射合成
        with c2:
          st.caption("2️⃣ 抗 UV / 偏光亮點合成")
          p2 = (
              "Bright intense solar light beam spectrum passing through transparent"
              " water droplets, lens refraction light streaks, glare control"
              " visual effect, dark studio"
          )
          bg2 = safe_generate_image(client, p2, fallback_color=(15, 30, 45))
          img_uv = composite_glass_on_bg(bg2, cutout_img, scale=0.52)
          st.image(img_uv, use_container_width=True)

        # 3. 防霧 / 流線：動態風洞氣流合成
        with c3:
          st.caption("3️⃣ 防霧透氣亮點合成")
          p3 = (
              "Aerodynamic wind tunnel visual effect, white smooth smoke airflow"
              " lines swirling through air, high-speed motion trail, dark blue"
              " background"
          )
          bg3 = safe_generate_image(client, p3, fallback_color=(20, 35, 50))
          img_fog = composite_glass_on_bg(bg3, cutout_img, scale=0.52)
          st.image(img_fog, use_container_width=True)

        # 4. 極輕量：羽毛懸浮合成
        with c4:
          st.caption("4️⃣ 超輕量亮點合成")
          p4 = (
              "Soft white feather floating in mid-air, levitation floating"
              " effect, zero gravity concept, clean soft lighting, ultra light"
              " feel"
          )
          bg4 = safe_generate_image(client, p4, fallback_color=(40, 40, 45))
          img_light = composite_glass_on_bg(bg4, cutout_img, scale=0.52)
          st.image(img_light, use_container_width=True)

        # 5. 耐用韌性：高科技金屬背景合成
        with c5:
          st.caption("5️⃣ 耐用細節亮點合成")
          p5 = (
              "Macro close-up photography of precision engineered carbon fiber"
              " texture, sharp focus, metallic hinge details, dark studio"
          )
          bg5 = safe_generate_image(client, p5, fallback_color=(30, 30, 30))
          img_temple = composite_glass_on_bg(bg5, cutout_img, scale=0.55)
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

        # 7. 情境圖：戶外騎行背景合成
        with c7:
          st.caption("7️⃣ 動態使用情境合成")
          p7 = (
              "Professional cyclist riding fast on scenic highway, motion blur"
              " background, bright sunshine, action shot"
          )
          bg7 = safe_generate_image(client, p7, fallback_color=(20, 40, 30))
          img_model = composite_glass_on_bg(bg7, cutout_img, scale=0.55)
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

    st.success("🎉 全套去背與合成大片已生成完成！")
    st.download_button(
        label="📥 一鍵打包下載【全套廣告大片 (ZIP)】",
        data=all_zip_buffer.getvalue(),
        file_name="eyewear_visual_ad_pack.zip",
        mime="application/zip",
    )
