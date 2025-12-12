# AMDX/XAMD 模式分析系统

📊 分析比特币(BTC)和以太坊(ETH)每月第一周的价格模式

## 概述

本系统用于判断每个月第一周是属于 **AMDX** 还是 **XAMD** 模式，基于与前一周的价格区间比较。

### 模式定义

#### 月度模式（AMDX/XAMD）

| 模式 | 定义 |
|------|------|
| **AMDX** | 第一周的最高价和最低价都在前一周的价格区间内（不突破） |
| **XAMD** | 第一周的最高价或最低价超出前一周的价格区间（突破） |

#### 周度模式（XAMDXAM/AMDXAMD）

基于每周7天的价格走势模式：

| 模式 | 定义 |
|------|------|
| **XAMDXAM** | 周一突破上周日价格区间，后续6天按固定序列：A-M-D-X-A-M |
| **AMDXAMD** | 周一未突破上周日价格区间，后续6天按固定序列：M-D-X-A-M-D |

**走势字母含义：**
- **X**: 突破（向上或向下）
- **A**: 在区间内
- **M**: 向上突破
- **D**: 向下突破

### 时间定义

- **周开始时间**: 周一早上8点 (UTC+9)
- **周结束时间**: 下周一早上7:59 (UTC+9)
- **第一周定义**: 每月第一个完整周（如果1号不是周一，则从该月第一个周一开始）

## 功能特点

- ✅ 自动从 Binance API 获取历史K线数据
- ✅ 支持 BTC/USDT 和 ETH/USDT 永续合约
- ✅ **月度模式分析**：AMDX/XAMD 模式（每月第一周）
- ✅ **周度模式分析**：XAMDXAM/AMDXAMD 模式（每周7天）
- ✅ **日数据分析**：每日价格数据与走势明细
- ✅ 每日自动更新数据
- ✅ 生成 Excel 和 PDF 格式报告
- ✅ **合并报告**：月度模式 + 周度模式一体化分析
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

# 步骤4: 获取日数据
python scripts/fetch_daily_data.py

# 步骤5: 计算周度模式
python scripts/calculate_weekly_patterns.py

# 步骤6: 生成报告
python scripts/generate_reports.py

# 步骤7: 生成合并报告（月度模式 + 周度模式）
python scripts/export_combined_report.py
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
│   ├── init_database.py              # 数据库初始化
│   ├── fetch_data.py                 # 周数据获取
│   ├── fetch_daily_data.py           # 日数据获取
│   ├── calculate_patterns.py         # 月度模式计算
│   ├── calculate_weekly_patterns.py # 周度模式计算
│   ├── generate_reports.py           # 月度模式报告生成
│   ├── export_all_data_to_excel.py   # 完整数据导出
│   ├── export_weekly_patterns_to_excel.py # 周度模式报告生成
│   └── export_combined_report.py    # 合并报告生成
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

### 合并分析报告 (`reports/excel/完整分析报告_最新.xlsx`)

**月度模式分析部分：**
- **月度模式_总体汇总**: 所有交易对的整体统计
- **月度模式_年度汇总**: 按年份统计AMDX/XAMD分布
- **BTC月份分布统计**: BTC按月份（1-12月）统计模式分布
- **ETH月份分布统计**: ETH按月份（1-12月）统计模式分布
- **BTCUSDT_周数据**: BTC周数据（含X/A/M/D走势列）
- **ETHUSDT_周数据**: ETH周数据（含X/A/M/D走势列）

**周度模式分析部分：**
- **周度模式_总体汇总**: 所有交易对的整体统计
- **周度模式_年度汇总**: 按年份统计XAMDXAM/AMDXAMD分布
- **BTC周度详细**: BTC每周7天的详细走势明细和突破幅度
- **ETH周度详细**: ETH每周7天的详细走势明细和突破幅度
- **BTC日数据**: BTC每日数据（含周度模式、走势明细、突破幅度）
- **ETH日数据**: ETH每日数据（含周度模式、走势明细、突破幅度）

### 其他报告

- **月度模式报告** (`reports/excel/AMDX_XAMD_分析报告_最新.xlsx`): 仅月度模式分析
- **周度模式报告** (`reports/excel/周度模式分析_最新.xlsx`): 仅周度模式分析
- **完整数据导出** (`reports/excel/完整数据导出_最新.xlsx`): 原始数据导出

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

- **周数据**: 从Binance API可用数据开始（约2019年9月起）
- **日数据**: 从2019年9月起（历史回填）
- **更新频率**: 每日更新（日数据），每周更新（周数据）
- **结束时间**: 最新完整周/日

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

### Q: 周度模式和月度模式有什么区别？

- **月度模式（AMDX/XAMD）**: 分析每月第一周相对于前一周的价格走势，用于月度趋势判断
- **周度模式（XAMDXAM/AMDXAMD）**: 分析每周7天的价格走势模式，用于周内趋势判断
- **日数据**: 记录每日的价格数据和相对于前一天的走势明细

### Q: 如何查看最新的合并报告？

运行以下命令生成最新的合并报告：

```bash
python scripts/export_combined_report.py
```

报告将保存在 `reports/excel/完整分析报告_最新.xlsx`

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

