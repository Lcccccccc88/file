# -*- coding: utf-8 -*-
"""
浏览器防挂机验证弹窗 · 自动点击脚本
====================================
原理：脚本周期性截取整个屏幕，用 OpenCV 图像匹配在屏幕任意位置寻找指定的"按钮参考图"，
      一旦找到（说明弹窗出现了）就自动移动鼠标到该按钮中心并点击。
      弹窗出现在屏幕哪里都能点到，不依赖固定坐标。

依赖（已安装）：pillow, numpy, opencv-python   （Python 3.13 +）

使用方法
--------
1. 准备按钮参考图：
   - 让那个验证弹窗显示出来，用 Win+Shift+S 截图，只框选【按钮本身】那一小块，
     例如"继续挂机 / 我知道了 / 确定"等按钮，保存为 button.png，放到本脚本同目录。
   - 参考图越接近按钮真实外观越好，不要包含大块背景。

2. 先自检（不点击，只确认环境与参考图是否能被找到）：
       python auto_click_popup.py --check

3. 试点一次（截屏、找按钮、点一次就退出，方便验证）：
       python auto_click_popup.py --test

4. 正式运行（循环自动点）：
       python auto_click_popup.py
   按 Ctrl+C 停止。

常见问题
--------
- 老是找不到按钮：降低下方 CONFIDENCE（如 0.8 -> 0.7），或重新截一张更清晰、更贴近弹窗
  实际外观的参考图。
- 误点到别的东西：调高 CONFIDENCE（如 0.85 -> 0.92），并确保参考图只包含按钮本身。
- 高分屏（150%/200% 缩放）坐标偏移：脚本已自动开启 DPI 感知，一般无需处理。
"""

import ctypes
import os
import sys
import time

import cv2
import numpy as np
from PIL import ImageGrab

# ====================== 配置区（按需修改） ======================
BUTTON_IMAGE = "button.png"      # 按钮参考图文件名（放在本脚本同目录）
CHECK_INTERVAL = 3               # 每隔 N 秒截屏检测一次
CONFIDENCE = 0.85                # 匹配阈值 0~1，越高越严格（越不容易误点，也可能漏点）
CLICK_COOLDOWN = 8               # 点过一次后冷却 N 秒，防止弹窗还没消失就连点
MAX_CLICKS = 0                   # 最多点击次数；0 表示不限次数，跑到你 Ctrl+C 为止
SCALE_RANGE = (0.5, 2.0)         # 按钮参考图的缩放搜索范围（应对高分屏/浏览器缩放导致尺寸不同）
SCALE_STEPS = 12                 # 在该范围内尝试多少档缩放，越大越精确但略慢
# ================================================================

# ---- Windows 鼠标左键消息 ----
_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004


