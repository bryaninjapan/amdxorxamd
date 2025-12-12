#!/usr/bin/env python3
"""
回测引擎
模拟基于AMDX/XAMD和周度模式的交易策略
"""

import os
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TZ_UTC9, DATABASE_PATH


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, symbol_name, initial_capital=10000):
        """
        初始化回测引擎
        
        Args:
            symbol_name: 交易对名称
            initial_capital: 初始资金
        """
        self.symbol_name = symbol_name
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # 持仓（正数=多头，负数=空头）
        self.trades = []
        self.equity_curve = []
        
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
        
        # 获取symbol_id
        self.cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol_name,))
        result = self.cursor.fetchone()
        if not result:
            raise ValueError(f"交易对 {symbol_name} 不存在")
        self.symbol_id = result[0]
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def get_monthly_patterns(self):
        """获取月度模式数据"""
        self.cursor.execute("""
            SELECT 
                mp.year, mp.month, mp.pattern,
                mp.first_week_high, mp.first_week_low,
                mp.previous_week_high, mp.previous_week_low,
                wd.week_close
            FROM monthly_patterns mp
            JOIN weekly_data wd ON mp.first_week_id = wd.id
            WHERE mp.symbol_id = ?
            ORDER BY mp.year, mp.month
        """, (self.symbol_id,))
        
        return self.cursor.fetchall()
    
    def get_weekly_patterns(self):
        """获取周度模式数据"""
        self.cursor.execute("""
            SELECT 
                wp.year, wp.month, wp.week_of_year, wp.pattern,
                wp.monday_high, wp.monday_low,
                wp.previous_sunday_high, wp.previous_sunday_low,
                wd.week_close
            FROM weekly_patterns wp
            JOIN weekly_data wd ON wd.symbol_id = wp.symbol_id 
                AND wd.week_start = wp.week_start
            WHERE wp.symbol_id = ?
            ORDER BY wp.year, wp.week_of_year
        """, (self.symbol_id,))
        
        return self.cursor.fetchall()
    
    def open_position(self, direction, price, size, date, reason):
        """
        开仓
        
        Args:
            direction: 'long' 或 'short'
            price: 开仓价格
            size: 仓位大小（资金比例，0-1）
            date: 日期
            reason: 开仓原因
        """
        if self.position != 0:
            # 已有持仓，先平仓
            self.close_position(price, date, "强制平仓（新信号）")
        
        position_value = self.capital * size
        self.position = position_value / price if direction == 'long' else -(position_value / price)
        
        self.trades.append({
            'type': 'open',
            'direction': direction,
            'price': price,
            'size': abs(self.position),
            'value': position_value,
            'date': date,
            'reason': reason,
            'capital': self.capital
        })
    
    def close_position(self, price, date, reason):
        """
        平仓
        
        Args:
            price: 平仓价格
            date: 日期
            reason: 平仓原因
        """
        if self.position == 0:
            return
        
        # 计算盈亏
        if self.position > 0:  # 多头
            pnl = self.position * price - (self.position * self.trades[-1]['price'])
        else:  # 空头
            pnl = abs(self.position) * self.trades[-1]['price'] - (abs(self.position) * price)
        
        self.capital += pnl
        pnl_percent = (pnl / self.trades[-1]['value']) * 100
        
        self.trades.append({
            'type': 'close',
            'direction': 'long' if self.position > 0 else 'short',
            'price': price,
            'size': abs(self.position),
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'date': date,
            'reason': reason,
            'capital': self.capital
        })
        
        self.position = 0
    
    def update_equity(self, price, date):
        """更新权益曲线"""
        if self.position != 0:
            if self.position > 0:  # 多头
                unrealized_pnl = self.position * price - (self.position * self.trades[-1]['price'])
            else:  # 空头
                unrealized_pnl = abs(self.position) * self.trades[-1]['price'] - (abs(self.position) * price)
            current_equity = self.capital + unrealized_pnl
        else:
            current_equity = self.capital
        
        self.equity_curve.append({
            'date': date,
            'equity': current_equity,
            'position': self.position
        })
    
    def calculate_metrics(self):
        """计算回测指标"""
        if not self.trades:
            return None
        
        # 提取所有平仓交易
        closed_trades = [t for t in self.trades if t['type'] == 'close']
        
        if not closed_trades:
            return None
        
        # 总收益
        total_return = self.capital - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100
        
        # 交易次数
        num_trades = len(closed_trades)
        
        # 盈利交易
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / num_trades * 100) if num_trades > 0 else 0
        
        # 平均盈亏
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # 盈亏比
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 最大回撤
        peak = self.initial_capital
        max_drawdown = 0
        max_drawdown_percent = 0
        
        for point in self.equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            drawdown = peak - point['equity']
            drawdown_percent = (drawdown / peak * 100) if peak > 0 else 0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_percent = drawdown_percent
        
        # 夏普比率（简化版，假设无风险利率为0）
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                ret = (self.equity_curve[i]['equity'] - self.equity_curve[i-1]['equity']) / self.equity_curve[i-1]['equity']
                returns.append(ret)
            
            import numpy as np
            if returns and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # 年化
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return': total_return,
            'total_return_percent': round(total_return_percent, 2),
            'num_trades': num_trades,
            'num_winning': len(winning_trades),
            'num_losing': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_percent': round(max_drawdown_percent, 2),
            'sharpe_ratio': round(sharpe_ratio, 2)
        }


