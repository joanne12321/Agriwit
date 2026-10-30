# image_service.py -- 修复版 + 本地模板上传 + AI生成海报 + 语音识别
try:
    from pydub import AudioSegment
    AudioSegment.converter = r"C:\Users\29399\AppData\Local\Programs\Python\Python311\ffmpeg.exe"
    AudioSegment.ffprobe = r"C:\Users\29399\AppData\Local\Programs\Python\Python311\ffprobe.exe"
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import io, base64, os, uuid, threading, json, hashlib, time, hmac, hashlib
from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv(Path(__file__).parent / ".env", override=True)

print("=== .env 加载调试 ===")
print(f"ARK_API_KEY  是否加载成功: {bool(os.getenv('ARK_API_KEY'))}  |  长度={len(os.getenv('ARK_API_KEY') or '')}")
print(f"XUNFEI_APP_ID 是否加载成功: {bool(os.getenv('XUNFEI_APP_ID'))}")
print("=====================")
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename

# -- 环境变量配置 --
from dotenv import load_dotenv
load_dotenv()

# -- 火山引擎 ARK API（Doubao-Seedream 4.0）--
ARK_API_KEY = os.getenv('ARK_API_KEY', '')
ARK_IMAGE_MODEL = 'ep-20260413215220-krgdm'
ARK_IMAGE_API = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'

# -- GLM-4V 视觉模型（智谱 AI，用于智能构图排版）--
GLM_API_KEY = os.getenv('GLM_API_KEY', '')
GLM_VISION_MODEL = 'glm-4v-flash'
GLM_VISION_API = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

# -- 讯飞语音识别配置 --
XUNFEI_APP_ID = os.getenv('XUNFEI_APP_ID', '')
XUNFEI_API_KEY = os.getenv('XUNFEI_API_KEY', '')
XUNFEI_API_SECRET = os.getenv('XUNFEI_API_SECRET', '')
XUNFEI_WS_URL = 'wss://iat.cn-huabei-1.xf-yun.com/v1'

# -- rembg（懒加载）--
try:
    from rembg import remove as rembg_remove, new_session
    REMBG_AVAILABLE = True
    print(" rembg 库已找到")
except ImportError:
    REMBG_AVAILABLE = False
    print(" rembg 未安装，开发模式运?（合成功能正常，抠图跳过）")

_session = None
def get_session():
    global _session
    if _session is None and REMBG_AVAILABLE:
        print(" 加载 u2netp 模型…")
        try:
            _session = new_session("u2netp")
            print(" u2netp 加载成功")
        except Exception as e:
            print(f" u2netp 失败({e})，尝试 u2net…")
            try:
                _session = new_session("u2net")
                print(" u2net 加载成功")
            except Exception as e2:
                print(f" 模型均不可?: {e2}")
                return None
    return _session

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

TEMPLATES_DIR = Path("templates")
TEMPLATES_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}

task_store: dict[str, dict] = {}
executor = ThreadPoolExecutor(max_workers=2)

# -- 滤镜定义 --
FILTER_DEFS = {
    "original": {"name": "原图", "desc": "保持原⾊"},
    "warm": {"name": "暖调", "desc": "丰收⾦秋感"},
    "cool": {"name": "冷调", "desc": "清新⾃然感"},
    "vivid": {"name": "鲜艳", "desc": "⾊彩饱和"},
    "vintage": {"name": "复古", "desc": "胶⽚质感"},
    "soft": {"name": "柔和", "desc": "奶油磨⽪感"},
    "dramatic": {"name": "浓郁", "desc": "⾼对⽐⼤⽚感"},
    "bright": {"name": "明亮", "desc": "清爽通透感"},
    "green": {"name": "⽥园", "desc": "绿意盎然"},
}

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]

BUILTIN_TEMPLATES = [
    {"id": "green_gradient", "name": "清新绿渐变", "color": (208,234,208), "color2": (240,250,240)},
    {"id": "warm_yellow", "name": "丰收暖⻩", "color": (255,243,185), "color2": (255,250,215)},
    {"id": "earth_brown", "name": "⼤地棕", "color": (210,190,165), "color2": (235,220,200)},
    {"id": "sky_blue", "name": "天空蓝", "color": (185,220,245), "color2": (215,238,255)},
    {"id": "sakura_pink", "name": "樱花粉", "color": (255,215,215), "color2": (255,235,235)},
    {"id": "pure_white", "name": "简约⽩", "color": (252,252,252), "color2": (255,255,255)},
]

# ================================================
# ⼯具函数
# ================================================
def to_b64(image: Image.Image, fmt="PNG") -> str:
    """PIL Image -> base64 字符串"""
    buf = io.BytesIO()
    save_fmt = "JPEG" if fmt.upper() in ("JPG", "JPEG") else fmt.upper()
    if save_fmt == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buf, format=save_fmt, quality=92)
    buf.seek(0)  # ★ 关键修复：回到开头再读，否则读到空字节
    return base64.b64encode(buf.read()).decode()

def from_b64(b64: str) -> Image.Image:
    if "," in b64:
        b64 = b64.split(",")[1]
    return Image.open(io.BytesIO(base64.b64decode(b64)))

def make_gradient_bg(c1, c2, size=(1080, 1080)) -> Image.Image:
    """快速⽣成上下渐变背景（不⽤ putpixel 逐像素，改⽤ resize 放⼤）"""
    W, H = size
    # 只⽣成 1×H 的细条，然后⽔平拉伸 -> ⽐ putpixel 快⼏百倍
    strip = Image.new("RGB", (1, H))
    for y in range(H):
        r = y / H
        px = tuple(int(c1[i] + (c2[i] - c1[i]) * r) for i in range(3))
        strip.putpixel((0, y), px)
    return strip.resize((W, H), Image.NEAREST)

def load_background(template_id: str, size=(1080, 1080)) -> Image.Image:
    W, H = size
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = TEMPLATES_DIR / f"{template_id}{ext}"
        if p.exists():
            return Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
    t = next((t for t in BUILTIN_TEMPLATES if t["id"] == template_id), BUILTIN_TEMPLATES[0])
    return make_gradient_bg(t["color"], t["color2"], size).convert("RGBA")

def apply_filter(img: Image.Image, name: str) -> Image.Image:
    img = img.copy()
    if img.mode == "RGBA":
        img = img.convert("RGB")
    
    if name == "warm":
        r, g, b = img.split()
        img = Image.merge("RGB", (r.point(lambda x: min(255, int(x * 1.12 + 10))), g, b.point(lambda x: max(0, int(x * 0.88)))))
        img = ImageEnhance.Color(img).enhance(1.15)
    elif name == "cool":
        r, g, b = img.split()
        img = Image.merge("RGB", (r.point(lambda x: max(0, int(x * 0.88))), g, b.point(lambda x: min(255, int(x * 1.12 + 8)))))
    elif name == "vivid":
        img = ImageEnhance.Color(img).enhance(1.55)
        img = ImageEnhance.Contrast(img).enhance(1.25)
        img = ImageEnhance.Sharpness(img).enhance(1.35)
    elif name == "vintage":
        img = ImageEnhance.Color(img).enhance(0.65)
        img = ImageEnhance.Contrast(img).enhance(0.88)
        r, g, b = img.split()
        img = Image.merge("RGB", (r.point(lambda x: min(255, int(x * 1.12 + 18))), g, b.point(lambda x: max(0, int(x * 0.82)))))
    elif name == "soft":
        img = img.filter(ImageFilter.GaussianBlur(0.6))
        img = ImageEnhance.Brightness(img).enhance(1.06)
        img = ImageEnhance.Color(img).enhance(0.88)
    elif name == "dramatic":
        img = ImageEnhance.Contrast(img).enhance(1.45)
        img = ImageEnhance.Color(img).enhance(1.35)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
    elif name == "bright":
        img = ImageEnhance.Brightness(img).enhance(1.28)
        img = ImageEnhance.Color(img).enhance(1.12)
    elif name == "green":
        r, g, b = img.split()
        img = Image.merge("RGB", (r.point(lambda x: max(0, int(x * 0.94))), g.point(lambda x: min(255, int(x * 1.08 + 6))), b))
        img = ImageEnhance.Color(img).enhance(1.2)
    return img

