#!/usr/bin/env python3
"""
Bitstamp 数据获取模块
获取 BTCUSD 现货数据
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TZ_UTC9, DATABASE_PATH, API_REQUEST_INTERVAL

# Bitstamp API 配置
BITSTAMP_API_BASE = 'https://www.bitstamp.net/api/v2'
BITSTAMP_OHLC_ENDPOINT = '/ohlc/{pair}/'

# OHLC 参数
STEP_1HOUR = 3600  # 1小时（秒）
MAX_LIMIT = 1000   # 每次最多获取1000条数据


class BitstampDataFetcher:
    """Bitstamp 数据获取器"""
    
    def __init__(self, pair='btcusd'):
        """
        初始化
        
        Args:
            pair: 交易对，如 'btcusd'
        """
        self.pair = pair.lower()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_ohlc(self, step=STEP_1HOUR, limit=MAX_LIMIT, start=None, end=None):
        """
        获取 OHLC 数据
        
        Args:
            step: 时间间隔（秒），3600=1小时
            limit: 返回数据条数，最多1000
            start: 开始时间戳（Unix时间戳，秒）
            end: 结束时间戳（Unix时间戳，秒）
        
        Returns:
            dict: API响应数据
        """
        url = BITSTAMP_API_BASE + BITSTAMP_OHLC_ENDPOINT.format(pair=self.pair)
        
        params = {
            'step': step,
            'limit': limit
        }
        
        if start:
            params['start'] = int(start)
        if end:
            params['end'] = int(end)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API 请求失败: {e}")
            return None
    
    def fetch_historical_data(self, start_date, end_date=None):
        """
        批量获取历史数据
        
        Args:
            start_date: 开始日期 (datetime对象)
            end_date: 结束日期 (datetime对象)，默认为当前时间
        
        Returns:
            list: OHLC数据列表
        """
        if end_date is None:
            end_date = datetime.now(TZ_UTC9)
        
        all_data = []
        current_end = end_date
        
        print(f"开始获取 {self.pair.upper()} 历史数据...")
        print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        batch_count = 0
        while current_end > start_date:
            batch_count += 1
            
            # 计算当前批次的开始时间（往前推1000小时）
            current_start = current_end - timedelta(hours=MAX_LIMIT)
            
            # 转换为Unix时间戳
            start_ts = int(current_start.timestamp())
            end_ts = int(current_end.timestamp())
            
            print(f"\n批次 {batch_count}: {current_start.strftime('%Y-%m-%d %H:%M')} 至 {current_end.strftime('%Y-%m-%d %H:%M')}")
            
            # 获取数据
            data = self.fetch_ohlc(step=STEP_1HOUR, limit=MAX_LIMIT, start=start_ts, end=end_ts)
            
            if data and 'data' in data and 'ohlc' in data['data']:
                ohlc_data = data['data']['ohlc']
                print(f"  获取到 {len(ohlc_data)} 条数据")
                all_data.extend(ohlc_data)
            else:
                print(f"  未获取到数据")
                break
            
            # 更新下一批次的结束时间
            current_end = current_start
            
            # 如果已经到达起始日期，退出
            if current_end <= start_date:
                break
            
            # 延时，避免API限流
            time.sleep(API_REQUEST_INTERVAL)
        
        print(f"\n总共获取 {len(all_data)} 条数据")
        return all_data
    
    def parse_ohlc_data(self, ohlc_data):
        """
        解析 OHLC 数据为标准格式
        
        Args:
            ohlc_data: Bitstamp OHLC 数据
        
        Returns:
            list: 标准格式的数据列表
        """
        parsed_data = []
        
        for candle in ohlc_data:
            try:
                # Bitstamp OHLC 数据格式:
                # {
                #   "high": "string",
                #   "timestamp": "string",
                #   "volume": "string",
                #   "low": "string",
                #   "close": "string",
                #   "open": "string"
                # }
                
                timestamp = int(candle['timestamp'])
                dt = datetime.fromtimestamp(timestamp, tz=TZ_UTC9)
                
                parsed_data.append({
                    'timestamp': timestamp,
                    'datetime': dt,
                    'open': float(candle['open']),
                    'high': float(candle['high']),
                    'low': float(candle['low']),
                    'close': float(candle['close']),
                    'volume': float(candle['volume'])
                })
            except (KeyError, ValueError) as e:
                print(f"解析数据失败: {e}, 数据: {candle}")
                continue
        
        return parsed_data
    
    def save_to_database(self, parsed_data, symbol_name='BTCUSD'):
        """
        保存数据到数据库
        
        Args:
            parsed_data: 解析后的数据
            symbol_name: 交易对名称
        """
        if not parsed_data:
            print("没有数据需要保存")
            return
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 确保交易对存在
        cursor.execute("""
            INSERT OR IGNORE INTO symbols (symbol, display_name, exchange, is_active)
            VALUES (?, ?, ?, ?)
        """, (symbol_name, f'{symbol_name} 现货', 'bitstamp', 1))
        
        # 获取symbol_id
        cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol_name,))
        symbol_id = cursor.fetchone()[0]
        
        # 插入小时数据（用于计算周数据）
        inserted_count = 0
        updated_count = 0
        
        for data in parsed_data:
            # 检查是否已存在
            cursor.execute("""
                SELECT id FROM hourly_data 
                WHERE symbol_id = ? AND timestamp = ?
            """, (symbol_id, data['timestamp']))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有数据
                cursor.execute("""
                    UPDATE hourly_data 
                    SET open = ?, high = ?, low = ?, close = ?, volume = ?
                    WHERE id = ?
                """, (data['open'], data['high'], data['low'], data['close'], 
                      data['volume'], existing[0]))
                updated_count += 1
            else:
                # 插入新数据
                cursor.execute("""
                    INSERT INTO hourly_data 
                    (symbol_id, timestamp, datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol_id, data['timestamp'], data['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                      data['open'], data['high'], data['low'], data['close'], data['volume']))
                inserted_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n数据保存完成:")
        print(f"  新增: {inserted_count} 条")
        print(f"  更新: {updated_count} 条")


def main(force_update=False):
    """主函数"""
    print("=" * 60)
    print("Bitstamp 数据获取")
    print("=" * 60)
    
    # 初始化数据获取器
    fetcher = BitstampDataFetcher(pair='btcusd')
    
    # 确定获取数据的时间范围
    if force_update:
        # 从2011年开始（Bitstamp成立时间）
        start_date = datetime(2011, 9, 1, tzinfo=TZ_UTC9)
    else:
        # 增量更新：从数据库最后一条数据开始
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(timestamp) FROM hourly_data 
            WHERE symbol_id = (SELECT id FROM symbols WHERE symbol = 'BTCUSD')
        """)
        last_timestamp = cursor.fetchone()[0]
        conn.close()
        
        if last_timestamp:
            start_date = datetime.fromtimestamp(last_timestamp, tz=TZ_UTC9)
            print(f"增量更新，从 {start_date.strftime('%Y-%m-%d %H:%M')} 开始")
        else:
            start_date = datetime(2011, 9, 1, tzinfo=TZ_UTC9)
            print("首次获取，从2011年开始")
    
    # 获取数据
    ohlc_data = fetcher.fetch_historical_data(start_date)
    
    if not ohlc_data:
        print("未获取到数据")
        return False
    
    # 解析数据
    parsed_data = fetcher.parse_ohlc_data(ohlc_data)
    
    # 保存到数据库
    fetcher.save_to_database(parsed_data, symbol_name='BTCUSD')
    
    print("\n" + "=" * 60)
    print("Bitstamp 数据获取完成")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='获取 Bitstamp 数据')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新获取所有数据')
    args = parser.parse_args()
    
    success = main(force_update=args.force)
    sys.exit(0 if success else 1)

