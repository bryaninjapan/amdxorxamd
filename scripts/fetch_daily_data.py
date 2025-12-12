"""
Binance API 日数据获取脚本
从Binance获取历史K线数据并聚合为日数据
"""

import requests
import sqlite3
import time
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DATABASE_PATH, BINANCE_API_BASE, BINANCE_FUTURES_API_BASE,
    SYMBOLS, TZ_UTC9, API_REQUEST_INTERVAL
)

import pytz

TZ_UTC = pytz.UTC


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
    """从Binance获取K线数据"""
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
            'limit': 1500
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            klines = response.json()
            
            if not klines:
                break
            
            all_klines.extend(klines)
            
            current_start = klines[-1][0] + 1
            
            if len(klines) < 1500:
                break
            
            time.sleep(API_REQUEST_INTERVAL)
            
        except requests.exceptions.RequestException as e:
            print(f"  API请求错误: {e}")
            time.sleep(5)
            continue
    
    return all_klines


def process_klines_to_daily(klines, trade_date_utc9):
    """
    将K线数据处理为日数据
    
    Args:
        klines: K线数据列表
        trade_date_utc9: 交易日期（UTC+9，当天00:00:00）
    
    Returns:
        dict: 日数据
    """
    if not klines:
        return None
    
    # 计算当天的开始和结束时间（UTC+9）
    day_start = trade_date_utc9.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1) - timedelta(seconds=1)
    
    # 转换为UTC时间戳
    start_ts = utc9_to_utc(day_start).timestamp() * 1000
    end_ts = utc9_to_utc(day_end).timestamp() * 1000
    
    # 过滤在时间范围内的K线
    valid_klines = [k for k in klines if start_ts <= k[0] <= end_ts]
    
    if not valid_klines:
        return None
    
    # 提取价格数据
    high_prices = [float(k[2]) for k in valid_klines]
    low_prices = [float(k[3]) for k in valid_klines]
    volumes = [float(k[5]) for k in valid_klines]
    
    return {
        'day_high': max(high_prices),
        'day_low': min(low_prices),
        'day_open': float(valid_klines[0][1]),
        'day_close': float(valid_klines[-1][4]),
        'day_volume': sum(volumes),
        'data_points': len(valid_klines)
    }


def calculate_data_quality(data_points, expected_points=24):
    """计算数据质量分数"""
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


def generate_all_dates(start_date_utc9, end_date_utc9):
    """生成从开始日期到结束日期的所有日期"""
    current = start_date_utc9.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end_date_utc9.replace(hour=0, minute=0, second=0, microsecond=0)
    
    while current <= end:
        yield current
        current += timedelta(days=1)


def get_earliest_available_date(symbol, use_futures=True):
    """获取Binance上该交易对最早可用数据的日期"""
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
    return TZ_UTC9.localize(datetime(2019, 9, 8, 0, 0, 0))


