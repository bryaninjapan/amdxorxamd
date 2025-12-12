"""
AMDX/XAMD 模式分析系统配置文件
"""

import os
from datetime import datetime
import pytz

# ==================== 时区设置 ====================
TZ_UTC9 = pytz.timezone('Asia/Tokyo')  # UTC+9 (东京时间)

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'patterns.db')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# ==================== Binance API 配置 ====================
# 使用公开API，不需要密钥
BINANCE_API_BASE = 'https://api.binance.com/api/v3'
BINANCE_FUTURES_API_BASE = 'https://fapi.binance.com/fapi/v1'

# ==================== Bitstamp API 配置 ====================
BITSTAMP_API_BASE = 'https://www.bitstamp.net/api/v2'

# API请求间隔（秒），避免限流
API_REQUEST_INTERVAL = 0.5

# ==================== 交易对配置 ====================
SYMBOLS = [
    {
        'name': 'BTCUSDT',
        'display_name': 'BTC/USDT 永续合约',
        'api_symbol': 'BTCUSDT',
        'use_futures': True,
        'exchange': 'binance'
    },
    {
        'name': 'ETHUSDT', 
        'display_name': 'ETH/USDT 永续合约',
        'api_symbol': 'ETHUSDT',
        'use_futures': True,
        'exchange': 'binance'
    },
    {
        'name': 'BTCUSD',
        'display_name': 'BTC/USD 现货',
        'api_symbol': 'btcusd',
        'use_futures': False,
        'exchange': 'bitstamp'
    }
]

# ==================== 时间配置 ====================
# 每周开始时间：周一早上8点(UTC+9)
WEEK_START_HOUR = 8
WEEK_START_MINUTE = 0

# 每周结束时间：下周一早上7:59(UTC+9)
WEEK_END_HOUR = 7
WEEK_END_MINUTE = 59

# ==================== 数据质量配置 ====================
QUALITY_THRESHOLDS = {
    'max_price_change_percent': 100,  # 单周最大价格变动百分比（异常值检测）
    'min_data_points_per_week': 100,  # 每周最少数据点数（1小时K线约168个点）
    'missing_data_tolerance': 0.10    # 缺失数据容忍度（10%）
}

# ==================== 报告配置 ====================
REPORT_CONFIG = {
    'excel_engine': 'openpyxl',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'decimal_places': 2
}

# ==================== 创建必要的目录 ====================
def ensure_directories():
    """确保所有必要的目录存在"""
    dirs = [
        DATABASE_DIR,
        REPORTS_DIR,
        os.path.join(REPORTS_DIR, 'excel'),
        os.path.join(REPORTS_DIR, 'pdf'),
        DATA_DIR,
        os.path.join(DATA_DIR, 'raw'),
        os.path.join(DATA_DIR, 'processed')
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

ensure_directories()

