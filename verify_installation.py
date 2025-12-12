#!/usr/bin/env python3
"""
安装验证脚本
验证 Git 和 Python 是否正确安装
"""

import subprocess
import sys
import platform

def check_command(command, args=['--version']):
    """检查命令是否可用"""
    try:
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout.strip()
    except FileNotFoundError:
        return False, f"{command} 未找到"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("软件安装验证")
    print("=" * 60)
    print()
    
    # 系统信息
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print()
    
    all_ok = True
    
    # 检查 Python
    print("1. 检查 Python...")
    python_ok, python_info = check_command('python')
    if python_ok:
        print(f"   ✅ Python 已安装: {python_info}")
        print(f"   版本详情: Python {sys.version}")
    else:
        print(f"   ❌ Python 未安装或不在 PATH 中")
        all_ok = False
    print()
    
    # 检查 pip
    print("2. 检查 pip...")
    pip_ok, pip_info = check_command('pip')
    if pip_ok:
        print(f"   ✅ pip 已安装: {pip_info}")
    else:
        print(f"   ❌ pip 未安装或不在 PATH 中")
        all_ok = False
    print()
    
    # 检查 Git
    print("3. 检查 Git...")
    git_ok, git_info = check_command('git')
    if git_ok:
        print(f"   ✅ Git 已安装: {git_info}")
    else:
        print(f"   ❌ Git 未安装或不在 PATH 中")
        all_ok = False
    print()
    
    # 检查必要的 Python 模块
    print("4. 检查关键 Python 模块...")
    required_modules = {
        'sqlite3': '数据库支持',
        'json': 'JSON 处理',
        'datetime': '日期时间处理',
        'urllib': 'HTTP 请求',
    }
    
    for module, description in required_modules.items():
        try:
            __import__(module)
            print(f"   ✅ {module}: {description}")
        except ImportError:
            print(f"   ❌ {module}: {description} - 未安装")
            all_ok = False
    print()
    
    # 总结
    print("=" * 60)
    if all_ok:
        print("✅ 所有检查通过！环境配置正确。")
        print()
        print("下一步：在 Cursor 中告诉 AI '软件安装完成'")
    else:
        print("❌ 部分检查失败，请按照 INSTALLATION_GUIDE.md 重新安装")
        print()
        print("提示：")
        print("  1. 如果刚安装完，请关闭并重新打开 PowerShell")
        print("  2. 确保安装时勾选了 'Add to PATH' 选项")
        print("  3. 如需帮助，请查看 INSTALLATION_GUIDE.md")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())