def fetch_and_store_daily_data(symbol_config, conn, force_update=False):
    """获取并存储日数据"""
    cursor = conn.cursor()
    symbol = symbol_config['name']
    api_symbol = symbol_config['api_symbol']
    use_futures = symbol_config.get('use_futures', True)
    
    print(f"\n处理交易对: {symbol}")
    print("-" * 40)
    
    # 获取symbol_id
    cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    
    if not result:
        print(f"  错误: 交易对 {symbol} 不存在于数据库中")
        return
    
    symbol_id = result[0]
    
    # 获取最早可用数据日期
    print(f"  检查Binance数据可用性...")
    earliest_date = get_earliest_available_date(api_symbol, use_futures)
    print(f"  最早可用数据: {earliest_date.strftime('%Y-%m-%d')}")
    
    # 确定开始日期
    if force_update:
        start_date = earliest_date
    else:
        # 查找数据库中最后一条记录
        cursor.execute("""
            SELECT MAX(trade_date) FROM daily_data WHERE symbol_id = ?
        """, (symbol_id,))
        last_date = cursor.fetchone()[0]
        
        if last_date:
            start_date = TZ_UTC9.localize(datetime.strptime(last_date, '%Y-%m-%d'))
            start_date = start_date + timedelta(days=1)
            print(f"  从上次更新点继续: {start_date.strftime('%Y-%m-%d')}")
        else:
            start_date = earliest_date
    
    # 确定结束日期（昨天，确保数据完整）
    now_utc9 = datetime.now(TZ_UTC9)
    end_date = (now_utc9 - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"  数据范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    if start_date > end_date:
        print(f"  数据已是最新，无需更新")
        return
    
    # 记录更新日志
    update_start_time = time.time()
    records_added = 0
    records_updated = 0
    
    # 获取所有需要处理的日期
    dates = list(generate_all_dates(start_date, end_date))
    total_dates = len(dates)
    
    print(f"  需要处理 {total_dates} 天的数据...")
    
    # 批量获取K线数据（每次获取一周的数据）
    for i in range(0, total_dates, 7):
        batch_dates = dates[i:min(i+7, total_dates)]
        batch_start = batch_dates[0]
        batch_end = batch_dates[-1] + timedelta(days=1)
        
        # 显示进度
        if i % 28 == 0:
            print(f"  处理进度: {i}/{total_dates} ({i * 100 // total_dates}%)")
        
        # 转换为UTC时间用于API查询
        batch_start_utc = utc9_to_utc(batch_start)
        batch_end_utc = utc9_to_utc(batch_end)
        
        # 获取K线数据
        klines = fetch_klines_from_binance(api_symbol, batch_start_utc, batch_end_utc, use_futures)
        
        # 处理每天的数据
        for trade_date in batch_dates:
            # 处理K线数据
            daily_data = process_klines_to_daily(klines, trade_date)
            
            if not daily_data:
                continue
            
            # 计算数据质量分数
            quality_score = calculate_data_quality(daily_data['data_points'])
            
            # 获取日期信息
            day_of_week = trade_date.weekday()  # 0=周一, 6=周日
            
            # 检查是否已存在
            trade_date_str = trade_date.strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT id FROM daily_data WHERE symbol_id = ? AND trade_date = ?
            """, (symbol_id, trade_date_str))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                cursor.execute("""
                    UPDATE daily_data SET
                        day_high = ?, day_low = ?, day_open = ?, day_close = ?,
                        day_volume = ?, data_points = ?, data_quality_score = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (daily_data['day_high'], daily_data['day_low'],
                      daily_data['day_open'], daily_data['day_close'],
                      daily_data['day_volume'], daily_data['data_points'],
                      quality_score, existing[0]))
                records_updated += 1
            else:
                # 插入
                cursor.execute("""
                    INSERT INTO daily_data
                    (symbol_id, trade_date, trade_date_utc9, day_of_week,
                     year, month, day,
                     day_high, day_low, day_open, day_close, day_volume,
                     data_points, data_quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol_id, trade_date_str,
                      trade_date.strftime('%Y-%m-%d %H:%M:%S'),
                      day_of_week,
                      trade_date.year, trade_date.month, trade_date.day,
                      daily_data['day_high'], daily_data['day_low'],
                      daily_data['day_open'], daily_data['day_close'],
                      daily_data['day_volume'],
                      daily_data['data_points'], quality_score))
                records_added += 1
            
            # 每100条提交一次
            if (records_added + records_updated) % 100 == 0:
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


def main(force_update=False):
    """主函数"""
    print("=" * 60)
    print("AMDX/XAMD 日数据获取程序")
    print("=" * 60)
    print(f"当前时间(UTC+9): {datetime.now(TZ_UTC9).strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        for symbol_config in SYMBOLS:
            fetch_and_store_daily_data(symbol_config, conn, force_update)
        
        print("\n" + "=" * 60)
        print("日数据获取完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='从Binance获取日数据')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制重新获取所有数据')
    
    args = parser.parse_args()
    main(force_update=args.force)

