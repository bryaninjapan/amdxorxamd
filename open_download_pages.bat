@echo off
echo ========================================
echo 打开软件下载页面
echo ========================================
echo.
echo 正在打开 Git 下载页面...
start https://git-scm.com/downloads
timeout /t 2 /nobreak >nul
echo.
echo 正在打开 Python 下载页面...
start https://www.python.org/downloads/
echo.
echo ========================================
echo 请按照 INSTALLATION_GUIDE.md 的说明安装
echo ========================================
pause