def _font(size: int, bold=True):
    preferred = FONT_CANDIDATES if bold else FONT_CANDIDATES[1:] + FONT_CANDIDATES[:1]
    for path in preferred:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()

def _clean_text(text, max_len=18):
    text = str(text or "").strip()
    for ch in ["\n", "\r", "\t", "#", "，", "。", "！", "!", "～", "~", "…", "：", ":"]:
        text = text.replace(ch, " ")
    text = " ".join(text.split())
    return text[:max_len]

def _is_generic_request(text):
    text = str(text or "")
    return any(k in text for k in ["生成", "海报", "文案", "帮我", "给我", "带字", "做一张", "来一张"])

def _trim_transparent_border(img: Image.Image, padding=8) -> Image.Image:
    """裁掉抠图后的透明空白，避免主体被透明画布拖得很小。"""
    if img.mode != "RGBA":
        return img
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return img
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(img.width, x2 + padding)
    y2 = min(img.height, y2 + padding)
    return img.crop((x1, y1, x2, y2))

def _fit_font(draw, text, max_width, start_size, min_size=24, bold=True):
    size = start_size
    while size > min_size:
        fnt = _font(size, bold=bold)
        box = draw.textbbox((0, 0), text, font=fnt, stroke_width=2)
        if box[2] - box[0] <= max_width:
            return fnt
        size -= 4
    return _font(min_size, bold=bold)

def _draw_centered_text(draw, xy, text, font, fill, stroke_fill=None, stroke_width=0, anchor="mm"):
    draw.text(xy, text, font=font, fill=fill, anchor=anchor,
              stroke_width=stroke_width, stroke_fill=stroke_fill or fill)

def _draw_soft_text(draw, xy, text, font, fill, shadow=(0, 0, 0, 120), stroke_fill=None, stroke_width=0, anchor="mm"):
    x, y = xy
    for dx, dy in [(0, 5), (3, 5), (-3, 5)]:
        draw.text((x + dx, y + dy), text, font=font, fill=shadow, anchor=anchor,
                  stroke_width=stroke_width, stroke_fill=shadow)
    draw.text(xy, text, font=font, fill=fill, anchor=anchor,
              stroke_width=stroke_width, stroke_fill=stroke_fill or fill)

