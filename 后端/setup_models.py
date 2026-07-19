# setup_models.py  ── 项目初次部署时跑一次，提前下好模型

# 使用方法：python setup_models.py

# 之后启动 image_service.py 就不会再等待下载

import urllib.request
import os
from pathlib import Path

# u2net   → 176MB，效果最好
# u2netp  → 4.7MB，效果够用，推荐生产环境
# isnet-general-use → 170MB，新版效果更好但更大

MODEL_URL  = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
MODEL_NAME = "u2netp.onnx"
SAVE_DIR   = Path.home() / ".u2net"
SAVE_PATH  = SAVE_DIR / MODEL_NAME

def download_with_progress(url, save_path):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"下载模型到：{save_path}")
    print(f"来源：{url}")
    
    def progress(count, block_size, total_size):
        mb_done  = count * block_size / 1024 / 1024
        mb_total = total_size / 1024 / 1024
        pct      = min(100, count * block_size * 100 / total_size)
        bar      = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\r  [{bar}] {pct:.0f}%  {mb_done:.1f}/{mb_total:.1f} MB", end="", flush=True)
    
    urllib.request.urlretrieve(url, save_path, reporthook=progress)
    print(f"\n✅ 下载完成：{save_path}")

if __name__ == "__main__":
    if SAVE_PATH.exists():
        size_mb = SAVE_PATH.stat().st_size / 1024 / 1024
        print(f"✅ 模型已存在（{size_mb:.1f} MB）：{SAVE_PATH}")
        print("   无需重新下载，可直接启动 image_service.py")
    else:
        print("=" * 55)
        print("  云稼集AgriWit · 抠图模型预下载工具")
        print("=" * 55)
        print(f"  模型：u2netp（轻量版，仅 ~4.7MB）")
        print(f"  保存位置：{SAVE_PATH}")
        print("=" * 55)
        try:
            download_with_progress(MODEL_URL, SAVE_PATH)
        except Exception as e:
            print(f"\n❌ 下载失败：{e}")
            print("\n手动下载方法：")
            print(f"  1. 浏览器打开：{MODEL_URL}")
            print(f"  2. 保存到：{SAVE_PATH}")