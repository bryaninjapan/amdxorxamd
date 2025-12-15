@echo off
chcp 65001 >nul
color 0A
cls
echo.
echo     ╔═══════════════════════════════════════════════════════════╗
echo     ║                                                           ║
echo     ║            AMDX 项目 - 一键安装向导                       ║
echo     ║                                                           ║
echo     ╚═══════════════════════════════════════════════════════════╝
echo.
echo.
echo     正在检查系统环境...
echo.

:: 检查 Python
python --version >nul 2>&1
set PYTHON_OK=%errorlevel%

:: 检查 Git
git --version >nul 2>&1
set GIT_OK=%errorlevel%

echo     ┌───────────────────────────────────────────────────────────┐
echo     │  当前状态                                                 │
echo     └───────────────────────────────────────────────────────────┘
echo.

if %PYTHON_OK% equ 0 (
    echo       [✓] Python 已安装
    python --version
) else (
    echo       [✗] Python 未安装
)
echo.

if %GIT_OK% equ 0 (
    echo       [✓] Git 已安装
    git --version
) else (
    echo       [✗] Git 未安装
)
echo.
echo     ═══════════════════════════════════════════════════════════
echo.

:: 如果都已安装
if %PYTHON_OK% equ 0 (
    if %GIT_OK% equ 0 (
        echo       🎉 所有软件已安装完成！
        echo.
        echo       下一步：运行完整验证
        echo       命令: python verify_installation.py
        echo.
        echo       验证通过后，在 Cursor 中告诉 AI:
        echo       "软件安装完成"
        echo.
        pause
        exit /b 0
    )
)

:: 需要安装
echo     ═══════════════════════════════════════════════════════════
echo       需要安装的软件：
echo     ═══════════════════════════════════════════════════════════
echo.

if %PYTHON_OK% neq 0 (
    echo       1. Python 3.11+
    echo          - 下载页面即将打开
    echo          - 务必勾选 "Add Python to PATH"
    echo.
)

if %GIT_OK% neq 0 (
    echo       2. Git
    echo          - 下载页面即将打开
    echo          - 使用默认选项安装
    echo.
)

echo     ═══════════════════════════════════════════════════════════
echo.
echo       按任意键打开下载页面...
pause >nul

:: 打开下载页面
if %PYTHON_OK% neq 0 (
    echo.
    echo       正在打开 Python 下载页面...
    start https://www.python.org/downloads/
    timeout /t 2 /nobreak >nul
)

if %GIT_OK% neq 0 (
    echo       正在打开 Git 下载页面...
    start https://git-scm.com/downloads
    timeout /t 2 /nobreak >nul
)

echo.
echo     ═══════════════════════════════════════════════════════════
echo       重要提示：
echo     ═══════════════════════════════════════════════════════════
echo.
echo       ✓ Python 安装时务必勾选 "Add Python to PATH"
echo       ✓ 安装完成后，关闭此窗口
echo       ✓ 重新打开 PowerShell
echo       ✓ 再次运行此脚本检查安装结果
echo.
echo     ═══════════════════════════════════════════════════════════
echo.
pause

