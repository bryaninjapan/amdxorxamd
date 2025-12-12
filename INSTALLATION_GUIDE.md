# 软件安装指南

## 步骤 1：安装 Git

### 下载和安装
1. 打开浏览器，访问：https://git-scm.com/downloads
2. 点击 "Windows" 下载最新版本
3. 运行下载的安装程序（git-xxx-64-bit.exe）
4. **重要设置**：
   - 选择 "Git from the command line and also from 3rd-party software"
   - 其他选项保持默认即可
5. 完成安装

### 验证安装
安装完成后，**重新打开 PowerShell**（关闭当前窗口，重新打开），然后运行：
```powershell
git --version
```
应该显示类似：`git version 2.43.0.windows.1`

---

## 步骤 2：安装 Python 3.11

### 下载和安装
1. 访问：https://www.python.org/downloads/
2. 点击 "Download Python 3.11.x"（推荐 3.11.9）
3. 运行下载的安装程序
4. **非常重要**：
   - ✅ 勾选 "Add Python to PATH"（最下方的复选框）
   - ✅ 选择 "Customize installation"
   - ✅ 确保勾选：
     - pip
     - tcl/tk and IDLE
     - Python test suite
     - py launcher
   - ✅ 在 "Advanced Options" 中勾选：
     - Install for all users
     - Add Python to environment variables
5. 点击 "Install"

### 验证安装
安装完成后，**重新打开 PowerShell**，然后运行：
```powershell
python --version
pip --version
```
应该显示：
- `Python 3.11.x`
- `pip xx.x.x from ...`

---

## 步骤 3：验证环境

安装完成后，运行验证脚本：
```powershell
python verify_installation.py
```

---

## 常见问题

### Q: 运行 python 命令提示找不到
A: 
1. 确保安装时勾选了 "Add Python to PATH"
2. 重新打开 PowerShell（必须重启）
3. 如果还不行，手动添加到 PATH：
   - 默认路径：`C:\Users\你的用户名\AppData\Local\Programs\Python\Python311`

### Q: Git 命令不识别
A:
1. 重新打开 PowerShell
2. 如果还不行，重新安装 Git 并确保选择了正确的选项

---

## 完成后执行

所有软件安装并验证成功后，在 Cursor 中告诉我："软件安装完成"，我将继续执行下一步。