def _draw_label(draw, box, text, fill, outline, radius=26):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=radius, fill=outline)
    inset = max(8, int((y2 - y1) * 0.12))
    draw.rounded_rectangle((x1 + inset, y1 + inset, x2 - inset, y2 - inset),
                           radius=max(8, radius - inset), fill=fill)
    fnt = _fit_font(draw, text, x2 - x1 - inset * 4, int((y2 - y1) * 0.45), 18)
    _draw_centered_text(draw, ((x1 + x2) // 2, (y1 + y2) // 2), text, fnt, (24, 155, 208))

def _draw_rotated_text(base, text, center, angle, font_size, fill, stroke_fill, stroke_width=4):
    W, H = base.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    fnt = _font(font_size, bold=True)
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke_width)
    tw, th = box[2] - box[0], box[3] - box[1]
    x = int(center[0] - tw / 2)
    y = int(center[1] - th / 2)
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
    rotated = layer.rotate(angle, resample=Image.BICUBIC, center=center)
    return Image.alpha_composite(base.convert("RGBA"), rotated)

def build_poster_text(product_name="", ai_content="", tags=None, user_hint=""):
    """把长文案压成可上屏的海报文字层，后续可被前端编辑。"""
    tags = tags or []
    source = f"{product_name} {ai_content} {' '.join(tags)} {user_hint}"
    clean_product = "" if _is_generic_request(product_name) else product_name
    product = _clean_text(clean_product or "农产品", 12)

    is_tea = any(k in source for k in ["茶", "茶叶", "绿茶", "红茶", "乌龙", "白茶", "普洱", "岩茶", "单丛", "龙井", "毛尖"])
    is_fruit = any(k in source for k in ["果", "枣", "橘", "橙", "桃", "梨", "苹果", "葡萄", "番茄", "芒果", "荔枝", "西瓜"])

    if is_tea:
        candidate_words = ["清香", "回甘", "醇厚", "鲜爽", "耐泡", "原叶", "高山", "手作", "茶香", "兰香"]
        default_words = ["清香", "回甘", "醇厚"]
        scene = "好茶上新"
        badge = "原叶好茶 清香回甘"
        footer = product if product != "农产品" else "精选原叶茶"
        headline_tpl = "{0}{1} 好茶入杯"
    elif is_fruit:
        candidate_words = ["清甜", "脆爽", "爆汁", "多汁", "香甜", "酸甜", "无渣", "化渣", "新鲜", "现摘", "解腻", "清凉"]
        default_words = ["新鲜", "清甜", "多汁"]
        scene = "夏日清凉节" if any(k in source for k in ["夏", "清凉", "解暑"]) else "鲜果上新"
        badge = "午后解暑 鲜甜补给" if any(k in source for k in ["夏", "清凉", "解暑", "午后"]) else "产地直发 新鲜到家"
        footer = product if product != "农产品" else "A 级当季鲜果"
        headline_tpl = "{0}{1} 直击味蕾"
    else:
        candidate_words = ["原产", "优选", "新鲜", "地道", "安心", "实在", "品质", "自然"]
        default_words = ["产地", "优选", "品质"]
        scene = "农品上新"
        badge = "产地直发 品质到家"
        footer = product if product != "农产品" else "优选农产品"
        headline_tpl = "{0}{1} 品质之选"

    taste_words = []
    for kw in candidate_words:
        if kw in source and kw not in taste_words:
            taste_words.append(kw)
    if not taste_words:
        taste_words = default_words

    headline = headline_tpl.format(taste_words[0], taste_words[1] if len(taste_words) > 1 else "")
    subhead = " ".join(taste_words[:3])

    return {
        "event": _clean_text(scene, 8),
        "headline": _clean_text(headline, 14),
        "subhead": _clean_text(subhead, 10),
        "badge": _clean_text(badge, 12),
        "footer": _clean_text(footer, 12),
        "brand": _clean_text("云稼集 AgriWit", 16),
        "disclaimer": _clean_text("广告由云稼集智能生成", 18),
    }

def _sanitize_background_prompt(prompt):
    text = str(prompt or "")
    for word in ["带字", "有字", "加字", "文字", "文案", "标题", "海报文字", "给我生成", "帮我生成", "生成一张", "生成"]:
        text = text.replace(word, " ")
    text = " ".join(text.split())
    return text or "干净高级的农产品宣传背景"

def refine_poster_text(current, instruction):
    """轻量级文字修改：支持“主标题改成...”这类直接指令，也有兜底改写。"""
    current = dict(current or {})
    instruction = str(instruction or "").strip()
    field_aliases = {
        "headline": ["主标题", "大标题", "标题"],
        "subhead": ["副标题", "小标题"],
        "badge": ["贴纸", "角标", "弧形", "卖点"],
        "footer": ["底部", "产品名", "底栏"],
        "event": ["活动", "节日", "左上角"],
        "brand": ["品牌", "店铺"],
    }
    for field, aliases in field_aliases.items():
        if any(a in instruction for a in aliases):
            for sep in ["改成", "修改为", "换成", "变成", "写成", "：", ":"]:
                if sep in instruction:
                    value = instruction.split(sep, 1)[1].strip(" “”\"'")
                    if value:
                        current[field] = _clean_text(value, 18 if field in ["brand", "disclaimer"] else 14)
                        return current
    if "年轻" in instruction or "活泼" in instruction:
        if "茶" in "".join(current.values()):
            current["headline"] = "一杯清香 轻松回甘"
            current["subhead"] = "清香 回甘"
        else:
            current["headline"] = "一口爆汁 清爽开炫"
            current["subhead"] = "鲜甜多汁"
    elif "高级" in instruction or "质感" in instruction:
        current["headline"] = "原产甄选 品质之选"
        current["subhead"] = "地道 好物"
    elif "清凉" in instruction or "夏" in instruction:
        current["event"] = "夏日清凉节"
        current["headline"] = "清甜沁凉 直击燥热"
        current["badge"] = "午后解暑 鲜甜补给"
    elif instruction:
        current["headline"] = _clean_text(instruction, 14)
    return current

def render_text_poster(base_img: Image.Image, poster_text=None):
    poster_text = poster_text or {}
    img = base_img.convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cyan = (20, 166, 222, 255)
    white = (255, 255, 255, 255)
    yellow = (250, 238, 44, 255)
    deep = (0, 145, 204, 255)

    event = _clean_text(poster_text.get("event", "鲜果上新"), 8)
    _draw_label(draw, (int(W * 0.05), int(H * 0.04), int(W * 0.34), int(H * 0.12)), event, yellow, yellow)

    brand = _clean_text(poster_text.get("brand", "云稼集 AgriWit"), 16)
    brand_font = _fit_font(draw, brand, int(W * 0.28), int(H * 0.035), 18)
    draw.text((int(W * 0.72), int(H * 0.05)), brand, font=brand_font, fill=white,
              stroke_width=1, stroke_fill=(0, 120, 170, 180))

    headline = _clean_text(poster_text.get("headline", "清甜多汁 正当季"), 14)
    headline_font = _fit_font(draw, headline, int(W * 0.84), int(H * 0.085), 38)
    _draw_soft_text(draw, (W // 2, int(H * 0.23)), headline, headline_font, white,
                    stroke_fill=(0, 0, 0, 110), stroke_width=2)

    subhead = _clean_text(poster_text.get("subhead", "新鲜清甜"), 10)
    sub_font = _fit_font(draw, subhead, int(W * 0.5), int(H * 0.05), 28)
    _draw_soft_text(draw, (W // 2, int(H * 0.32)), subhead, sub_font, white,
                    stroke_fill=(0, 0, 0, 90), stroke_width=1)

    img = Image.alpha_composite(img, overlay)

    badge = _clean_text(poster_text.get("badge", "产地直发 新鲜到家"), 12)
    img = _draw_rotated_text(img, badge, (int(W * 0.70), int(H * 0.45)), -13,
                             max(30, int(H * 0.045)), yellow, deep, 5)

    draw = ImageDraw.Draw(img)
    footer = _clean_text(poster_text.get("footer", "A 级当季鲜果"), 12)
    foot_font = _fit_font(draw, footer, int(W * 0.55), int(H * 0.062), 28)
    draw.text((int(W * 0.05), int(H * 0.89)), footer, font=foot_font, fill=cyan,
              stroke_width=2, stroke_fill=white)

    disclaimer = _clean_text(poster_text.get("disclaimer", "广告由云稼集智能生成"), 18)
    small_font = _font(max(14, int(H * 0.014)), bold=False)
    draw.text((int(W * 0.05), int(H * 0.965)), disclaimer, font=small_font, fill=(16, 145, 196, 220))
    return img.convert("RGB")

def _analyze_brightness_zones(bg: Image.Image, grid=3):
    """
    分析背景图的明暗分布，返回每个区块的平均亮度。
    用于智能排版 —— 产品图应放在亮度较高（较空旷）的区域。
    """
    gray = bg.convert('L')
    W, H = gray.size
    cell_w, cell_h = W // grid, H // grid
    zones = []
    for row in range(grid):
        row_data = []
        for col in range(grid):
            box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
            region = gray.crop(box)
            pixels = list(region.getdata())
            avg = sum(pixels) / len(pixels) if pixels else 128
            # 计算方差（纹理复杂度）
            variance = sum((p - avg) ** 2 for p in pixels) / len(pixels) if pixels else 0
            row_data.append({'brightness': avg, 'variance': variance})
        zones.append(row_data)
    return zones

def _find_best_placement(zones, grid=3):
    """
    根据亮度分析找到最佳放置位置。
    优先选择：亮度高 + 纹理简单（方差低）的区域。
    """
    best_score = -1
    best_pos = (1, 1)  # 默认中心
    for row in range(grid):
        for col in range(grid):
            z = zones[row][col]
            # 分数 = 亮度越高越好 + 方差越低越好（空旷区域）
            score = z['brightness'] * 0.6 + max(0, 255 - z['variance'] ** 0.5) * 0.4
            if score > best_score:
                best_score = score
                best_pos = (col, row)
    return best_pos


def _img_to_b64_url(img: Image.Image, fmt='JPEG', max_side=512) -> str:
    """将 PIL Image 压缩为 base64 data URL（供 GLM-4V 使用）"""
    thumb = img.copy()
    thumb.thumbnail((max_side, max_side), Image.LANCZOS)
    if thumb.mode == 'RGBA' and fmt == 'JPEG':
        bg = Image.new('RGB', thumb.size, (255, 255, 255))
        bg.paste(thumb, mask=thumb.split()[3])
        thumb = bg
    buf = io.BytesIO()
    thumb.save(buf, format=fmt, quality=80)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    mime = 'image/jpeg' if fmt == 'JPEG' else 'image/png'
    return f'data:{mime};base64,{b64}'


def _glm_vision_compose(bg: Image.Image, cutout: Image.Image, W: int, H: int) -> dict:
    """
    使用 GLM-4V 视觉模型分析背景和产品图，返回最佳贴图参数。
    
    返回: {'x_pct': 0.5, 'y_pct': 0.65, 'scale': 0.55} 或 None（失败时）
    x_pct, y_pct 是产品图中心点相对于画布的百分比位置
    scale 是产品图相对于画布短边的缩放比例
    """
    if not GLM_API_KEY:
        return None
    
    import requests as http
    
    bg_url = _img_to_b64_url(bg, 'JPEG')
    cutout_url = _img_to_b64_url(cutout, 'PNG')
    
    prompt = """你是专业的平面设计排版 AI。

我会给你两张图：
- 第一张是海报背景（尺寸 %dx%d）
- 第二张是抠好的产品图（透明背景）

请分析背景的构图、颜色分布、空旷区域，然后告诉我把产品图贴在背景上的最佳位置和大小。

要求：
1. 产品图应放在背景的空旷/干净区域，避开复杂纹理
2. 产品图大小要协调，不能太大遮住背景，也不能太小看不清
3. 整体构图要美观、有设计感

请严格按以下 JSON 格式回答，不要输出任何其他文字：
{"x_pct": 0.5, "y_pct": 0.6, "scale": 0.45}

其中：
- x_pct: 产品图中心点在背景上的水平位置（0=最左, 1=最右）
- y_pct: 产品图中心点在背景上的垂直位置（0=最上, 1=最下）
- scale: 产品图缩放比例（相对于背景短边，0.3~0.8之间）""" % (W, H)
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GLM_API_KEY}'
    }
    
    payload = {
        'model': GLM_VISION_MODEL,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': bg_url}},
                {'type': 'image_url', 'image_url': {'url': cutout_url}},
            ]
        }],
        'max_tokens': 200,
        'temperature': 0.1,
    }
    
    try:
        print(f'  [GLM-4V] 发送背景+产品图进行智能构图分析...')
        resp = http.post(GLM_VISION_API, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f'  [GLM-4V] 原始回复: {content[:200]}')
        
        # 从回复中提取 JSON
        import re
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            result = json.loads(json_match.group())
            x_pct = float(result.get('x_pct', 0.5))
            y_pct = float(result.get('y_pct', 0.5))
            s = float(result.get('scale', 0.5))
            # 安全范围校验
            x_pct = max(0.1, min(0.9, x_pct))
            y_pct = max(0.1, min(0.9, y_pct))
            s = max(0.2, min(0.85, s))
            print(f'  [GLM-4V] 智能构图: x={x_pct:.2f}, y={y_pct:.2f}, scale={s:.2f}')
            return {'x_pct': x_pct, 'y_pct': y_pct, 'scale': s}
        else:
            print(f'  [GLM-4V] 无法解析 JSON')
            return None
    except Exception as e:
        print(f'  [GLM-4V] 调用失败: {e}')
        return None


