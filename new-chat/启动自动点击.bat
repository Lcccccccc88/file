@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动自动点击脚本（按 Ctrl+C 或关闭本窗口停止）...
"C:\Users\A\AppData\Local\Programs\Python\Python313\python.exe" "%~dp0auto_click_popup.py"
echo.
echo 脚本已结束。
pause
