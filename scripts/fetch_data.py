"""
Binance API 数据获取脚本
从Binance获取历史K线数据并存入数据库
"""

import requests
import sqlite3
import time
import os
import sys
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DATABASE_PATH, BINANCE_API_BASE, BINANCE_FUTURES_API_BASE,
    SYMBOLS, TZ_UTC9, API_REQUEST_INTERVAL, QUALITY_THRESHOLDS,
    WEEK_START_HOUR, WEEK_START_MINUTE, DATA_DIR
)

import pytz

# UTC时区
TZ_UTC = pytz.UTC


def get_week_boundaries(date_utc9):
    """
    获取指定日期所在周的边界（UTC+9时区）
    周开始：周一早上8点(UTC+9)
    周结束：下周一早上7:59(UTC+9)
    """
    # 确保日期是UTC+9时区
    if date_utc9.tzinfo is None:
        date_utc9 = TZ_UTC9.localize(date_utc9)
    
    # 找到该周的周一
    days_since_monday = date_utc9.weekday()
    monday = date_utc9 - timedelta(days=days_since_monday)
    
    # 周开始：周一早上8点
    week_start = monday.replace(hour=WEEK_START_HOUR, minute=WEEK_START_MINUTE, 
                                second=0, microsecond=0)
    
    # 周结束：下周一早上7:59
    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)
    
    return week_start, week_end


