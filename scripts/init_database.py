"""
数据库初始化脚本
"""

import sqlite3
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH, DATABASE_DIR, SYMBOLS

def init_database():
    """初始化数据库"""
    print("=" * 50)
    print("AMDX/XAMD 数据库初始化")
    print("=" * 50)
    
    # 确保目录存在
    os.makedirs(DATABASE_DIR, exist_ok=True)
    
    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 读取并执行schema
    schema_path = os.path.join(DATABASE_DIR, 'schema.sql')
    
    if os.path.exists(schema_path):
        print(f"读取数据库结构: {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.executescript(schema_sql)
        print("✓ 数据库结构创建成功")
    else:
        print(f"错误: 找不到schema文件: {schema_path}")
        return False
    
    # 插入交易对配置
    print("\n初始化交易对配置...")
    for symbol_config in SYMBOLS:
        cursor.execute("""
            INSERT OR IGNORE INTO symbols (symbol, display_name, exchange)
            VALUES (?, ?, 'binance')
        """, (symbol_config['name'], symbol_config['display_name']))
        
        if cursor.rowcount > 0:
            print(f"  ✓ 添加交易对: {symbol_config['name']}")
        else:
            print(f"  - 交易对已存在: {symbol_config['name']}")
    
    conn.commit()
    
    # 验证表是否创建成功
    print("\n验证数据库表...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    expected_tables = ['data_quality_logs', 'monthly_patterns', 'symbols', 
                       'system_config', 'update_logs', 'weekly_data']
    
    created_tables = [t[0] for t in tables]
    
    for table in expected_tables:
        if table in created_tables:
            print(f"  ✓ 表 {table} 已创建")
        else:
            print(f"  ✗ 表 {table} 创建失败")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print(f"数据库初始化完成: {DATABASE_PATH}")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    init_database()

