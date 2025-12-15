@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              Git 安装向导                                 ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo [步骤 1] 打开 Git 官网下载页面...
echo.
start https://git-scm.com/downloads
timeout /t 2 /nobreak >nul
echo.
echo ═══════════════════════════════════════════════════════════
echo   重要提示：
echo ═══════════════════════════════════════════════════════════
echo.
echo   1. 下载 Windows 64-bit 版本
echo.
echo   2. 运行安装程序，在选项页面选择：
echo      ✓ Git from the command line and also from 3rd-party software
echo.
echo   3. 其他选项保持默认
echo.
echo   4. 安装完成后：
echo      - 关闭此窗口
echo      - 重新打开 PowerShell
echo      - 运行: git --version
echo.
echo ═══════════════════════════════════════════════════════════
echo.
pause


