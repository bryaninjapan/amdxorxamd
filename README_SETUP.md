# 🚀 快速安装指南

## 问题诊断

您遇到的错误：
```
Python was not found
```

**原因**：Python 还没有安装到您的电脑上。

---

## ✅ 解决方案（3 步完成）

### 📌 方案 A：使用自动化脚本（最简单）

#### 第 1 步：安装 Python
1. **双击运行**：`install_python_guide.bat`
2. 会自动打开 Python 下载页面
3. 下载并运行安装程序
4. **关键**：勾选 ✅ **Add Python to PATH**
5. 完成安装

#### 第 2 步：安装 Git
1. **双击运行**：`install_git_guide.bat`
2. 会自动打开 Git 下载页面
3. 下载并运行安装程序
4. 选择默认选项即可
5. 完成安装

#### 第 3 步：验证安装
1. **关闭所有 PowerShell 窗口**（重要！）
2. **重新打开 PowerShell**
3. **双击运行**：`quick_install_check.bat`
4. 看到 ✓✓ 表示成功

---

### 📌 方案 B：手动下载安装

#### 安装 Python 3.11

**1. 下载**
- 访问：https://www.python.org/downloads/
- 点击 "Download Python 3.11.x"

**2. 安装（关键步骤）**

打开安装程序后：

```
┌─────────────────────────────────────┐
│  Python 3.11.x Setup                │
├─────────────────────────────────────┤
│                                     │
│  ☑ Install launcher for all users  │
│  ☑ Add Python to PATH  ← 必须勾选！ │
│                                     │
│  [ Customize installation ]  ← 点这个│
│  [ Install Now ]                    │
└─────────────────────────────────────┘
```

**必须勾选的选项**：
- ✅ Add Python to PATH（最重要！）
- ✅ pip
- ✅ tcl/tk and IDLE
- ✅ Install for all users
- ✅ Add Python to environment variables

**3. 验证**
安装完成后，**重新打开 PowerShell**，运行：
```powershell
python --version
```
应该显示：`Python 3.11.x`

---

#### 安装 Git

**1. 下载**
- 访问：https://git-scm.com/downloads
- 下载 Windows 64-bit 版本

**2. 安装**
- 选择 "Git from the command line and also from 3rd-party software"
- 其他保持默认

**3. 验证**
安装完成后，**重新打开 PowerShell**，运行：
```powershell
git --version
```
应该显示：`git version 2.xx.x`

---

## 🔧 常见问题

### Q1: 安装后还是显示 "Python was not found"？
**原因**：没有重新打开 PowerShell

**解决**：
1. 关闭所有 PowerShell 窗口
2. 重新打开 PowerShell
3. 再次运行 `python --version`

### Q2: 安装时忘记勾选 "Add Python to PATH"？
**解决**：重新安装 Python，这次记得勾选

### Q3: 如何确认已经成功？
运行完整验证脚本：
```powershell
python verify_installation.py
```
看到 ✅ 所有检查通过即可

---

## 📊 安装完成后

当看到：
```
✅ Python 已安装: Python 3.11.x
✅ Git 已安装: git version 2.xx.x
```

**在 Cursor 中告诉 AI**：
> "软件安装完成"

AI 将自动继续执行剩余 12 个步骤！

---

## 🎯 完整流程图

```
开始
  ↓
安装 Python（勾选 Add to PATH）
  ↓
安装 Git
  ↓
关闭并重新打开 PowerShell ← 关键步骤！
  ↓
运行: python --version
  ↓
运行: git --version
  ↓
运行: python verify_installation.py
  ↓
看到 ✅ 全部通过
  ↓
告诉 AI "软件安装完成"
  ↓
AI 自动完成后续 12 步
  ↓
完成！
```

---

## 📝 需要帮助？

- 查看详细说明：`INSTALLATION_GUIDE.md`
- 快速检查工具：`quick_install_check.bat`
- Python 安装向导：`install_python_guide.bat`
- Git 安装向导：`install_git_guide.bat`
- 完整验证脚本：`python verify_installation.py`