class Strategy:
    """交易策略基类"""
    
    def __init__(self, name):
        self.name = name
    
    def generate_signals(self, data):
        """
        生成交易信号
        
        Args:
            data: 历史数据
        
        Returns:
            list: 交易信号列表
        """
        raise NotImplementedError


class SimpleFollowStrategy(Strategy):
    """简单跟随策略：识别到特定模式就做多/做空"""
    
    def __init__(self):
        super().__init__("简单跟随策略")
    
    def generate_signals(self, monthly_patterns):
        """
        基于月度模式生成信号
        XAMD -> 做多
        AMDX -> 做空
        """
        signals = []
        
        for i, pattern_data in enumerate(monthly_patterns):
            year, month, pattern, first_high, first_low, prev_high, prev_low, close_price = pattern_data
            
            if pattern == 'XAMD':
                # 向上突破，做多
                signals.append({
                    'date': f"{year}-{month:02d}",
                    'action': 'long',
                    'price': close_price,
                    'size': 0.5,  # 50%仓位
                    'reason': f'XAMD模式 - 向上突破'
                })
            elif pattern == 'AMDX':
                # 向下突破，做空
                signals.append({
                    'date': f"{year}-{month:02d}",
                    'action': 'short',
                    'price': close_price,
                    'size': 0.5,
                    'reason': f'AMDX模式 - 向下突破'
                })
        
        return signals


class ReversalStrategy(Strategy):
    """反转策略：基于历史统计，某模式出现后预期反转"""
    
    def __init__(self):
        super().__init__("反转策略")
    
    def generate_signals(self, monthly_patterns):
        """
        基于模式反转生成信号
        XAMD后可能反转 -> 做空
        AMDX后可能反转 -> 做多
        """
        signals = []
        
        for i, pattern_data in enumerate(monthly_patterns):
            if i == 0:
                continue  # 跳过第一个，因为需要看前一个模式
            
            year, month, pattern, first_high, first_low, prev_high, prev_low, close_price = pattern_data
            prev_pattern = monthly_patterns[i-1][2]
            
            if prev_pattern == 'XAMD':
                # 上个月向上突破，这个月可能反转，做空
                signals.append({
                    'date': f"{year}-{month:02d}",
                    'action': 'short',
                    'price': close_price,
                    'size': 0.3,  # 30%仓位（反转策略风险较高）
                    'reason': f'反转策略 - 前月XAMD'
                })
            elif prev_pattern == 'AMDX':
                # 上个月向下突破，这个月可能反转，做多
                signals.append({
                    'date': f"{year}-{month:02d}",
                    'action': 'long',
                    'price': close_price,
                    'size': 0.3,
                    'reason': f'反转策略 - 前月AMDX'
                })
        
        return signals


class MultiTimeframeStrategy(Strategy):
    """多周期结合策略：同时考虑月度和周度模式"""
    
    def __init__(self):
        super().__init__("多周期结合策略")
    
    def generate_signals(self, monthly_patterns, weekly_patterns):
        """
        结合月度和周度模式生成信号
        两个信号同向 -> 加大仓位
        信号冲突 -> 减少仓位或观望
        """
        signals = []
        
        # 创建月度模式字典
        monthly_dict = {}
        for pattern_data in monthly_patterns:
            year, month = pattern_data[0], pattern_data[1]
            monthly_dict[(year, month)] = pattern_data[2]
        
        # 遍历周度模式
        for week_data in weekly_patterns:
            year, month, week_of_year, pattern = week_data[0], week_data[1], week_data[2], week_data[3]
            close_price = week_data[8]
            
            # 获取对应的月度模式
            monthly_pattern = monthly_dict.get((year, month))
            
            if not monthly_pattern:
                continue
            
            # 判断信号方向
            monthly_signal = 'long' if monthly_pattern == 'XAMD' else 'short'
            weekly_signal = 'long' if pattern == 'XAMDXAM' else 'short'
            
            if monthly_signal == weekly_signal:
                # 两个信号同向，加大仓位
                signals.append({
                    'date': f"{year}-{month:02d}-W{week_of_year}",
                    'action': monthly_signal,
                    'price': close_price,
                    'size': 0.7,  # 70%仓位
                    'reason': f'多周期同向 - 月度:{monthly_pattern}, 周度:{pattern}'
                })
            else:
                # 信号冲突，小仓位或观望
                signals.append({
                    'date': f"{year}-{month:02d}-W{week_of_year}",
                    'action': monthly_signal,  # 以月度信号为主
                    'price': close_price,
                    'size': 0.2,  # 20%仓位
                    'reason': f'多周期冲突 - 月度:{monthly_pattern}, 周度:{pattern}'
                })
        
        return signals


def main():
    """主函数"""
    print("=" * 60)
    print("回测引擎测试")
    print("=" * 60)
    
    # 这里只是框架测试，实际回测在 backtest_reports.py 中执行
    print("\n回测引擎框架已创建")
    print("包含以下策略：")
    print("  1. 简单跟随策略")
    print("  2. 反转策略")
    print("  3. 多周期结合策略")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

