#!/usr/bin/env python3
"""
模式预测模块
基于历史数据预测下一周/月的模式
"""

import os
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TZ_UTC9, DATABASE_PATH, SYMBOLS


class PatternPredictor:
    """模式预测器"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def predict_monthly_pattern(self, symbol_name):
        """
        预测下一个月的月度模式（AMDX/XAMD）
        
        Args:
            symbol_name: 交易对名称
        
        Returns:
            dict: 预测结果
        """
        # 获取symbol_id
        self.cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol_name,))
        result = self.cursor.fetchone()
        if not result:
            return None
        symbol_id = result[0]
        
        # 获取所有历史月度模式
        self.cursor.execute("""
            SELECT year, month, pattern 
            FROM monthly_patterns 
            WHERE symbol_id = ?
            ORDER BY year, month
        """, (symbol_id,))
        
        historical_patterns = self.cursor.fetchall()
        
        if len(historical_patterns) < 2:
            return {
                'symbol': symbol_name,
                'prediction': None,
                'confidence': 0,
                'method': 'insufficient_data',
                'message': '历史数据不足，无法预测'
            }
        
        # 方法1: 历史频率法
        pattern_counts = Counter([p[2] for p in historical_patterns])
        most_common_pattern = pattern_counts.most_common(1)[0][0]
        frequency_confidence = pattern_counts[most_common_pattern] / len(historical_patterns)
        
        # 方法2: 季节性分析（按月份统计）
        current_month = datetime.now(TZ_UTC9).month
        next_month = (current_month % 12) + 1
        
        monthly_patterns = defaultdict(Counter)
        for year, month, pattern in historical_patterns:
            monthly_patterns[month][pattern] += 1
        
        seasonal_prediction = None
        seasonal_confidence = 0
        if next_month in monthly_patterns:
            if monthly_patterns[next_month]:
                seasonal_pattern = monthly_patterns[next_month].most_common(1)[0]
                seasonal_prediction = seasonal_pattern[0]
                seasonal_confidence = seasonal_pattern[1] / sum(monthly_patterns[next_month].values())
        
        # 方法3: 连续模式识别（马尔可夫链）
        transitions = defaultdict(Counter)
        for i in range(len(historical_patterns) - 1):
            current_pattern = historical_patterns[i][2]
            next_pattern = historical_patterns[i + 1][2]
            transitions[current_pattern][next_pattern] += 1
        
        # 获取最近一个月的模式
        last_pattern = historical_patterns[-1][2]
        markov_prediction = None
        markov_confidence = 0
        if last_pattern in transitions and transitions[last_pattern]:
            markov_pattern = transitions[last_pattern].most_common(1)[0]
            markov_prediction = markov_pattern[0]
            markov_confidence = markov_pattern[1] / sum(transitions[last_pattern].values())
        
        # 综合预测（加权平均）
        predictions = []
        if seasonal_prediction:
            predictions.append((seasonal_prediction, seasonal_confidence * 0.4, 'seasonal'))
        if markov_prediction:
            predictions.append((markov_prediction, markov_confidence * 0.35, 'markov'))
        predictions.append((most_common_pattern, frequency_confidence * 0.25, 'frequency'))
        
        # 计算加权得分
        pattern_scores = defaultdict(float)
        for pattern, confidence, method in predictions:
            pattern_scores[pattern] += confidence
        
        final_prediction = max(pattern_scores.items(), key=lambda x: x[1])
        
        return {
            'symbol': symbol_name,
            'prediction': final_prediction[0],
            'confidence': round(final_prediction[1] * 100, 2),
            'next_month': next_month,
            'methods': {
                'frequency': {
                    'prediction': most_common_pattern,
                    'confidence': round(frequency_confidence * 100, 2),
                    'total_samples': len(historical_patterns)
                },
                'seasonal': {
                    'prediction': seasonal_prediction,
                    'confidence': round(seasonal_confidence * 100, 2) if seasonal_prediction else 0,
                    'month_samples': sum(monthly_patterns[next_month].values()) if next_month in monthly_patterns else 0
                },
                'markov': {
                    'prediction': markov_prediction,
                    'confidence': round(markov_confidence * 100, 2) if markov_prediction else 0,
                    'last_pattern': last_pattern
                }
            },
            'historical_distribution': dict(pattern_counts)
        }
    
    def predict_weekly_pattern(self, symbol_name):
        """
        预测下一周的周度模式（XAMDXAM/AMDXAMD）
        
        Args:
            symbol_name: 交易对名称
        
        Returns:
            dict: 预测结果
        """
        # 获取symbol_id
        self.cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol_name,))
        result = self.cursor.fetchone()
        if not result:
            return None
        symbol_id = result[0]
        
        # 获取所有历史周度模式
        self.cursor.execute("""
            SELECT year, month, week_of_year, pattern 
            FROM weekly_patterns 
            WHERE symbol_id = ?
            ORDER BY year, week_of_year
        """, (symbol_id,))
        
        historical_patterns = self.cursor.fetchall()
        
        if len(historical_patterns) < 2:
            return {
                'symbol': symbol_name,
                'prediction': None,
                'confidence': 0,
                'method': 'insufficient_data',
                'message': '历史数据不足，无法预测'
            }
        
        # 方法1: 历史频率法
        pattern_counts = Counter([p[3] for p in historical_patterns])
        most_common_pattern = pattern_counts.most_common(1)[0][0]
        frequency_confidence = pattern_counts[most_common_pattern] / len(historical_patterns)
        
        # 方法2: 连续模式识别
        transitions = defaultdict(Counter)
        for i in range(len(historical_patterns) - 1):
            current_pattern = historical_patterns[i][3]
            next_pattern = historical_patterns[i + 1][3]
            transitions[current_pattern][next_pattern] += 1
        
        last_pattern = historical_patterns[-1][3]
        markov_prediction = None
        markov_confidence = 0
        if last_pattern in transitions and transitions[last_pattern]:
            markov_pattern = transitions[last_pattern].most_common(1)[0]
            markov_prediction = markov_pattern[0]
            markov_confidence = markov_pattern[1] / sum(transitions[last_pattern].values())
        
        # 综合预测
        if markov_prediction:
            final_prediction = markov_prediction
            final_confidence = markov_confidence * 0.6 + frequency_confidence * 0.4
        else:
            final_prediction = most_common_pattern
            final_confidence = frequency_confidence
        
        return {
            'symbol': symbol_name,
            'prediction': final_prediction,
            'confidence': round(final_confidence * 100, 2),
            'methods': {
                'frequency': {
                    'prediction': most_common_pattern,
                    'confidence': round(frequency_confidence * 100, 2),
                    'total_samples': len(historical_patterns)
                },
                'markov': {
                    'prediction': markov_prediction,
                    'confidence': round(markov_confidence * 100, 2) if markov_prediction else 0,
                    'last_pattern': last_pattern
                }
            },
            'historical_distribution': dict(pattern_counts)
        }
    
    def calculate_historical_accuracy(self, symbol_name, pattern_type='monthly'):
        """
        计算历史预测准确率
        
        Args:
            symbol_name: 交易对名称
            pattern_type: 'monthly' 或 'weekly'
        
        Returns:
            dict: 准确率统计
        """
        # 获取symbol_id
        self.cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol_name,))
        result = self.cursor.fetchone()
        if not result:
            return None
        symbol_id = result[0]
        
        if pattern_type == 'monthly':
            table = 'monthly_patterns'
            order_by = 'year, month'
        else:
            table = 'weekly_patterns'
            order_by = 'year, week_of_year'
        
        # 获取历史数据
        self.cursor.execute(f"""
            SELECT pattern FROM {table}
            WHERE symbol_id = ?
            ORDER BY {order_by}
        """, (symbol_id,))
        
        patterns = [row[0] for row in self.cursor.fetchall()]
        
        if len(patterns) < 10:
            return {
                'accuracy': 0,
                'total_predictions': 0,
                'correct_predictions': 0,
                'message': '数据不足，无法计算准确率'
            }
        
        # 模拟历史预测
        correct = 0
        total = 0
        
        for i in range(10, len(patterns)):
            # 使用前i个数据预测第i+1个
            historical = patterns[:i]
            actual = patterns[i]
            
            # 简单预测：使用最常见的模式
            pattern_counts = Counter(historical)
            predicted = pattern_counts.most_common(1)[0][0]
            
            if predicted == actual:
                correct += 1
            total += 1
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return {
            'accuracy': round(accuracy, 2),
            'total_predictions': total,
            'correct_predictions': correct,
            'sample_size': len(patterns)
        }


def main():
    """主函数"""
    print("=" * 60)
    print("模式预测分析")
    print("=" * 60)
    
    predictor = PatternPredictor()
    
    for symbol_config in SYMBOLS:
        symbol_name = symbol_config['name']
        print(f"\n{'=' * 60}")
        print(f"交易对: {symbol_config['display_name']}")
        print('=' * 60)
        
        # 月度模式预测
        print("\n【月度模式预测】")
        monthly_pred = predictor.predict_monthly_pattern(symbol_name)
        if monthly_pred:
            if monthly_pred['prediction']:
                print(f"预测结果: {monthly_pred['prediction']}")
                print(f"置信度: {monthly_pred['confidence']}%")
                print(f"下个月份: {monthly_pred['next_month']}月")
                print(f"\n预测方法详情:")
                for method, data in monthly_pred['methods'].items():
                    print(f"  {method}: {data['prediction']} (置信度: {data['confidence']}%)")
                print(f"\n历史分布: {monthly_pred['historical_distribution']}")
            else:
                print(f"  {monthly_pred['message']}")
        
        # 周度模式预测
        print("\n【周度模式预测】")
        weekly_pred = predictor.predict_weekly_pattern(symbol_name)
        if weekly_pred:
            if weekly_pred['prediction']:
                print(f"预测结果: {weekly_pred['prediction']}")
                print(f"置信度: {weekly_pred['confidence']}%")
                print(f"\n预测方法详情:")
                for method, data in weekly_pred['methods'].items():
                    print(f"  {method}: {data['prediction']} (置信度: {data['confidence']}%)")
                print(f"\n历史分布: {weekly_pred['historical_distribution']}")
            else:
                print(f"  {weekly_pred['message']}")
        
        # 历史准确率
        print("\n【历史预测准确率】")
        monthly_acc = predictor.calculate_historical_accuracy(symbol_name, 'monthly')
        if monthly_acc:
            print(f"月度模式: {monthly_acc['accuracy']}% ({monthly_acc['correct_predictions']}/{monthly_acc['total_predictions']})")
        
        weekly_acc = predictor.calculate_historical_accuracy(symbol_name, 'weekly')
        if weekly_acc:
            print(f"周度模式: {weekly_acc['accuracy']}% ({weekly_acc['correct_predictions']}/{weekly_acc['total_predictions']})")
    
    print("\n" + "=" * 60)
    print("预测分析完成")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

