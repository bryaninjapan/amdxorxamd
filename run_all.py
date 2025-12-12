#!/usr/bin/env python3
"""
AMDX/XAMD 模式分析系统 - 一键运行脚本
运行所有步骤：初始化数据库 -> 获取数据 -> 计算模式 -> 生成报告
"""

import os
import sys
import argparse
from datetime import datetime

# 确保当前目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TZ_UTC9, DATABASE_PATH


def run_step(step_name, module_name, function_name='main', *args, **kwargs):
    """运行指定步骤"""
    print(f"\n{'=' * 60}")
    print(f"步骤: {step_name}")
    print('=' * 60)
    
    try:
        module = __import__(f'scripts.{module_name}', fromlist=[function_name])
        func = getattr(module, function_name)
        func(*args, **kwargs)
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AMDX/XAMD 模式分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_all.py           # 运行所有步骤（增量更新）
  python run_all.py --force   # 强制重新获取所有数据
  python run_all.py --report  # 只生成报告
  python run_all.py --init    # 只初始化数据库
        """
    )
    
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制重新获取所有数据')
    parser.add_argument('--report', '-r', action='store_true',
                        help='只生成报告（跳过数据获取）')
    parser.add_argument('--init', '-i', action='store_true',
                        help='只初始化数据库')
    parser.add_argument('--fetch', action='store_true',
                        help='只获取数据')
    parser.add_argument('--calculate', '-c', action='store_true',
                        help='只计算模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AMDX/XAMD 模式分析系统")
    print("=" * 60)
    print(f"当前时间: {datetime.now(TZ_UTC9).strftime('%Y-%m-%d %H:%M:%S')} (UTC+9)")
    print(f"数据库: {DATABASE_PATH}")
    
    # 根据参数决定运行哪些步骤
    run_init = args.init or (not args.report and not args.fetch and not args.calculate)
    run_fetch = args.fetch or (not args.init and not args.report and not args.calculate)
    run_calc = args.calculate or (not args.init and not args.report and not args.fetch)
    run_report = args.report or (not args.init and not args.fetch and not args.calculate)
    
    success = True
    
    # 步骤1: 初始化数据库
    if run_init:
        if not run_step("初始化数据库", "init_database", "init_database"):
            print("\n初始化数据库失败，停止执行")
            return 1
    
    if args.init:
        print("\n数据库初始化完成!")
        return 0
    
    # 步骤2: 获取数据
    if run_fetch:
        if not run_step("获取Binance数据", "fetch_data", "main", force_update=args.force):
            print("\n数据获取失败，继续执行...")
            success = False
    
    if args.fetch:
        return 0 if success else 1
    
    # 步骤3: 计算模式
    if run_calc:
        if not run_step("计算AMDX/XAMD模式", "calculate_patterns", "main"):
            print("\n模式计算失败，继续执行...")
            success = False
    
    if args.calculate:
        return 0 if success else 1
    
    # 步骤4: 生成报告
    if run_report:
        if not run_step("生成分析报告", "generate_reports", "main"):
            print("\n报告生成失败")
            success = False
    
    # 完成
    print("\n" + "=" * 60)
    if success:
        print("所有步骤执行完成!")
    else:
        print("部分步骤执行失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

