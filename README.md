# AMDX/XAMD 模式分析系统（增强版）

📊 分析比特币(BTC)和以太坊(ETH)的价格模式，支持多交易所数据

## 概述

本系统用于判断每个月第一周是属于 **AMDX** 还是 **XAMD** 模式，基于与前一周的价格区间比较。同时支持周度模式分析。

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

### 数据获取
- ✅ 自动从 Binance API 获取历史K线数据
- ✅ 支持 BTC/USDT 和 ETH/USDT 永续合约
- ✅ **NEW** 支持 Bitstamp 交易所
- ✅ **NEW** 支持 BTC/USD 现货数据
- ✅ **NEW** 历史数据回填（从2011年开始）

### 模式分析
- ✅ **月度模式分析**：AMDX/XAMD 模式（每月第一周）
- ✅ **周度模式分析**：XAMDXAM/AMDXAMD 模式（每周7天）
- ✅ **日数据分析**：每日价格数据与走势明细
- ✅ 数据质量检查
- ✅ 突破方向和幅度记录

### 报告生成
- ✅ 生成 Excel 和 PDF 格式报告
- ✅ **合并报告**：月度模式 + 周度模式一体化分析
- ✅ 每日自动更新数据

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
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

# 获取Bitstamp数据
python run_all.py --bitstamp
```

### 3. 分步运行

```bash
# 步骤1: 初始化数据库
python scripts/init_database.py

# 步骤2: 获取Binance数据
python scripts/fetch_data.py

# 步骤3: 获取Bitstamp数据（NEW）
python scripts/fetch_bitstamp_data.py

# 步骤4: 计算模式
python scripts/calculate_patterns.py

# 步骤5: 获取日数据
python scripts/fetch_daily_data.py

# 步骤6: 计算周度模式
python scripts/calculate_weekly_patterns.py

# 步骤7: 生成报告
python scripts/generate_reports.py

# 步骤8: 生成合并报告
python scripts/export_combined_report.py

```

## 项目结构

```
AMDX/
├── config.py                 # 配置文件（支持多交易所）
├── run_all.py               # 一键运行脚本（增强版）
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
│
├── database/
│   ├── schema.sql          # 数据库结构（支持小时数据）
│   └── patterns.db         # SQLite数据库
│
├── scripts/
│   ├── init_database.py              # 数据库初始化
│   ├── fetch_data.py                 # Binance周数据获取
│   ├── fetch_bitstamp_data.py        # Bitstamp数据获取（NEW）
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
│   │   ├── 完整分析报告_最新.xlsx
│   │   └── ...
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

### 1. 完整分析报告 (`reports/excel/完整分析报告_最新.xlsx`)

**月度模式分析部分：**
- **月度模式_总体汇总**: 所有交易对的整体统计
- **月度模式_年度汇总**: 按年份统计AMDX/XAMD分布
- **BTC月份分布统计**: BTC按月份（1-12月）统计模式分布
- **ETH月份分布统计**: ETH按月份（1-12月）统计模式分布
- **BTCUSDT_周数据**: BTC周数据（含X/A/M/D走势列）
- **ETHUSDT_周数据**: ETH周数据（含X/A/M/D走势列）
- **BTCUSD_周数据**: BTC现货周数据（NEW）

**周度模式分析部分：**
- **周度模式_总体汇总**: 所有交易对的整体统计
- **周度模式_年度汇总**: 按年份统计XAMDXAM/AMDXAMD分布
- **BTC周度详细**: BTC每周7天的详细走势明细和突破幅度
- **ETH周度详细**: ETH每周7天的详细走势明细和突破幅度
- **BTC日数据**: BTC每日数据（含周度模式、走势明细、突破幅度）
- **ETH日数据**: ETH每日数据（含周度模式、走势明细、突破幅度）

### 2. 其他报告

- **月度模式报告** (`reports/excel/AMDX_XAMD_分析报告_最新.xlsx`): 仅月度模式分析
- **周度模式报告** (`reports/excel/周度模式分析_最新.xlsx`): 仅周度模式分析
- **完整数据导出** (`reports/excel/完整数据导出_最新.xlsx`): 原始数据导出

## 数据说明

### 数据来源

- **Binance 期货API** (fapi.binance.com)
  - BTC/USDT 永续合约
  - ETH/USDT 永续合约
  - 使用1小时K线数据计算周最高/最低价

- **Bitstamp API** (www.bitstamp.net) 🆕
  - BTC/USD 现货
  - 历史数据从2011年开始
  - 使用1小时K线数据

### 数据范围

- **周数据**: 从各交易所API可用数据开始
  - Binance: 约2019年9月起
  - Bitstamp: 约2011年9月起
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
    {'name': 'BTCUSDT', 'display_name': 'BTC/USDT 永续合约', 
     'exchange': 'binance', ...},
    {'name': 'ETHUSDT', 'display_name': 'ETH/USDT 永续合约', 
     'exchange': 'binance', ...},
    {'name': 'BTCUSD', 'display_name': 'BTC/USD 现货', 
     'exchange': 'bitstamp', ...},  # NEW
]

# 时区设置
TZ_UTC9 = pytz.timezone('Asia/Tokyo')  # UTC+9

# 周开始/结束时间
WEEK_START_HOUR = 8   # 周一早上8点
WEEK_START_MINUTE = 0

# API配置
BINANCE_API_BASE = 'https://api.binance.com/api/v3'
BITSTAMP_API_BASE = 'https://www.bitstamp.net/api/v2'  # NEW
```

## 常见问题

### Q: 如何添加新的交易对？

在 `config.py` 的 `SYMBOLS` 列表中添加新的配置：

```python
SYMBOLS = [
    # ... 现有交易对 ...
    {
        'name': 'ETHUSD',
        'display_name': 'ETH/USD 现货',
        'api_symbol': 'ethusd',
        'use_futures': False,
        'exchange': 'bitstamp'
    }
]
```

然后重新运行 `python run_all.py --force`

### Q: Bitstamp数据如何获取？

```bash
# 首次获取（从2011年开始）
python scripts/fetch_bitstamp_data.py --force

# 增量更新
python scripts/fetch_bitstamp_data.py
```

### Q: 数据更新失败怎么办？

1. 检查网络连接
2. 确认API是否可访问
3. 查看错误日志
4. 尝试手动运行各个步骤排查问题


## GitHub Actions 自动更新

### 每周自动更新

工作流在每周一早上9点(UTC+9)自动运行，更新最新一周的数据。

### 手动触发

1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Manual Data Update" 工作流
3. 点击 "Run workflow"
4. 选择要执行的操作

## 技术要点

### API请求限制处理
- Binance：1200请求/分钟
- Bitstamp：每次最多1000条数据，需要分批获取
- 添加重试机制和延时

### 数据对齐策略
- 统一时区：UTC+9
- 统一周定义：周一8:00开始
- 处理缺失数据：向前填充

### 性能优化
- 使用数据库索引
- 批量插入数据
- 缓存计算结果

## 更新日志

### v2.0 (2025-12-12) 🆕
- ✅ 新增 Bitstamp 交易所支持
- ✅ 新增 BTC/USD 现货数据
- ✅ 新增小时数据表支持
- ✅ 优化数据库结构
- ✅ 增强主运行脚本

### v1.0 (2024)
- ✅ 基础月度模式分析
- ✅ 周度模式分析
- ✅ Binance数据获取
- ✅ Excel/PDF报告生成

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 联系方式

如有问题或建议，请提交 Issue。

