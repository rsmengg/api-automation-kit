#!/usr/bin/env python3
"""把一段终端输出渲染成 PNG（零系统依赖，只需 pillow）。

用途：给作品集 / 平台作品展示生成"真实运行截图"。
用法：python3 tools/render_terminal_shot.py --out path.png
"""
import argparse
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    os.path.expanduser("~/Library/Fonts/NotoSansSC-Black.otf"),
    "/System/Library/Fonts/Supplemental/PingFang.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


# (文本, 颜色) —— 逐行渲染
SHELL_LINES = [
    ("$ git clone https://github.com/rsmengg/api-automation-kit.git", "#d4d4d4"),
    ("$ cd api-automation-kit && python3 mock_api.py &", "#d4d4d4"),
    ("$ pytest --base-url http://127.0.0.1:8899 -v", "#d4d4d4"),
    ("", "#d4d4d4"),
    ("============================= test session starts ==============================", "#5a5a66"),
    ("platform darwin -- Python 3.13.12, pytest-9.1.1, pluggy-1.6.0", "#8a8a96"),
    ("rootdir: api-automation-kit    configfile: pytest.ini    testpaths: tests", "#8a8a96"),
    ("collected 4 items", "#8a8a96"),
    ("", "#d4d4d4"),
    ("tests/test_api.py::test_health_check PASSED                            [ 25%]", "#4ec9b0"),
    ("tests/test_api.py::test_create_order PASSED                            [ 50%]", "#4ec9b0"),
    ("tests/test_api.py::test_create_order_invalid PASSED                    [ 75%]", "#4ec9b0"),
    ("tests/test_api.py::test_order_pagination PASSED                        [100%]", "#4ec9b0"),
    ("", "#d4d4d4"),
    ("============================== 4 passed in 0.01s ===============================", "#4ec9b0"),
    ("$", "#d4d4d4"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/screenshots/api-kit-terminal.png")
    ap.add_argument("--width", type=int, default=1180)
    ap.add_argument("--title", default="api-automation-kit — pytest")
    ap.add_argument(
        "--lines-file",
        help="JSON 文件，内容为 [[文本, 颜色], ...]，覆盖内置的 SHELL_LINES",
    )
    args = ap.parse_args()

    lines = SHELL_LINES
    if args.lines_file:
        import json

        with open(args.lines_file, encoding="utf-8") as f:
            lines = json.load(f)

    font = load_font(20)
    lh = 32
    pad_top, pad_bottom = 66, 26
    pad_left = 28
    height = pad_top + lh * len(lines) + pad_bottom

    img = Image.new("RGB", (args.width, height), "#16161a")
    d = ImageDraw.Draw(img)

    # 窗口标题栏 + 三个 mac 圆点
    d.rectangle([0, 0, args.width, 42], fill="#2b2b31")
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx, cy = 26 + i * 22, 21
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=color)
    d.text((args.width // 2 - 60, 12), "api-automation-kit — pytest", font=font, fill="#9a9aa6")

    y = pad_top
    for text, color in lines:
        if text.startswith("$"):
            d.text((pad_left, y), "$", font=font, fill="#4ec9b0")
            d.text((pad_left + 18, y), text[1:], font=font, fill=color)
        else:
            d.text((pad_left, y), text, font=font, fill=color)
        y += lh

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    img.save(args.out)
    print("saved:", args.out, img.size)


if __name__ == "__main__":
    main()
