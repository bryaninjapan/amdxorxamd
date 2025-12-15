@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              快速安装检查                                 ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

echo [检查 1/2] 检查 Git...
git --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Git 已安装
    git --version
) else (
    echo ✗ Git 未安装
    echo   请运行: install_git_guide.bat
)
echo.

echo [检查 2/2] 检查 Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python 已安装
    python --version
    pip --version
) else (
    echo ✗ Python 未安装
    echo   请运行: install_python_guide.bat
)
echo.

echo ═══════════════════════════════════════════════════════════
python --version >nul 2>&1
if %errorlevel% equ 0 (
    git --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓✓ 所有软件已安装！
        echo.
        echo 下一步：运行验证脚本
        echo   python verify_installation.py
    )
) else (
    echo 请先完成软件安装
)
echo ═══════════════════════════════════════════════════════════
echo.
pause


