@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              Python 安装向导                              ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo [步骤 1] 打开 Python 官网下载页面...
echo.
start https://www.python.org/downloads/
timeout /t 2 /nobreak >nul
echo.
echo ═══════════════════════════════════════════════════════════
echo   重要提示：
echo ═══════════════════════════════════════════════════════════
echo.
echo   1. 下载 Python 3.11.x（推荐 3.11.9）
echo.
echo   2. 运行安装程序时，务必勾选：
echo      ✓ [Add Python to PATH]  ← 最重要！
echo.
echo   3. 选择 "Customize installation"
echo.
echo   4. 确保勾选：
echo      ✓ pip
echo      ✓ tcl/tk and IDLE
echo      ✓ Python test suite
echo      ✓ py launcher
echo.
echo   5. 在 "Advanced Options" 中勾选：
echo      ✓ Install for all users
echo      ✓ Add Python to environment variables
echo.
echo   6. 安装完成后：
echo      - 关闭此窗口
echo      - 重新打开 PowerShell
echo      - 运行: python --version
echo.
echo ═══════════════════════════════════════════════════════════
echo.
pause