def composite(cutout: Image.Image, template_id: str, size, position="center", scale=0.62, 
              alignment="center", auto_composition=False, template_type="builtin") -> Image.Image:
    """
    合成海报，支持 GLM-4V 视觉智能构图
    
    优先级：
        1. GLM-4V 视觉模型（如果配置了 GLM_API_KEY）
        2. 亮度分析自适应构图
        3. 手动指定位置
    """
    W, H = int(size[0]), int(size[1])
    bg = load_background(template_id, (W, H))
    cutout = cutout.copy()
    
    use_glm = (GLM_API_KEY and 
               (auto_composition or position in ['smart', 'intelligent'] or template_type in ['file', 'ai']))
    
    # ========================
    # 路径 A: GLM-4V 智能构图
    # ========================
    if use_glm:
        glm_result = _glm_vision_compose(bg, cutout, W, H)
        if glm_result:
            s = glm_result['scale']
            if template_type in ['file', 'ai'] or auto_composition:
                s = max(s, 0.58)
            short_side = min(W, H)
            target_size = int(short_side * s)
            # 等比缩放
            cw0, ch0 = cutout.size
            ratio = target_size / max(cw0, ch0)
            new_w, new_h = int(cw0 * ratio), int(ch0 * ratio)
            cutout = cutout.resize((new_w, new_h), Image.LANCZOS)
            # 按百分比定位（中心点）
            x_pct = glm_result['x_pct']
            y_pct = glm_result['y_pct']
            if y_pct < 0.48:
                y_pct = 0.58
            cx = int(W * x_pct)
            cy = int(H * y_pct)
            x = cx - new_w // 2
            y = cy - new_h // 2
            x = max(0, min(x, W - new_w))
            y = max(0, min(y, H - new_h))
            print(f'  [OK] GLM-4V 构图: 产品({new_w}x{new_h}) @ ({x},{y})')
            poster = bg.copy()
            poster.paste(cutout, (x, y), cutout)
            return poster
        else:
            print(f'  [!] GLM-4V 失败，回退亮度分析')
    
    # ========================
    # 路径 B: 亮度分析 / 手动
    # ========================
    if auto_composition or template_type == 'ai':
        scale = max(0.9, min(scale, 1.05))
    elif template_type == 'file':
        scale = max(0.78, min(scale, 0.95))
    
    cutout.thumbnail((int(W * scale), int(H * scale)), Image.LANCZOS)
    cw, ch = cutout.size
    
    if position in ['smart', 'intelligent'] or (auto_composition and template_type == 'file'):
        if template_type == 'ai' or auto_composition:
            x = int(W * 0.5 - cw // 2)
            y = int(H * 0.60 - ch // 2)
            print(f'  智能排版: 海报文字模式主体居中偏下，位置=({x},{y})')
        else:
          try:
            zones = _analyze_brightness_zones(bg, grid=3)
            best_col, best_row = _find_best_placement(zones, grid=3)
            cell_w, cell_h = W // 3, H // 3
            center_x = best_col * cell_w + cell_w // 2
            center_y = max(best_row * cell_h + cell_h // 2, int(H * 0.48))
            x = center_x - cw // 2
            y = center_y - ch // 2
            print(f'  智能排版: 最佳区块=({best_col},{best_row}), 位置=({x},{y})')
          except Exception as e:
            print(f'  智能排版分析失败，使用居中: {e}')
            x = (W - cw) // 2
            y = int(H * 0.60 - ch // 2)
    else:
        if alignment == 'left':
            x = int(W * 0.1)
        elif alignment == 'right':
            x = W - cw - int(W * 0.1)
        else:
            x = (W - cw) // 2
        
        if position == 'bottom':
            y = H - ch - int(H * 0.08)
        elif position == 'top':
            y = int(H * 0.08)
        else:
            y = (H - ch) // 2
    
    x = max(0, min(x, W - cw))
    y = max(0, min(y, H - ch))
    
    poster = bg.copy()
    poster.paste(cutout, (x, y), cutout)
    return poster

# ================================================
# 后台任务
# ================================================
def _do_remove_bg(task_id: str, img_bytes: bytes, template_id: str,
                  size: list, position: str, filters: list, scale=0.62, 
                  alignment="center", auto_composition=False, template_type="builtin",
                  poster_text=None, product_name="", ai_content="", render_text=True):
    try:
        task_store[task_id].update({"status": "processing", "progress": 5, "step": "准备中…"})
        
        # -- Step 1：抠图 --
        task_store[task_id].update({"progress": 10, "step": "正在抠图…"})
        sess = get_session() if REMBG_AVAILABLE else None
        if sess:
            task_store[task_id].update({"progress": 15, "step": "AI 模型已加载，识别主体中…"})
            cutout_bytes = rembg_remove(img_bytes, session=sess)
            cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")
            cutout = _trim_transparent_border(cutout, padding=12)
            task_store[task_id].update({"progress": 50, "step": "抠图完成，合成海报中…"})
        else:
            # ⽆模型：直接⽤原图（背景不透明，合成效果稍差但能⽤）
            task_store[task_id].update({"progress": 50, "step": "跳过抠图（模型未就绪），合成中…"})
            cutout = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            cutout = _trim_transparent_border(cutout, padding=12)
        
        # -- Step 2：合成 + 滤镜 + 可编辑文字层 --
        if GLM_API_KEY and (auto_composition or template_type in ['file', 'ai']):
            task_store[task_id].update({"progress": 52, "step": "GLM-4V 智能分析最佳构图位置..."})
        else:
            task_store[task_id].update({"progress": 55, "step": "正在合成海报..."})
        poster = composite(cutout, template_id, size, position, scale, alignment, auto_composition, template_type)
        if render_text:
            poster_text = poster_text or build_poster_text(product_name, ai_content)
        versions = {}
        total = len(filters)
        for i, fname in enumerate(filters):
            if fname in FILTER_DEFS:
                filtered_base = apply_filter(poster, fname)
                filtered = render_text_poster(filtered_base, poster_text) if render_text else filtered_base
                thumb = filtered.copy()
                thumb.thumbnail([360, 360], Image.LANCZOS)
                versions[fname] = {
                    "name": FILTER_DEFS[fname]["name"],
                    "base_image": f"data:image/jpeg;base64,{to_b64(filtered_base, 'JPEG')}",
                    "image": f"data:image/jpeg;base64,{to_b64(filtered, 'JPEG')}",
                    "thumbnail": f"data:image/jpeg;base64,{to_b64(thumb, 'JPEG')}"
                }
                pct = 55 + int((i + 1) / total * 40)
                task_store[task_id].update({"progress": pct, "step": f"⽣成滤镜 {i+1}/{total}：{FILTER_DEFS.get(fname,{}).get('name','')}…"})
        
        cutout_b64 = f"data:image/png;base64,{to_b64(cutout, 'PNG')}"
        task_store[task_id].update({
            "status": "done",
            "progress": 100,
            "step": "完成！",
            "cutout_base64": cutout_b64,
            "poster_versions": versions,
            "poster_text": poster_text or {},
        })
        print(f" 任务完成 [{task_id[:8]}] {len(versions)} 个版本")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        task_store[task_id].update({"status": "error", "error": str(e), "progress": 0, "step": f"失败：{e}"})
        print(f" 任务失败 [{task_id[:8]}]: {e}")

# ================================================
# 接⼝ 1：提交任务（支持自适应构图智能排版）
# ================================================
@app.route('/api/image/full-pipeline', methods=['POST'])
def full_pipeline():
    data = request.json
    image_b64 = data.get("image_base64", "")
    template_id = data.get("template_id", "green_gradient")
    template_type = data.get("template_type", "builtin")
    size = data.get("size", [1080, 1080])
    position = data.get("position", "center")
    scale = data.get("scale", 0.62)
    alignment = data.get("alignment", "center")
    auto_composition = data.get("auto_composition", False)
    filters = data.get("filters", ["original", "warm", "vivid", "vintage"])
    poster_text = data.get("poster_text") or None
    product_name = data.get("product_name", "")
    ai_content = data.get("ai_content", "")
    render_text = data.get("render_text", True)
    
    if not image_b64:
        return jsonify({"error": "请提供图⽚"}), 400
    
    b64 = image_b64.split(",")[1] if "," in image_b64 else image_b64
    img_bytes = base64.b64decode(b64)
    
    task_id = str(uuid.uuid4())
    task_store[task_id] = {"status": "queued", "progress": 0, "step": "等待处理…"}
    executor.submit(_do_remove_bg, task_id, img_bytes, template_id, size, position, 
                   filters, scale, alignment, auto_composition, template_type,
                   poster_text, product_name, ai_content, render_text)
    
    print(f" 任务已提交 [{task_id[:8]}]")
    return jsonify({"task_id": task_id, "status": "queued"})

# ================================================
# 接⼝ 2：查询进度
# ================================================
@app.route('/api/task/<task_id>', methods=['GET'])
def get_task(task_id):
    task = task_store.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    
    if task.get("status") == "done":
        def cleanup():
            import time
            time.sleep(120)
            task_store.pop(task_id, None)
        threading.Thread(target=cleanup, daemon=True).start()
    
    return jsonify(task)

@app.route('/api/poster/text-draft', methods=['POST'])
def poster_text_draft():
    data = request.json or {}
    text = build_poster_text(
        product_name=data.get("product_name", ""),
        ai_content=data.get("ai_content", ""),
        tags=data.get("tags", []),
        user_hint=data.get("user_hint", ""),
    )
    return jsonify({"success": True, "poster_text": text})

@app.route('/api/poster/refine-text', methods=['POST'])
def poster_refine_text():
    data = request.json or {}
    current = data.get("poster_text") or {}
    instruction = data.get("instruction", "")
    refined = refine_poster_text(current, instruction)
    return jsonify({"success": True, "poster_text": refined})

@app.route('/api/poster/render-text', methods=['POST'])
def poster_render_text():
    data = request.json or {}
    base_b64 = data.get("base_image") or data.get("image_base64") or ""
    poster_text = data.get("poster_text") or {}
    if not base_b64:
        return jsonify({"success": False, "error": "请提供海报底图"}), 400
    try:
        base = from_b64(base_b64).convert("RGB")
        rendered = render_text_poster(base, poster_text)
        thumb = rendered.copy()
        thumb.thumbnail([360, 360], Image.LANCZOS)
        return jsonify({
            "success": True,
            "image": f"data:image/jpeg;base64,{to_b64(rendered, 'JPEG')}",
            "thumbnail": f"data:image/jpeg;base64,{to_b64(thumb, 'JPEG')}",
            "poster_text": poster_text,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ================================================
# bg_01、bg_02 等文件名 -> 友好显示名称映射
# 按你⾃⼰的模板数量和含义修改这⾥即可
# ================================================
BG_NAME_MAP = {
    "bg_01": "田园清新",
    "bg_02": "简约原木",
    "bg_03": "传统瓷器",
    "bg_04": "大地棕调",
    "bg_05": "水墨国风",
    "bg_06": "典雅绿意",
    "bg_07": "花海烂漫",
    "bg_08": "蓝天云朵",
    "bg_09": "复古报纸",
    "bg_10": "丰收果园",
    
}

def get_bg_display_name(stem: str) -> str:
    """bg_01 -> 映射名；找不到映射则把下划线换成空格"""
    return BG_NAME_MAP.get(stem, stem.replace("_", " ").replace("-", " "))

# ================================================
# 接⼝ 3：获取模板列表
# ================================================
@app.route('/api/templates', methods=['GET'])
def get_templates():
    templates = []
    
    # ⽤户上传的⾃定义模板（包含 bg_01.jpg 等）
    if TEMPLATES_DIR.exists():
        for f in sorted(TEMPLATES_DIR.iterdir()):
            if f.suffix.lower() in ALLOWED_EXTENSIONS:
                try:
                    img = Image.open(f).convert("RGB")
                    img.thumbnail((300, 300), Image.LANCZOS)
                    templates.append({
                        "id": f.stem,
                        "name": get_bg_display_name(f.stem),  # <- ⽤映射名
                        "type": "file",
                        "thumbnail": f"data:image/jpeg;base64,{to_b64(img, 'JPEG')}"
                    })
                except Exception as e:
                    print(f" 读模板失败 {f.name}: {e}")
    
    # 内置渐变模板
    for t in BUILTIN_TEMPLATES:
        bg = make_gradient_bg(t["color"], t["color2"], (300, 300))
        # 写名称（不依赖 anchor 参数，兼容⽼版本 Pillow）
        try:
            draw = ImageDraw.Draw(bg)
            draw.text((150, 150), t["name"], fill=(80, 80, 80))
        except Exception:
            pass
        templates.append({
            "id": t["id"],
            "name": t["name"],
            "type": "builtin",
            "thumbnail": f"data:image/jpeg;base64,{to_b64(bg, 'JPEG')}"
        })
    
    return jsonify({"templates": templates, "count": len(templates)})

# ================================================
# 接⼝ 4：上传本地模板图⽚（新增）
# ================================================
@app.route('/api/templates/upload', methods=['POST'])
def upload_template():
    """
    上传⾃定义背景模板图⽚。
    ⽀持 multipart/form-data，字段名 file 或 image。
    上传成功后⾃动出现在模板列表⾥。
    """
    file = request.files.get('file') or request.files.get('image')
    if not file or not file.filename:
        return jsonify({"error": "请选择图⽚文件"}), 400
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"只⽀持 jpg/png/webp，收到: {suffix}"}), 400
    
    # ⽤ secure_filename 防路径注⼊，保留原始名（去除特殊字符）
    safe_name = secure_filename(file.filename)
    save_path = TEMPLATES_DIR / safe_name
    
    # 如果同名已存在，加序号
    if save_path.exists():
        stem = Path(safe_name).stem
        counter = 1
        while save_path.exists():
            save_path = TEMPLATES_DIR / f"{stem}_{counter}{suffix}"
            counter += 1
    
    file.save(str(save_path))
    
    # ⽣成缩略图预览
    try:
        img = Image.open(save_path).convert("RGB")
        img.thumbnail((300, 300), Image.LANCZOS)
        thumb_b64 = f"data:image/jpeg;base64,{to_b64(img, 'JPEG')}"
    except Exception as e:
        return jsonify({"error": f"图⽚处理失败: {e}"}), 500
    
    print(f" 模板已上传：{save_path.name}")
    return jsonify({
        "success": True,
        "id": save_path.stem,
        "name": save_path.stem.replace("_", " ").replace("-", " "),
        "type": "file",
        "thumbnail": thumb_b64,
        "message": f"模板「{save_path.stem}」上传成功"
    })

# ================================================
# 接⼝ 5：删除⾃定义模板
# ================================================
@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    for ext in ALLOWED_EXTENSIONS:
        p = TEMPLATES_DIR / f"{template_id}{ext}"
        if p.exists():
            p.unlink()
            return jsonify({"success": True, "message": f"已删除 {template_id}"})
    return jsonify({"error": "模板不存在"}), 404

# ================================================
# 接⼝ 6：滤镜列表
# ================================================
@app.route('/api/filters', methods=['GET'])
def get_filters():
    return jsonify({"filters": [{"id": k, "name": v["name"], "desc": v["desc"]} for k, v in FILTER_DEFS.items()]})

# ================================================
# 接⼝ 7：单独抠图
# ================================================
@app.route('/api/image/remove-bg', methods=['POST'])
def remove_bg():
    try:
        if request.files and 'image' in request.files:
            img_bytes = request.files['image'].read()
        else:
            b64 = request.json.get('image_base64', '')
            if ',' in b64: 
                b64 = b64.split(',')[1]
            img_bytes = base64.b64decode(b64)
        
        sess = get_session() if REMBG_AVAILABLE else None
        if sess:
            result = Image.open(io.BytesIO(rembg_remove(img_bytes, session=sess))).convert("RGBA")
        else:
            result = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        
        return jsonify({"success": True, "cutout_base64": f"data:image/png;base64,{to_b64(result, 'PNG')}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================
# 接⼝ 8：使用 Doubao-Seedream 4.0 AI 生成海报背景
#         通过火山引擎 ARK OpenAPI
# ================================================
@app.route('/api/ai/generate-poster', methods=['POST'])
def generate_poster():
    """
    使用 Doubao-Seedream 4.0 通过火山引擎 ARK API 生成海报背景图片

    请求参数：
        prompt: 文字描述，描述想要的海报风格
        size: 图片尺寸比例，可选 '1024x1024', '768x1024', '1024x768'
        style: 风格提示，会追加到 prompt
    返回：
        template_id / thumbnail / type 等
    """
    try:
        data = request.json
        prompt = data.get("prompt", "")
        size_str = data.get("size", "1024x1024")
        style = data.get("style", "")

        if not prompt.strip():
            return jsonify({"error": "请提供文字描述"}), 400

        # 如果没有配置 ARK_API_KEY，返回错误
        if not ARK_API_KEY:
            print("  [!] 未配置 ARK_API_KEY")
            return jsonify({
                "success": False,
                "error": "未配置 ARK_API_KEY，请在 .env 文件中配置后重启 image_service.py"
            }), 400

        # -- 构建农产品海报专用 prompt --
        visual_prompt = _sanitize_background_prompt(prompt)
        full_prompt = f"为农产品设计一张高品质宣传海报背景图，{visual_prompt}"
        if style:
            full_prompt += f"，风格：{style}"
        full_prompt += "。要求：无文字、干净大气、适合放置产品图和文案叠加。"

        import requests as http
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ARK_API_KEY}"
        }

        payload = {
            "model": ARK_IMAGE_MODEL,
            "prompt": full_prompt,
            "size": size_str,          # "1024x1024" / "768x1024" / "1024x768"
            "response_format": "b64_json",
            "n": 1,
            # seed 可不传，API 自动随机
        }

        print(f"  [*] 调用 Doubao-Seedream 4.0 -> {full_prompt[:50]}...")
        response = http.post(ARK_IMAGE_API, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        # ARK 返回格式: { "data": [ { "b64_json": "...", "index": 0 } ], "created": ... }
        items = result.get("data", [])
        if not items:
            print(f"  [X] ARK 返回数据为空: {result}")
            return generate_poster_mock(prompt, size_str)

        img_b64 = items[0].get("b64_json", "")
        if not img_b64:
            # 也可能返回 url
            img_url = items[0].get("url", "")
            if img_url:
                img_resp = http.get(img_url, timeout=60)
                img_b64 = base64.b64encode(img_resp.content).decode()
            else:
                return generate_poster_mock(prompt, size_str)

        # 解码并保存
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        template_id = f"ai_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}"
        save_path = TEMPLATES_DIR / f"{template_id}.png"
        img.save(str(save_path), format="PNG")

        # 缩略图
        thumb = img.copy()
        thumb.thumbnail((300, 300), Image.LANCZOS)
        thumb_b64 = f"data:image/jpeg;base64,{to_b64(thumb, 'JPEG')}"

        print(f"  [OK] AI 海报生成成功：{save_path.name}")
        return jsonify({
            "success": True,
            "template_id": template_id,
            "name": "AI生成-" + prompt[:20],
            "type": "ai",
            "thumbnail": thumb_b64,
            "auto_composition": True
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return generate_poster_mock(prompt, data.get("size", "1024x1024") if 'data' in dir() else "1024x1024")


def generate_poster_mock(prompt, size_str="1024x1024"):
    """模拟生成海报背景（当 API 不可用时）"""
    parts = size_str.split('x')
    W = int(parts[0]) if len(parts) == 2 else 1080
    H = int(parts[1]) if len(parts) == 2 else 1080

    # 根据 prompt 关键词生成不同风格的背景
    bg_color1, bg_color2 = (208, 234, 208), (240, 250, 240)
    if "复古" in prompt or "怀旧" in prompt:
        bg_color1, bg_color2 = (210, 190, 165), (235, 220, 200)
    elif "蓝" in prompt or "天空" in prompt:
        bg_color1, bg_color2 = (185, 220, 245), (215, 238, 255)
    elif "粉" in prompt or "浪漫" in prompt:
        bg_color1, bg_color2 = (255, 215, 215), (255, 235, 235)
    elif "金" in prompt or "丰收" in prompt:
        bg_color1, bg_color2 = (255, 243, 185), (255, 250, 215)
    elif "红" in prompt or "喜庆" in prompt:
        bg_color1, bg_color2 = (220, 80, 60), (255, 180, 160)

    bg = make_gradient_bg(bg_color1, bg_color2, (W, H))
    try:
        draw = ImageDraw.Draw(bg)
        draw.text((W // 2 - 60, H // 2), "AI 海报", fill=(180, 180, 180))
    except Exception:
        pass

    template_id = f"ai_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}"
    save_path = TEMPLATES_DIR / f"{template_id}.png"
    bg.save(str(save_path), format="PNG")

    thumb = bg.copy()
    thumb.thumbnail((300, 300), Image.LANCZOS)
    thumb_b64 = f"data:image/jpeg;base64,{to_b64(thumb, 'JPEG')}"

    print(f"  [~] 模拟 AI 海报：{save_path.name}")
    return jsonify({
        "success": True,
        "template_id": template_id,
        "name": "AI生成-" + prompt[:20],
        "type": "ai",
        "thumbnail": thumb_b64,
        "auto_composition": True,
        "message": "模拟生成（未配置 ARK_API_KEY，请在 .env 配置后启用 Doubao-Seedream 4.0）"
    })

# ================================================
# 接⼝ 9：直播脚本生成
# ================================================
@app.route('/api/ai/generate-live-script', methods=['POST'])
def generate_live_script():
    """
    生成直播脚本
    
    请求参数：
        product_name: 产品名称
        platform: 平台（抖音、快手、视频号等）
        user_id: 用户ID
        duration: 时长（秒）
        style: 风格（fresh清新、humorous幽默、professional专业等）
    
    返回：
        script: 生成的直播脚本
    """
    try:
        data = request.json
        product_name = data.get("product_name", "农产品")
        platform = data.get("platform", "抖音")
        duration = data.get("duration", 30)
        style = data.get("style", "fresh")
        
        # 生成直播脚本
        script = generate_script_content(product_name, platform, duration, style)
        
        return jsonify({
            "success": True,
            "script": script
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "script": generate_mock_script(product_name, platform)
        })

def generate_script_content(product_name, platform, duration, style):
    """生成直播脚本内容"""
    script_parts = []
    
    # 开场
    script_parts.append({
        "part": "开场",
        "time": "0-3秒",
        "content": f"哈喽家人们！欢迎来到我的直播间！今天给大家带来一款超级棒的{product_name}！"
    })
    
    # 产品介绍
    script_parts.append({
        "part": "产品介绍",
        "time": "3-10秒",
        "content": f"这款{product_name}是我们自家农场种植的，纯天然、无污染，品质绝对保证！"
    })
    
    # 产品特点
    script_parts.append({
        "part": "产品特点",
        "time": "10-20秒",
        "content": "大家看这个色泽，多么新鲜！口感更是没话说，咬一口满满的幸福感！"
    })
    
    # 福利环节
    script_parts.append({
        "part": "福利时间",
        "time": "20-27秒",
        "content": "今天直播间专属福利！原价XX元，现在下单只要XX元！数量有限，先到先得！"
    })
    
    # 引导下单
    script_parts.append({
        "part": "引导下单",
        "time": "27-30秒",
        "content": "点击下方购物车立即抢购！家人们冲啊！"
    })
    
    return script_parts

def generate_mock_script(product_name, platform):
    """模拟生成直播脚本"""
    return [
        {"part": "开场", "time": "0-3秒", "content": f"哈喽家人们！欢迎来到我的直播间！今天给大家带来{product_name}！"},
        {"part": "产品介绍", "time": "3-10秒", "content": f"这款{product_name}品质非常好，大家不要错过！"},
        {"part": "产品特点", "time": "10-20秒", "content": "新鲜采摘，品质保证，口感绝佳！"},
        {"part": "福利时间", "time": "20-27秒", "content": "直播间专属优惠，限时抢购！"},
        {"part": "引导下单", "time": "27-30秒", "content": "点击购物车立即购买！"}
    ]

# ================================================
# 接口 10：讯飞语音识别（修复版 —— 正确的 RFC2616 鉴权）
# ================================================
def _build_xunfei_ws_url():
    """
    按照讯飞 IAT WebSocket 文档构建带签名的 URL：
    1. 用 RFC2616 格式的 date
    2. 拼接签名原文：host + date + request-line
    3. HMAC-SHA256(api_secret, signature_origin) -> base64
    4. 拼成 authorization header -> base64 -> 放 URL 参数
    """
    from datetime import datetime as dt, timezone
    from urllib.parse import urlencode, quote
    import hmac as _hmac

    # RFC2616 格式时间
    now = dt.now(timezone.utc)
    date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

    host = 'iat.cn-huabei-1.xf-yun.com'
    request_line = 'GET /v1 HTTP/1.1'

    signature_origin = f'host: {host}\ndate: {date}\n{request_line}'
    signature_sha = _hmac.new(
        XUNFEI_API_SECRET.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')

    authorization_origin = (
        f'api_key="{XUNFEI_API_KEY}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

    params = {
        'authorization': authorization,
        'date': date,
        'host': host,
    }
    ws_url = XUNFEI_WS_URL + '?' + urlencode(params)
    return ws_url


# 讯飞方言 accent 映射（讯飞 IAT accent 参数值）
XUNFEI_ACCENT_MAP = {
    'mandarin':  'mandarin',
    'cantonese': 'cantonese',
    'sichuan':   'lmz',        # 四川话
    'henan':     'henanese',    # 河南话
    'shandong':  'mandarin',    # 山东话用普通话兜底
    'zhejiang':  'mandarin',
    'fujian':    'minnan',      # 闽南语
}


@app.route('/api/voice/recognize', methods=['POST'])
def voice_recognize():
    """
    讯飞语音识别（WebSocket IAT）

    请求：{ audio_base64, dialect, format }
    返回：{ success, text, dialect }
    """
    data = request.json or {}
    dialect = data.get('dialect', 'mandarin')

    try:
        audio_base64 = data.get('audio_base64', '')
        audio_format = data.get('format', 'wav')

        if not audio_base64:
            return jsonify({'error': '请提供音频数据'}), 400

        if not XUNFEI_APP_ID or not XUNFEI_API_KEY or not XUNFEI_API_SECRET:
            print('  [!] 未配置讯飞 API，使用模拟识别')
            return recognize_mock(dialect)

        # 解码音频
        if ',' in audio_base64:
            audio_base64 = audio_base64.split(',')[1]
        audio_bytes = base64.b64decode(audio_base64)

        if not PYDUB_AVAILABLE:
          print("  [!] pydub 未安装，无法转码语音，使用模拟识别")
          return recognize_mock(dialect)

        try:
          audio_file = io.BytesIO(audio_bytes)
    # 自动识别格式并读取
          audio = AudioSegment.from_file(audio_file)
    # 强制转为 16000Hz, 单声道, 16bit(采样位深)
          audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    # 获取原始 PCM 数据
          audio_bytes = audio.raw_data
          print(f"  [DEBUG] 转码完成，处理后长度: {len(audio_bytes)}")
        except Exception as e:
          print(f"  [!] 转码失败: {e}，请检查是否安装 ffmpeg")

        # -- 构建签名 URL --
        ws_url = _build_xunfei_ws_url()

        import websocket
        accent = XUNFEI_ACCENT_MAP.get(dialect, 'mandarin')

        result_text_parts = []
        ws_error = [None]
        ws_done = threading.Event()

        def on_message(ws, message):
            try:
                msg = json.loads(message)
                header = msg.get('header', {})
                code = header.get('code', -1)
                if code != 0:
                    ws_error[0] = header.get('message', f'识别错误码: {code}')
                    ws_done.set()
                    return
                
                payload = msg.get('payload', {})
                result_obj = payload.get('result', {})
                text_b64 = result_obj.get('text', '')
                
                if text_b64:
                    try:
                        text_str = base64.b64decode(text_b64).decode('utf-8')
                        result_dict = json.loads(text_str)
                        for ws_item in result_dict.get('ws', []):
                            for cw_item in ws_item.get('cw', []):
                                w = cw_item.get('w', '')
                                if w:
                                    result_text_parts.append(w)
                    except Exception as dec_e:
                        print(f"  解析文本结果失败: {dec_e}")
                        
                # status=2 表示最后一帧
                if header.get('status') == 2:
                    ws_done.set()
            except Exception as e:
                print(f'  讯飞消息解析失败: {e}')
                ws_done.set()

        def on_error(ws, error):
            ws_error[0] = str(error)
            ws_done.set()

        def on_close(ws, *args):
            ws_done.set()

        def on_open(ws):
            """连接建立后分帧发送音频"""
            def _send():
                FRAME_SIZE = 8000  # 每帧字节数
                status = 0  # 0=第一帧, 1=中间帧, 2=最后一帧
                i = 0
                seq = 0
                while i < len(audio_bytes):
                    chunk = audio_bytes[i:i + FRAME_SIZE]
                    is_last = (i + FRAME_SIZE >= len(audio_bytes))
                    if is_last:
                        status = 2

                    audio_b64 = base64.b64encode(chunk).decode('utf-8')
                    if status == 0:
                        frame = {
                            "header": { "app_id": XUNFEI_APP_ID, "status": 0 },
                            "parameter": {
                                "iat": {
                                    "language": "zh_cn",
                                    "accent": "mulacc",
                                    "domain": "slm",
                                    "result": { "encoding": "utf8", "compress": "raw", "format": "json" }
                                }
                            },
                            "payload": {
                                "audio": {
                                    "encoding": "raw",
                                    "sample_rate": 16000,
                                    "channels": 1,
                                    "bit_depth": 16,
                                    "status": 0,
                                    "seq": seq,
                                    "audio": audio_b64
                                }
                            }
                        }
                        status = 1  # 后续帧状态变为 1
                    else:
                        frame = {
                            "header": { "app_id": XUNFEI_APP_ID, "status": status },
                            "payload": {
                                "audio": {
                                    "encoding": "raw",
                                    "sample_rate": 16000,
                                    "channels": 1,
                                    "bit_depth": 16,
                                    "status": status,
                                    "seq": seq,
                                    "audio": audio_b64
                                }
                            }
                        }

                    try:
                        ws.send(json.dumps(frame))
                    except Exception:
                        break
                    i += FRAME_SIZE
                    seq += 1
                    time.sleep(0.04)  # 模拟实时语速
            threading.Thread(target=_send, daemon=True).start()

        websocket.enableTrace(False)
        ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        # 在子线程运行 WebSocket，主线程等待结果
        t = threading.Thread(target=ws_app.run_forever, kwargs={'ping_timeout': 10}, daemon=True)
        t.start()
        ws_done.wait(timeout=30)

        if ws_error[0]:
            print(f'  [X] 讯飞识别错误: {ws_error[0]}')
            return recognize_mock(dialect)

        final_text = ''.join(result_text_parts).strip()
        if not final_text:
            return recognize_mock(dialect)

        print(f'  [OK] 语音识别成功: {final_text[:50]}...')
        return jsonify({'success': True, 'text': final_text, 'dialect': dialect})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return recognize_mock(dialect)


def recognize_mock(dialect):
    """讯飞未配置或调用失败时的兜底"""
    print(f'  [~] 语音识别未成功，方言: {dialect}')
    return jsonify({
        'success': False,
        'text': '',
        'dialect': dialect,
        'error': '语音识别服务未就绪（请检查讯飞 API 配置或重启 image_service.py）'
    })

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(" 图片处理服务启动")
    print("=" * 60)
    print(f" 地址：http://localhost:5003")
    print(f" rembg: {'[OK] 已安装' if REMBG_AVAILABLE else '[!] 未安装（合成正常，抠图跳过）'}")
    print(f" 模板目录: {TEMPLATES_DIR.resolve()}")
    print(f" <- 把你的背景图片放进这个目录，自动出现在模板列表")
    print(f" Doubao-Seedream 4.0: {'[OK] ARK_API_KEY 已配置' if ARK_API_KEY else '[!] 未配置'}")
    print(f" GLM-4V 智能构图: {'[OK] GLM_API_KEY 已配置' if GLM_API_KEY else '[!] 未配置（使用亮度分析兜底）'}")
    print(f" 讯飞语音识别: {'[OK] 已配置' if XUNFEI_APP_ID else '[!] 未配置'}")
    print()
    print("接?：")
    print(" POST /api/image/full-pipeline 提交任务（支持自适应构图）")
    print(" GET /api/task/{id} 查询进度")
    print(" GET /api/templates 获取模板列表")
    print(" POST /api/templates/upload 上传本地模板")
    print(" DELETE /api/templates/{id} 删除?定义模板")
    print(" GET /api/filters 滤镜列表")
    print(" POST /api/image/remove-bg 单独抠图")
    print(" POST /api/ai/generate-poster ★AI生成海报（Doubao-Seedream 4.0）")
    print(" POST /api/voice/recognize ★语音识别（讯飞）")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5003, host='0.0.0.0')
