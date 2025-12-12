"""
AMDX/XAMD 模式计算脚本
判断每个月第一周的模式
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH, TZ_UTC9, WEEK_START_HOUR
import pytz


def get_first_monday_of_month(year, month):
    """
    获取该月第一个周一
    如果1号不是周一，返回该月第一个周一的日期
    """
    first_day = datetime(year, month, 1)
    
    # 如果1号是周一
    if first_day.weekday() == 0:
        return first_day
    
    # 找到该月第一个周一
    days_until_monday = (7 - first_day.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    
    first_monday = first_day + timedelta(days=days_until_monday)
    return first_monday


def get_first_week_of_month(symbol_id, year, month, conn):
    """
    获取该月第一个完整周的数据
    
    第一周定义：
    - 如果1号是周一，则第一周从1号开始
    - 如果1号不是周一，则第一周从该月第一个周一开始
    """
    cursor = conn.cursor()
    
    # 获取该月第一个周一
    first_monday = get_first_monday_of_month(year, month)
    first_monday_str = first_monday.strftime('%Y-%m-%d')
    
    # 查找该周一开始的周数据
    cursor.execute("""
        SELECT id, week_start, week_end, week_high, week_low, 
               week_open, week_close, data_quality_score
        FROM weekly_data
        WHERE symbol_id = ? 
          AND year = ? 
          AND month = ?
          AND DATE(week_start) = ?
        ORDER BY week_start ASC
        LIMIT 1
    """, (symbol_id, year, month, first_monday_str))
    
    result = cursor.fetchone()
    
    if not result:
        # 如果精确匹配失败，尝试查找该月第一周
        cursor.execute("""
            SELECT id, week_start, week_end, week_high, week_low,
                   week_open, week_close, data_quality_score
            FROM weekly_data
            WHERE symbol_id = ?
              AND year = ?
              AND month = ?
            ORDER BY week_start ASC
            LIMIT 1
        """, (symbol_id, year, month))
        result = cursor.fetchone()
    
    return result


def get_previous_week(week_start_str, symbol_id, conn):
    """
    获取指定周之前一周的数据
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, week_start, week_high, week_low, data_quality_score
        FROM weekly_data
        WHERE symbol_id = ? 
          AND week_start < ?
        ORDER BY week_start DESC
        LIMIT 1
    """, (symbol_id, week_start_str))
    
    return cursor.fetchone()


def determine_pattern(first_week_high, first_week_low, prev_week_high, prev_week_low):
    """
    判断模式
    
    AMDX: 第一周的最高和最低不超过前一周的区间
    XAMD: 第一周的最高或最低超过前一周的区间
    
    边界情况：等于前一周最高/最低不算突破
    
    Returns:
        tuple: (pattern, is_breakout_up, is_breakout_down, 
                breakout_up_amount, breakout_down_amount,
                breakout_up_percent, breakout_down_percent)
    """
    # 判断是否突破
    is_breakout_up = first_week_high > prev_week_high
    is_breakout_down = first_week_low < prev_week_low
    
    # 计算突破幅度
    breakout_up_amount = None
    breakout_down_amount = None
    breakout_up_percent = None
    breakout_down_percent = None
    
    if is_breakout_up:
        breakout_up_amount = first_week_high - prev_week_high
        breakout_up_percent = (breakout_up_amount / prev_week_high) * 100
    
    if is_breakout_down:
        breakout_down_amount = prev_week_low - first_week_low
        breakout_down_percent = (breakout_down_amount / prev_week_low) * 100
    
    # 判断模式
    if is_breakout_up or is_breakout_down:
        pattern = 'XAMD'
    else:
        pattern = 'AMDX'
    
    return (pattern, is_breakout_up, is_breakout_down,
            breakout_up_amount, breakout_down_amount,
            breakout_up_percent, breakout_down_percent)


def calculate_pattern_for_month(symbol_id, year, month, conn):
    """
    计算指定月份的模式
    """
    cursor = conn.cursor()
    
    # 获取该月第一周数据
    first_week = get_first_week_of_month(symbol_id, year, month, conn)
    
    if not first_week:
        return None
    
    (first_week_id, first_week_start, first_week_end, 
     first_week_high, first_week_low, first_week_open, 
     first_week_close, first_week_quality) = first_week
    
    # 获取前一周数据
    prev_week = get_previous_week(first_week_start, symbol_id, conn)
    
    if not prev_week:
        # 没有前一周数据，无法判断模式
        return None
    
    (prev_week_id, prev_week_start, prev_week_high, 
     prev_week_low, prev_week_quality) = prev_week
    
    # 判断模式
    (pattern, is_breakout_up, is_breakout_down,
     breakout_up_amount, breakout_down_amount,
     breakout_up_percent, breakout_down_percent) = determine_pattern(
        first_week_high, first_week_low, prev_week_high, prev_week_low
    )
    
    # 计算数据质量分数（取两周的最低分）
    data_quality_score = min(first_week_quality or 100, prev_week_quality or 100)
    
    # 检查是否已存在记录
    cursor.execute("""
        SELECT id FROM monthly_patterns
        WHERE symbol_id = ? AND year = ? AND month = ?
    """, (symbol_id, year, month))
    
    existing = cursor.fetchone()
    
    # 构建数据
    data = {
        'symbol_id': symbol_id,
        'year': year,
        'month': month,
        'first_week_id': first_week_id,
        'previous_week_id': prev_week_id,
        'first_week_start': first_week_start,
        'pattern': pattern,
        'first_week_high': first_week_high,
        'first_week_low': first_week_low,
        'previous_week_high': prev_week_high,
        'previous_week_low': prev_week_low,
        'is_breakout_up': 1 if is_breakout_up else 0,
        'is_breakout_down': 1 if is_breakout_down else 0,
        'breakout_up_amount': breakout_up_amount,
        'breakout_down_amount': breakout_down_amount,
        'breakout_up_percent': breakout_up_percent,
        'breakout_down_percent': breakout_down_percent,
        'data_quality_score': data_quality_score
    }
    
    if existing:
        # 更新记录
        cursor.execute("""
            UPDATE monthly_patterns SET
                first_week_id = ?, previous_week_id = ?, first_week_start = ?,
                pattern = ?, first_week_high = ?, first_week_low = ?,
                previous_week_high = ?, previous_week_low = ?,
                is_breakout_up = ?, is_breakout_down = ?,
                breakout_up_amount = ?, breakout_down_amount = ?,
                breakout_up_percent = ?, breakout_down_percent = ?,
                data_quality_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data['first_week_id'], data['previous_week_id'], data['first_week_start'],
              data['pattern'], data['first_week_high'], data['first_week_low'],
              data['previous_week_high'], data['previous_week_low'],
              data['is_breakout_up'], data['is_breakout_down'],
              data['breakout_up_amount'], data['breakout_down_amount'],
              data['breakout_up_percent'], data['breakout_down_percent'],
              data['data_quality_score'], existing[0]))
    else:
        # 插入新记录
        cursor.execute("""
            INSERT INTO monthly_patterns
            (symbol_id, year, month, first_week_id, previous_week_id, first_week_start,
             pattern, first_week_high, first_week_low,
             previous_week_high, previous_week_low,
             is_breakout_up, is_breakout_down,
             breakout_up_amount, breakout_down_amount,
             breakout_up_percent, breakout_down_percent,
             data_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['symbol_id'], data['year'], data['month'],
              data['first_week_id'], data['previous_week_id'], data['first_week_start'],
              data['pattern'], data['first_week_high'], data['first_week_low'],
              data['previous_week_high'], data['previous_week_low'],
              data['is_breakout_up'], data['is_breakout_down'],
              data['breakout_up_amount'], data['breakout_down_amount'],
              data['breakout_up_percent'], data['breakout_down_percent'],
              data['data_quality_score']))
    
    conn.commit()
    return data


def calculate_all_patterns(conn):
    """
    计算所有交易对的所有月份模式
    """
    cursor = conn.cursor()
    
    # 获取所有交易对
    cursor.execute("SELECT id, symbol FROM symbols WHERE is_active = 1")
    symbols = cursor.fetchall()
    
    for symbol_id, symbol_name in symbols:
        print(f"\n处理交易对: {symbol_name}")
        print("-" * 40)
        
        # 获取该交易对的所有不同年月组合
        cursor.execute("""
            SELECT DISTINCT year, month
            FROM weekly_data
            WHERE symbol_id = ?
            ORDER BY year, month
        """, (symbol_id,))
        
        months = cursor.fetchall()
        
        amdx_count = 0
        xamd_count = 0
        
        for year, month in months:
            result = calculate_pattern_for_month(symbol_id, year, month, conn)
            
            if result:
                pattern = result['pattern']
                if pattern == 'AMDX':
                    amdx_count += 1
                else:
                    xamd_count += 1
                
                # 显示详情
                breakout_info = ""
                if result['is_breakout_up']:
                    breakout_info += f" ↑{result['breakout_up_percent']:.2f}%"
                if result['is_breakout_down']:
                    breakout_info += f" ↓{result['breakout_down_percent']:.2f}%"
                
                print(f"  {year}-{month:02d}: {pattern}{breakout_info}")
        
        total = amdx_count + xamd_count
        if total > 0:
            print(f"\n  统计: AMDX={amdx_count} ({amdx_count*100/total:.1f}%), "
                  f"XAMD={xamd_count} ({xamd_count*100/total:.1f}%)")


def run_data_quality_checks(conn):
    """
    运行数据质量检查
    """
    cursor = conn.cursor()
    
    print("\n运行数据质量检查...")
    print("-" * 40)
    
    # 检查1: 缺失数据
    cursor.execute("""
        SELECT s.symbol, COUNT(*) as low_quality_weeks
        FROM weekly_data wd
        JOIN symbols s ON wd.symbol_id = s.id
        WHERE wd.data_quality_score < 80
        GROUP BY s.symbol
    """)
    
    low_quality = cursor.fetchall()
    
    for symbol, count in low_quality:
        print(f"  警告: {symbol} 有 {count} 周数据质量较低")
        
        # 记录到日志
        cursor.execute("""
            INSERT INTO data_quality_logs
            (symbol_id, check_date, check_type, status, message, affected_records)
            SELECT id, CURRENT_TIMESTAMP, 'LOW_QUALITY_DATA', 'WARN',
                   '数据质量分数低于80', ?
            FROM symbols WHERE symbol = ?
        """, (count, symbol))
    
    # 检查2: 异常价格变动
    cursor.execute("""
        SELECT s.symbol, wd.week_start,
               ((wd.week_high - wd.week_low) / wd.week_low * 100) as price_range_percent
        FROM weekly_data wd
        JOIN symbols s ON wd.symbol_id = s.id
        WHERE ((wd.week_high - wd.week_low) / wd.week_low * 100) > 50
        ORDER BY price_range_percent DESC
        LIMIT 10
    """)
    
    high_volatility = cursor.fetchall()
    
    for symbol, week_start, pct in high_volatility:
        print(f"  注意: {symbol} 在 {week_start[:10]} 周波动率达 {pct:.1f}%")
    
    conn.commit()
    print("  数据质量检查完成")


def main():
    """主函数"""
    print("=" * 60)
    print("AMDX/XAMD 模式计算程序")
    print("=" * 60)
    print(f"当前时间: {datetime.now(TZ_UTC9).strftime('%Y-%m-%d %H:%M:%S')} (UTC+9)")
    
    # 连接数据库
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # 计算所有模式
        calculate_all_patterns(conn)
        
        # 运行数据质量检查
        run_data_quality_checks(conn)
        
        print("\n" + "=" * 60)
        print("模式计算完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()