def get_first_monday_of_month(year, month):
    """
    获取该月第一个周一（早上8点，UTC+9）
    如果1号是周一，则返回1号；否则返回该月第一个周一
    """
    first_day = TZ_UTC9.localize(datetime(year, month, 1, WEEK_START_HOUR, 0, 0))
    
    # 如果1号是周一
    if first_day.weekday() == 0:
        return first_day
    
    # 找到该月第一个周一
    days_until_monday = (7 - first_day.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    
    first_monday = first_day + timedelta(days=days_until_monday)
    return first_monday.replace(hour=WEEK_START_HOUR, minute=0, second=0, microsecond=0)


def utc9_to_utc(dt_utc9):
    """将UTC+9时间转换为UTC时间"""
    if dt_utc9.tzinfo is None:
        dt_utc9 = TZ_UTC9.localize(dt_utc9)
    return dt_utc9.astimezone(TZ_UTC)


def utc_to_utc9(dt_utc):
    """将UTC时间转换为UTC+9时间"""
    if dt_utc.tzinfo is None:
        dt_utc = TZ_UTC.localize(dt_utc)
    return dt_utc.astimezone(TZ_UTC9)


def fetch_klines_from_binance(symbol, start_time_utc, end_time_utc, use_futures=True):
    """
    从Binance获取K线数据
    
    Args:
        symbol: 交易对符号（如 BTCUSDT）
        start_time_utc: 开始时间（UTC）
        end_time_utc: 结束时间（UTC）
        use_futures: 是否使用期货API
    
    Returns:
        list: K线数据列表
    """
    base_url = BINANCE_FUTURES_API_BASE if use_futures else BINANCE_API_BASE
    url = f"{base_url}/klines"
    
    all_klines = []
    current_start = int(start_time_utc.timestamp() * 1000)
    end_ms = int(end_time_utc.timestamp() * 1000)
    
    while current_start < end_ms:
        params = {
            'symbol': symbol,
            'interval': '1h',  # 1小时K线
            'startTime': current_start,
            'endTime': end_ms,
            'limit': 1500  # 最大限制
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            klines = response.json()
            
            if not klines:
                break
            
            all_klines.extend(klines)
            
            # 更新起始时间为最后一条数据的时间 + 1毫秒
            current_start = klines[-1][0] + 1
            
            # 如果返回数据少于限制，说明已获取完毕
            if len(klines) < 1500:
                break
            
            # 避免请求过快
            time.sleep(API_REQUEST_INTERVAL)
            
        except requests.exceptions.RequestException as e:
            print(f"  API请求错误: {e}")
            time.sleep(5)  # 出错后等待5秒重试
            continue
    
    return all_klines


def process_klines_to_weekly(klines, week_start_utc9, week_end_utc9):
    """
    将K线数据处理为周数据
    
    Args:
        klines: K线数据列表
        week_start_utc9: 周开始时间（UTC+9）
        week_end_utc9: 周结束时间（UTC+9）
    
    Returns:
        dict: 周数据，包含最高价、最低价、开盘价、收盘价等
    """
    if not klines:
        return None
    
    # 转换为UTC时间戳范围
    start_ts = utc9_to_utc(week_start_utc9).timestamp() * 1000
    end_ts = utc9_to_utc(week_end_utc9).timestamp() * 1000
    
    # 过滤在时间范围内的K线
    valid_klines = [k for k in klines if start_ts <= k[0] <= end_ts]
    
    if not valid_klines:
        return None
    
    # 提取价格数据
    # K线格式: [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]
    high_prices = [float(k[2]) for k in valid_klines]
    low_prices = [float(k[3]) for k in valid_klines]
    
    return {
        'week_high': max(high_prices),
        'week_low': min(low_prices),
        'week_open': float(valid_klines[0][1]),
        'week_close': float(valid_klines[-1][4]),
        'data_points': len(valid_klines)
    }


def calculate_data_quality(data_points, expected_points=168):
    """
    计算数据质量分数
    
    Args:
        data_points: 实际数据点数
        expected_points: 预期数据点数（一周168小时）
    
    Returns:
        int: 数据质量分数 (0-100)
    """
    if data_points >= expected_points * 0.95:
        return 100
    elif data_points >= expected_points * 0.8:
        return 80
    elif data_points >= expected_points * 0.5:
        return 60
    elif data_points >= expected_points * 0.3:
        return 40
    else:
        return 20


def generate_all_weeks(start_date_utc9, end_date_utc9):
    """
    生成从开始日期到结束日期的所有周
    
    Args:
        start_date_utc9: 开始日期（UTC+9）
        end_date_utc9: 结束日期（UTC+9）
    
    Yields:
        tuple: (week_start, week_end, year, month, week_of_year, week_of_month)
    """
    current = start_date_utc9
    
    while current < end_date_utc9:
        week_start, week_end = get_week_boundaries(current)
        
        # 确保周结束不超过结束日期
        if week_end > end_date_utc9:
            week_end = end_date_utc9
        
        # 确保周开始不早于开始日期
        if week_start < start_date_utc9:
            week_start = start_date_utc9
        
        year = week_start.year
        month = week_start.month
        week_of_year = week_start.isocalendar()[1]
        
        # 计算月内第几周
        first_monday = get_first_monday_of_month(year, month)
        if week_start >= first_monday:
            week_of_month = ((week_start - first_monday).days // 7) + 1
        else:
            week_of_month = 0
        
        yield (week_start, week_end, year, month, week_of_year, week_of_month)
        
        # 移动到下一周
        current = week_end + timedelta(seconds=1)


def get_earliest_available_date(symbol, use_futures=True):
    """
    获取Binance上该交易对最早可用数据的日期
    """
    base_url = BINANCE_FUTURES_API_BASE if use_futures else BINANCE_API_BASE
    url = f"{base_url}/klines"
    
    # 尝试从2017年开始
    test_date = TZ_UTC.localize(datetime(2017, 1, 1))
    
    params = {
        'symbol': symbol,
        'interval': '1d',
        'startTime': int(test_date.timestamp() * 1000),
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        klines = response.json()
        
        if klines:
            earliest_ts = klines[0][0] / 1000
            earliest_date = datetime.fromtimestamp(earliest_ts, tz=TZ_UTC)
            return utc_to_utc9(earliest_date)
    except Exception as e:
        print(f"  获取最早日期失败: {e}")
    
    # 默认返回2019年9月（Binance期货上线时间）
    return TZ_UTC9.localize(datetime(2019, 9, 8, 8, 0, 0))


def fetch_and_store_weekly_data(symbol_config, conn, force_update=False):
    """
    获取并存储周数据
    
    Args:
        symbol_config: 交易对配置
        conn: 数据库连接
        force_update: 是否强制更新所有数据
    """
    cursor = conn.cursor()
    symbol = symbol_config['name']
    api_symbol = symbol_config['api_symbol']
    use_futures = symbol_config.get('use_futures', True)
    
    print(f"\n处理交易对: {symbol}")
    print("-" * 40)
    
    # 获取symbol_id
    cursor.execute("SELECT id, data_start_date FROM symbols WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    
    if not result:
        print(f"  错误: 交易对 {symbol} 不存在于数据库中")
        return
    
    symbol_id = result[0]
    
    # 获取最早可用数据日期
    print(f"  检查Binance数据可用性...")
    earliest_date = get_earliest_available_date(api_symbol, use_futures)
    print(f"  最早可用数据: {earliest_date.strftime('%Y-%m-%d')}")
    
    # 更新symbols表中的data_start_date
    cursor.execute("""
        UPDATE symbols SET data_start_date = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (earliest_date.strftime('%Y-%m-%d %H:%M:%S'), symbol_id))
    
    # 确定开始日期
    if force_update:
        start_date = earliest_date
    else:
        # 查找数据库中最后一条记录
        cursor.execute("""
            SELECT MAX(week_end) FROM weekly_data WHERE symbol_id = ?
        """, (symbol_id,))
        last_date = cursor.fetchone()[0]
        
        if last_date:
            start_date = TZ_UTC9.localize(datetime.strptime(last_date, '%Y-%m-%d %H:%M:%S'))
            start_date = start_date + timedelta(seconds=1)
            print(f"  从上次更新点继续: {start_date.strftime('%Y-%m-%d')}")
        else:
            start_date = earliest_date
    
    # 确定结束日期（当前时间的上一个完整周）
    now_utc9 = datetime.now(TZ_UTC9)
    _, current_week_end = get_week_boundaries(now_utc9)
    
    # 如果当前周还未结束，使用上一周的结束时间
    if now_utc9 < current_week_end:
        end_date = current_week_end - timedelta(days=7)
    else:
        end_date = current_week_end
    
    print(f"  数据范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    # 如果开始日期已经超过结束日期，无需更新
    if start_date >= end_date:
        print(f"  数据已是最新，无需更新")
        return
    
    # 记录更新日志
    update_start_time = time.time()
    records_added = 0
    records_updated = 0
    
    # 获取所有需要处理的周
    weeks = list(generate_all_weeks(start_date, end_date))
    total_weeks = len(weeks)
    
    print(f"  需要处理 {total_weeks} 周的数据...")
    
    for i, (week_start, week_end, year, month, week_of_year, week_of_month) in enumerate(weeks):
        # 显示进度
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  处理进度: {i + 1}/{total_weeks} ({(i + 1) * 100 // total_weeks}%)")
        
        # 转换为UTC时间用于API查询
        week_start_utc = utc9_to_utc(week_start)
        week_end_utc = utc9_to_utc(week_end)
        
        # 获取K线数据
        klines = fetch_klines_from_binance(api_symbol, week_start_utc, week_end_utc, use_futures)
        
        if not klines:
            print(f"    警告: {week_start.strftime('%Y-%m-%d')} 周无数据")
            continue
        
        # 处理K线数据
        weekly_data = process_klines_to_weekly(klines, week_start, week_end)
        
        if not weekly_data:
            continue
        
        # 计算数据质量分数
        quality_score = calculate_data_quality(weekly_data['data_points'])
        
        # 检查是否已存在
        cursor.execute("""
            SELECT id FROM weekly_data WHERE symbol_id = ? AND week_start = ?
        """, (symbol_id, week_start.strftime('%Y-%m-%d %H:%M:%S')))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新记录
            cursor.execute("""
                UPDATE weekly_data SET
                    week_high = ?, week_low = ?, week_open = ?, week_close = ?,
                    data_points = ?, data_quality_score = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (weekly_data['week_high'], weekly_data['week_low'],
                  weekly_data['week_open'], weekly_data['week_close'],
                  weekly_data['data_points'], quality_score, existing[0]))
            records_updated += 1
        else:
            # 插入新记录
            cursor.execute("""
                INSERT INTO weekly_data
                (symbol_id, week_start, week_end, week_start_utc, week_end_utc,
                 year, month, week_of_year, week_of_month,
                 week_high, week_low, week_open, week_close,
                 data_points, data_quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol_id,
                  week_start.strftime('%Y-%m-%d %H:%M:%S'),
                  week_end.strftime('%Y-%m-%d %H:%M:%S'),
                  week_start_utc.strftime('%Y-%m-%d %H:%M:%S'),
                  week_end_utc.strftime('%Y-%m-%d %H:%M:%S'),
                  year, month, week_of_year, week_of_month,
                  weekly_data['week_high'], weekly_data['week_low'],
                  weekly_data['week_open'], weekly_data['week_close'],
                  weekly_data['data_points'], quality_score))
            records_added += 1
        
        # 每50条提交一次
        if (records_added + records_updated) % 50 == 0:
            conn.commit()
    
    conn.commit()
    
    # 记录更新日志
    execution_time = time.time() - update_start_time
    cursor.execute("""
        INSERT INTO update_logs
        (symbol_id, update_type, start_date, end_date, records_added, records_updated,
         status, execution_time_seconds)
        VALUES (?, ?, ?, ?, ?, ?, 'SUCCESS', ?)
    """, (symbol_id, 'FULL' if force_update else 'INCREMENTAL',
          start_date.strftime('%Y-%m-%d %H:%M:%S'),
          end_date.strftime('%Y-%m-%d %H:%M:%S'),
          records_added, records_updated, execution_time))
    
    conn.commit()
    
    print(f"\n  完成! 新增: {records_added}, 更新: {records_updated}, 耗时: {execution_time:.1f}秒")


def update_system_config(conn):
    """更新系统配置"""
    cursor = conn.cursor()
    now = datetime.now(TZ_UTC9).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        UPDATE system_config SET value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE key = 'last_update'
    """, (now,))
    
    conn.commit()


def main(force_update=False):
    """主函数"""
    print("=" * 60)
    print("AMDX/XAMD 数据获取程序")
    print("=" * 60)
    print(f"当前时间(UTC+9): {datetime.now(TZ_UTC9).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 连接数据库
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # 处理每个交易对
        for symbol_config in SYMBOLS:
            fetch_and_store_weekly_data(symbol_config, conn, force_update)
        
        # 更新系统配置
        update_system_config(conn)
        
        print("\n" + "=" * 60)
        print("数据获取完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='从Binance获取K线数据')
    parser.add_argument('--force', '-f', action='store_true', 
                        help='强制重新获取所有数据')
    
    args = parser.parse_args()
    main(force_update=args.force)