def enable_dpi_aware():
    """开启 DPI 感知，避免高分屏下截图像素坐标与鼠标坐标不一致。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 每显示器感知
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()   # 旧系统回退
        except Exception:
            pass


def click(x, y):
    """把鼠标移动到 (x, y) 并做一次真实左键点击。"""
    ctypes.windll.user32.SetCursorPos(int(round(x)), int(round(y)))
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def find_button(screen_gray, template_gray, threshold):
    """在整屏灰度图中，用多档缩放查找按钮参考图，返回(中心x, 中心y, 匹配度, 缩放)；没找到返回 None。"""
    sh, sw = screen_gray.shape[:2]
    th, tw = template_gray.shape[:2]
    best = None  # (max_val, max_loc, scale)
    lo, hi = SCALE_RANGE
    for i in range(SCALE_STEPS + 1):
        scale = lo + (hi - lo) * (i / SCALE_STEPS)
        th_s, tw_s = int(round(th * scale)), int(round(tw * scale))
        if th_s < 8 or tw_s < 8 or th_s >= sh or tw_s >= sw:  # 缩放后太小或超过屏幕，跳过
            continue
        t = cv2.resize(template_gray, (tw_s, th_s), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(screen_gray, t, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if best is None or max_val > best[0]:
            best = (max_val, max_loc, scale)
    if best is None:
        return None
    max_val, max_loc, scale = best
    if max_val >= threshold:
        cx = int(round(max_loc[0] + tw * scale / 2))
        cy = int(round(max_loc[1] + th * scale / 2))
        return cx, cy, float(max_val), scale
    return None


def grab_screen_gray():
    """抓取整个虚拟屏幕（含多显示器），返回灰度 numpy 数组。"""
    img = ImageGrab.grab(all_screens=True)
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return gray


def load_template():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), BUTTON_IMAGE)
    if not os.path.exists(path):
        print(f"[错误] 找不到参考图：{path}")
        print("       请用 Win+Shift+S 截取按钮本身，保存为 button.png 放到本脚本同目录。")
        sys.exit(1)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"[错误] 无法读取参考图：{path}（不是有效图片？）")
        sys.exit(1)
    return img


def cmd_check():
    """自检：验证环境与参考图，截屏一次看能否找到按钮（不点击）。"""
    print("== 自检中 ==")
    print(f"屏幕分辨率(逻辑): {ctypes.windll.user32.GetSystemMetrics(0)} x "
          f"{ctypes.windll.user32.GetSystemMetrics(1)}")
    template = load_template()
    print(f"参考图加载成功：{template.shape[1]}x{template.shape[0]} 像素")
    screen = grab_screen_gray()
    print(f"截屏成功：{screen.shape[1]}x{screen.shape[0]} 像素")
    pos = find_button(screen, template, CONFIDENCE)
    if pos:
        print(f"[结果] 检测到按钮，中心在 ({pos[0]}, {pos[1]})，匹配度 {pos[2]:.2f} —— 配置可用。")
    else:
        print(f"[结果] 本次截屏未检测到按钮（当前弹窗可能没出现，或参考图/阈值不匹配）。")
        print("       → 可先让弹窗出现再 --check；仍找不到就降低 CONFIDENCE 或重截参考图。")
    print("== 自检结束 ==")


def cmd_test():
    """截屏找按钮，找到就点一次然后退出。"""
    print("== 测试点击一次 ==")
    template = load_template()
    screen = grab_screen_gray()
    pos = find_button(screen, template, CONFIDENCE)
    if not pos:
        print("本次截屏未检测到按钮，未点击。请让弹窗出现后再试，或调整阈值/参考图。")
        return
    print(f"检测到按钮 ({pos[0]}, {pos[1]})，匹配度 {pos[2]:.2f}，点击一次。")
    click(pos[0], pos[1])
    print("已点击。")


def run_loop():
    """正式运行：循环截屏检测并点击。"""
    print("== 开始自动点击（Ctrl+C 停止）==")
    print(f"检测间隔: {CHECK_INTERVAL}s | 阈值: {CONFIDENCE} | 点击冷却: {CLICK_COOLDOWN}s | "
          f"点击上限: {'不限' if MAX_CLICKS == 0 else MAX_CLICKS} 次")
    template = load_template()

    clicks = 0
    last_click_time = 0.0
    while True:
        try:
            now = time.time()
            screen = grab_screen_gray()
            pos = find_button(screen, template, CONFIDENCE)
            if pos and (now - last_click_time >= CLICK_COOLDOWN):
                print(f"[{time.strftime('%H:%M:%S')}] 检测到按钮 ({pos[0]},{pos[1]})，"
                      f"匹配度 {pos[2]:.2f}，点击。")
                click(pos[0], pos[1])
                clicks += 1
                last_click_time = time.time()
                if MAX_CLICKS and clicks >= MAX_CLICKS:
                    print(f"已达到点击上限 {MAX_CLICKS} 次，退出。")
                    break
            else:
                # 没检测到，或还在冷却期内 → 安静等待，不刷屏
                pass
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n已停止。共点击", clicks, "次。")
            break
        except Exception as e:   # 单次异常不中断，记下继续
            print(f"[{time.strftime('%H:%M:%S')}] 出错: {e}（忽略，继续）")


def main():
    enable_dpi_aware()
    args = sys.argv[1:]
    if "--check" in args:
        cmd_check()
    elif "--test" in args:
        cmd_test()
    else:
        run_loop()


if __name__ == "__main__":
    main()
