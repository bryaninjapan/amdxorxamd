"""
周度模式计算脚本
计算每周的7字母模式（XAMDXAM 或 AMDXAMD）
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH, TZ_UTC9, WEEK_START_HOUR, WEEK_START_MINUTE
import pytz


def determine_trend_detail(today_high, today_low, prev_high, prev_low):
    """
    判断走势明细（相对于前一天）
    
    返回：
    - '同时向上和向下突破'
    - '在区间内'
    - '向上突破'
    - '向下突破'
    """
    is_breakout_up = today_high > prev_high
    is_breakout_down = today_low < prev_low
    
    if is_breakout_up and is_breakout_down:
        return '同时向上和向下突破'
    elif is_breakout_up:
        return '向上突破'
    elif is_breakout_down:
        return '向下突破'
    else:
        return '在区间内'


def calculate_breakout_percent(today_high, today_low, prev_high, prev_low):
    """计算突破幅度百分比"""
    breakout_up_percent = None
    breakout_down_percent = None
    
    if today_high > prev_high:
        breakout_up_percent = ((today_high - prev_high) / prev_high) * 100
    
    if today_low < prev_low:
        breakout_down_percent = ((prev_low - today_low) / prev_low) * 100
    
    return breakout_up_percent, breakout_down_percent


def determine_weekly_pattern(monday_high, monday_low, prev_sunday_high, prev_sunday_low):
    """
    判断周度模式（XAMDXAM 或 AMDXAMD）
    
    只判断周一相对于上周日：
    - 如果突破 → XAMDXAM
    - 如果在区间内 → AMDXAMD
    """
    is_breakout = (monday_high > prev_sunday_high) or (monday_low < prev_sunday_low)
    
    if is_breakout:
        return 'XAMDXAM'
    else:
        return 'AMDXAMD'


def get_week_mondays(conn, symbol_id):
    """获取所有完整周的周一日期"""
    cursor = conn.cursor()
    
    # 从日数据表中获取所有周一的数据
    cursor.execute("""
        SELECT DISTINCT trade_date
        FROM daily_data
        WHERE symbol_id = ? AND day_of_week = 0
        ORDER BY trade_date
    """, (symbol_id,))
    
    return [row[0] for row in cursor.fetchall()]


def calculate_pattern_for_week(symbol_id, monday_date_str, conn):
    """计算指定周的模式"""
    cursor = conn.cursor()
    
    # 解析周一日期
    monday_date = datetime.strptime(monday_date_str, '%Y-%m-%d')
    
    # 获取周一到周日的日数据
    days_data = {}
    for i in range(7):
        day_date = monday_date + timedelta(days=i)
        day_date_str = day_date.strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT id, day_high, day_low, day_open, day_close
            FROM daily_data
            WHERE symbol_id = ? AND trade_date = ?
        """, (symbol_id, day_date_str))
        
        day_data = cursor.fetchone()
        if day_data:
            days_data[i] = {
                'id': day_data[0],
                'high': day_data[1],
                'low': day_data[2],
                'open': day_data[3],
                'close': day_data[4]
            }
    
    # 检查是否有周一数据
    if 0 not in days_data:
        return None
    
    monday = days_data[0]
    
    # 获取前一周周日的数据
    prev_sunday_date = monday_date - timedelta(days=1)
    prev_sunday_str = prev_sunday_date.strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT id, day_high, day_low
        FROM daily_data
        WHERE symbol_id = ? AND trade_date = ?
    """, (symbol_id, prev_sunday_str))
    
    prev_sunday = cursor.fetchone()
    if not prev_sunday:
        return None  # 没有前一周周日数据，无法判断
    
    prev_sunday_id, prev_sunday_high, prev_sunday_low = prev_sunday
    
    # 判断周度模式
    pattern = determine_weekly_pattern(
        monday['high'], monday['low'],
        prev_sunday_high, prev_sunday_low
    )
    
    # 计算周一相对于上周日的突破情况
    monday_is_breakout_up = monday['high'] > prev_sunday_high
    monday_is_breakout_down = monday['low'] < prev_sunday_low
    monday_breakout_up_percent, monday_breakout_down_percent = calculate_breakout_percent(
        monday['high'], monday['low'],
        prev_sunday_high, prev_sunday_low
    )
    monday_trend_detail = determine_trend_detail(
        monday['high'], monday['low'],
        prev_sunday_high, prev_sunday_low
    )
    
    # 计算周二到周日的走势明细
    trend_details = {}
    breakout_percents = {}
    
    for i in range(1, 7):  # 周二到周日
        if i not in days_data or (i-1) not in days_data:
            continue
        
        today = days_data[i]
        yesterday = days_data[i-1]
        
        trend_detail = determine_trend_detail(
            today['high'], today['low'],
            yesterday['high'], yesterday['low']
        )
        trend_details[i] = trend_detail
        
        breakout_up_pct, breakout_down_pct = calculate_breakout_percent(
            today['high'], today['low'],
            yesterday['high'], yesterday['low']
        )
        breakout_percents[i] = (breakout_up_pct, breakout_down_pct)
    
    # 计算周开始和结束时间
    week_start = TZ_UTC9.localize(monday_date.replace(hour=WEEK_START_HOUR, minute=WEEK_START_MINUTE, second=0))
    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)
    
    # 检查是否已存在记录
    cursor.execute("""
        SELECT id FROM weekly_patterns
        WHERE symbol_id = ? AND week_start = ?
    """, (symbol_id, week_start.strftime('%Y-%m-%d %H:%M:%S')))
    
    existing = cursor.fetchone()
    
    # 构建数据
    data = {
        'symbol_id': symbol_id,
        'week_start': week_start,
        'week_end': week_end,
        'year': week_start.year,
        'month': week_start.month,
        'week_of_year': week_start.isocalendar()[1],
        'pattern': pattern,
        'monday_id': monday['id'],
        'tuesday_id': days_data.get(1, {}).get('id'),
        'wednesday_id': days_data.get(2, {}).get('id'),
        'thursday_id': days_data.get(3, {}).get('id'),
        'friday_id': days_data.get(4, {}).get('id'),
        'saturday_id': days_data.get(5, {}).get('id'),
        'sunday_id': days_data.get(6, {}).get('id'),
        'previous_sunday_id': prev_sunday_id,
        'monday_high': monday['high'],
        'monday_low': monday['low'],
        'previous_sunday_high': prev_sunday_high,
        'previous_sunday_low': prev_sunday_low,
        'monday_is_breakout_up': 1 if monday_is_breakout_up else 0,
        'monday_is_breakout_down': 1 if monday_is_breakout_down else 0,
        'monday_breakout_up_percent': monday_breakout_up_percent,
        'monday_breakout_down_percent': monday_breakout_down_percent,
        'monday_trend_detail': monday_trend_detail,
        'tuesday_trend_detail': trend_details.get(1),
        'wednesday_trend_detail': trend_details.get(2),
        'thursday_trend_detail': trend_details.get(3),
        'friday_trend_detail': trend_details.get(4),
        'saturday_trend_detail': trend_details.get(5),
        'sunday_trend_detail': trend_details.get(6),
    }
    
    # 添加突破幅度百分比
    if 1 in breakout_percents:
        data['tuesday_breakout_up_percent'], data['tuesday_breakout_down_percent'] = breakout_percents[1]
    if 2 in breakout_percents:
        data['wednesday_breakout_up_percent'], data['wednesday_breakout_down_percent'] = breakout_percents[2]
    if 3 in breakout_percents:
        data['thursday_breakout_up_percent'], data['thursday_breakout_down_percent'] = breakout_percents[3]
    if 4 in breakout_percents:
        data['friday_breakout_up_percent'], data['friday_breakout_down_percent'] = breakout_percents[4]
    if 5 in breakout_percents:
        data['saturday_breakout_up_percent'], data['saturday_breakout_down_percent'] = breakout_percents[5]
    if 6 in breakout_percents:
        data['sunday_breakout_up_percent'], data['sunday_breakout_down_percent'] = breakout_percents[6]
    
    if existing:
        # 更新记录
        cursor.execute("""
            UPDATE weekly_patterns SET
                pattern = ?, monday_id = ?, tuesday_id = ?, wednesday_id = ?,
                thursday_id = ?, friday_id = ?, saturday_id = ?, sunday_id = ?,
                previous_sunday_id = ?, monday_high = ?, monday_low = ?,
                previous_sunday_high = ?, previous_sunday_low = ?,
                monday_is_breakout_up = ?, monday_is_breakout_down = ?,
                monday_breakout_up_percent = ?, monday_breakout_down_percent = ?,
                monday_trend_detail = ?, tuesday_trend_detail = ?,
                wednesday_trend_detail = ?, thursday_trend_detail = ?,
                friday_trend_detail = ?, saturday_trend_detail = ?,
                sunday_trend_detail = ?,
                tuesday_breakout_up_percent = ?, tuesday_breakout_down_percent = ?,
                wednesday_breakout_up_percent = ?, wednesday_breakout_down_percent = ?,
                thursday_breakout_up_percent = ?, thursday_breakout_down_percent = ?,
                friday_breakout_up_percent = ?, friday_breakout_down_percent = ?,
                saturday_breakout_up_percent = ?, saturday_breakout_down_percent = ?,
                sunday_breakout_up_percent = ?, sunday_breakout_down_percent = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data['pattern'], data['monday_id'], data['tuesday_id'], data['wednesday_id'],
            data['thursday_id'], data['friday_id'], data['saturday_id'], data['sunday_id'],
            data['previous_sunday_id'], data['monday_high'], data['monday_low'],
            data['previous_sunday_high'], data['previous_sunday_low'],
            data['monday_is_breakout_up'], data['monday_is_breakout_down'],
            data['monday_breakout_up_percent'], data['monday_breakout_down_percent'],
            data['monday_trend_detail'], data['tuesday_trend_detail'],
            data['wednesday_trend_detail'], data['thursday_trend_detail'],
            data['friday_trend_detail'], data['saturday_trend_detail'],
            data['sunday_trend_detail'],
            data.get('tuesday_breakout_up_percent'), data.get('tuesday_breakout_down_percent'),
            data.get('wednesday_breakout_up_percent'), data.get('wednesday_breakout_down_percent'),
            data.get('thursday_breakout_up_percent'), data.get('thursday_breakout_down_percent'),
            data.get('friday_breakout_up_percent'), data.get('friday_breakout_down_percent'),
            data.get('saturday_breakout_up_percent'), data.get('saturday_breakout_down_percent'),
            data.get('sunday_breakout_up_percent'), data.get('sunday_breakout_down_percent'),
            existing[0]
        ))
    else:
        # 插入新记录
        cursor.execute("""
            INSERT INTO weekly_patterns
            (symbol_id, week_start, week_end, year, month, week_of_year,
             pattern, monday_id, tuesday_id, wednesday_id, thursday_id,
             friday_id, saturday_id, sunday_id, previous_sunday_id,
             monday_high, monday_low, previous_sunday_high, previous_sunday_low,
             monday_is_breakout_up, monday_is_breakout_down,
             monday_breakout_up_percent, monday_breakout_down_percent,
             monday_trend_detail, tuesday_trend_detail, wednesday_trend_detail,
             thursday_trend_detail, friday_trend_detail, saturday_trend_detail,
             sunday_trend_detail,
             tuesday_breakout_up_percent, tuesday_breakout_down_percent,
             wednesday_breakout_up_percent, wednesday_breakout_down_percent,
             thursday_breakout_up_percent, thursday_breakout_down_percent,
             friday_breakout_up_percent, friday_breakout_down_percent,
             saturday_breakout_up_percent, saturday_breakout_down_percent,
             sunday_breakout_up_percent, sunday_breakout_down_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['symbol_id'],
            data['week_start'].strftime('%Y-%m-%d %H:%M:%S'),
            data['week_end'].strftime('%Y-%m-%d %H:%M:%S'),
            data['year'], data['month'], data['week_of_year'],
            data['pattern'], data['monday_id'], data['tuesday_id'], data['wednesday_id'],
            data['thursday_id'], data['friday_id'], data['saturday_id'], data['sunday_id'],
            data['previous_sunday_id'],
            data['monday_high'], data['monday_low'],
            data['previous_sunday_high'], data['previous_sunday_low'],
            data['monday_is_breakout_up'], data['monday_is_breakout_down'],
            data['monday_breakout_up_percent'], data['monday_breakout_down_percent'],
            data['monday_trend_detail'], data['tuesday_trend_detail'],
            data['wednesday_trend_detail'], data['thursday_trend_detail'],
            data['friday_trend_detail'], data['saturday_trend_detail'],
            data['sunday_trend_detail'],
            data.get('tuesday_breakout_up_percent'), data.get('tuesday_breakout_down_percent'),
            data.get('wednesday_breakout_up_percent'), data.get('wednesday_breakout_down_percent'),
            data.get('thursday_breakout_up_percent'), data.get('thursday_breakout_down_percent'),
            data.get('friday_breakout_up_percent'), data.get('friday_breakout_down_percent'),
            data.get('saturday_breakout_up_percent'), data.get('saturday_breakout_down_percent'),
            data.get('sunday_breakout_up_percent'), data.get('sunday_breakout_down_percent')
        ))
    
    conn.commit()
    return data


def calculate_all_weekly_patterns(conn):
    """计算所有交易对的所有周模式"""
    cursor = conn.cursor()
    
    # 获取所有交易对
    cursor.execute("SELECT id, symbol FROM symbols WHERE is_active = 1")
    symbols = cursor.fetchall()
    
    for symbol_id, symbol_name in symbols:
        print(f"\n处理交易对: {symbol_name}")
        print("-" * 40)
        
        # 获取所有周一日期
        mondays = get_week_mondays(conn, symbol_id)
        
        pattern_count = {'XAMDXAM': 0, 'AMDXAMD': 0}
        
        for i, monday_date_str in enumerate(mondays):
            if (i + 1) % 50 == 0:
                print(f"  处理进度: {i + 1}/{len(mondays)} ({(i + 1) * 100 // len(mondays)}%)")
            
            result = calculate_pattern_for_week(symbol_id, monday_date_str, conn)
            
            if result:
                pattern = result['pattern']
                pattern_count[pattern] += 1
        
        total = sum(pattern_count.values())
        if total > 0:
            print(f"\n  统计: XAMDXAM={pattern_count['XAMDXAM']} ({pattern_count['XAMDXAM']*100/total:.1f}%), "
                  f"AMDXAMD={pattern_count['AMDXAMD']} ({pattern_count['AMDXAMD']*100/total:.1f}%)")


def main():
    """主函数"""
    print("=" * 60)
    print("周度模式计算程序")
    print("=" * 60)
    print(f"当前时间: {datetime.now(TZ_UTC9).strftime('%Y-%m-%d %H:%M:%S')} (UTC+9)")
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        calculate_all_weekly_patterns(conn)
        
        print("\n" + "=" * 60)
        print("周度模式计算完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()

