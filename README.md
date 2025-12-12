# AMDX/XAMD 模式分析系统

📊 分析比特币(BTC)和以太坊(ETH)每月第一周的价格模式

## 概述

本系统用于判断每个月第一周是属于 **AMDX** 还是 **XAMD** 模式，基于与前一周的价格区间比较。

### 模式定义

| 模式 | 定义 |
|------|------|
| **AMDX** | 第一周的最高价和最低价都在前一周的价格区间内（不突破） |
| **XAMD** | 第一周的最高价或最低价超出前一周的价格区间（突破） |

### 时间定义

- **周开始时间**: 周一早上8点 (UTC+9)
- **周结束时间**: 下周一早上7:59 (UTC+9)
- **第一周定义**: 每月第一个完整周（如果1号不是周一，则从该月第一个周一开始）

## 功能特点

- ✅ 自动从 Binance API 获取历史K线数据
- ✅ 支持 BTC/USDT 和 ETH/USDT 永续合约
- ✅ 每周自动更新（通过 GitHub Actions）
- ✅ 生成 Excel 和 PDF 格式报告
- ✅ 数据质量检查
- ✅ 突破方向和幅度记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 一键运行

```bash
# 运行所有步骤（初始化 -> 获取数据 -> 计算模式 -> 生成报告）
python run_all.py

# 强制重新获取所有历史数据
python run_all.py --force

# 只生成报告
python run_all.py --report
```

### 3. 分步运行

```bash
# 步骤1: 初始化数据库
python scripts/init_database.py

# 步骤2: 获取Binance数据
python scripts/fetch_data.py

# 步骤3: 计算模式
python scripts/calculate_patterns.py

# 步骤4: 生成报告
python scripts/generate_reports.py
```

## 项目结构

```
AMDX/
├── config.py                 # 配置文件
├── run_all.py               # 一键运行脚本
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
│
├── database/
│   ├── schema.sql          # 数据库结构
│   └── patterns.db         # SQLite数据库
│
├── scripts/
│   ├── init_database.py    # 数据库初始化
│   ├── fetch_data.py       # 数据获取
│   ├── calculate_patterns.py # 模式计算
│   └── generate_reports.py # 报告生成
│
├── reports/
│   ├── excel/              # Excel报告
│   ├── pdf/                # PDF报告
│   └── data/               # JSON数据
│
├── data/
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后数据
│
└── .github/
    └── workflows/
        ├── weekly_update.yml   # 每周自动更新
        └── manual_update.yml   # 手动触发更新
```

## 输出报告

### Excel报告 (`reports/excel/`)

包含以下工作表：
- **总体汇总**: 所有交易对的整体统计
- **年度汇总**: 按年份统计AMDX/XAMD分布
- **月度详细**: 每月详细数据
- **月份分布**: 按月份（1-12月）统计模式分布
- **各交易对详细**: 分交易对的详细数据

### PDF报告 (`reports/pdf/`)

包含总体汇总和年度汇总的可打印版本。

### JSON数据 (`reports/data/`)

适用于程序化处理和Web展示的JSON格式数据。

## GitHub Actions 自动更新

### 每周自动更新

工作流在每周一早上9点(UTC+9)自动运行，更新最新一周的数据。

### 手动触发

1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Manual Data Update" 工作流
3. 点击 "Run workflow"
4. 选择要执行的操作

## 数据说明

### 数据来源

- Binance 期货API (fapi.binance.com)
- 使用1小时K线数据计算周最高/最低价

### 数据范围

- 开始时间: 根据Binance API可用数据（约2019年9月起）
- 结束时间: 最新完整周

### 边界情况处理

- 等于前一周最高/最低价**不算**突破
- 第一周的最高价超过前一周最高价 = 向上突破
- 第一周的最低价低于前一周最低价 = 向下突破

## 配置说明

在 `config.py` 中可以修改：

```python
# 交易对配置
SYMBOLS = [
    {'name': 'BTCUSDT', 'display_name': 'BTC/USDT 永续合约', ...},
    {'name': 'ETHUSDT', 'display_name': 'ETH/USDT 永续合约', ...},
]

# 时区设置
TZ_UTC9 = pytz.timezone('Asia/Tokyo')  # UTC+9

# 周开始/结束时间
WEEK_START_HOUR = 8   # 周一早上8点
WEEK_START_MINUTE = 0
```

## 常见问题

### Q: 如何添加新的交易对？

在 `config.py` 的 `SYMBOLS` 列表中添加新的配置：

```python
SYMBOLS = [
    # ... 现有交易对 ...
    {
        'name': 'SOLUSDT',
        'display_name': 'SOL/USDT 永续合约',
        'api_symbol': 'SOLUSDT',
        'use_futures': True
    }
]
```

然后重新运行 `python run_all.py --force`

### Q: 数据更新失败怎么办？

1. 检查网络连接
2. 确认Binance API是否可访问
3. 查看错误日志
4. 尝试手动运行各个步骤排查问题

### Q: 如何修改自动更新时间？

编辑 `.github/workflows/weekly_update.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * 0'  # UTC时间，对应UTC+9的周一早上9点
```

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

