import pandas as pd
import json
from collections import defaultdict

def analyze_rules():
    """分析规则信息，提取rule_id、rule_type、rule_name的映射关系"""
    print("=== 规则分析 ===")
    
    # 从tmp.xls中提取规则信息（实际上tmp.xls已经包含了完整信息）
    df = pd.read_excel('tmp.xls')
    
    # 提取唯一的规则信息
    rule_info = df[['rule_id', 'rule_name', 'rule_type']].drop_duplicates()
    print("唯一规则信息:")
    print(rule_info)
    
    # 创建规则映射字典
    rule_mapping = {}
    for _, row in rule_info.iterrows():
        rule_mapping[row['rule_id']] = {
            'rule_name': row['rule_name'],
            'rule_type': row['rule_type']
        }
    
    print(f"\n规则映射字典:")
    for rule_id, info in rule_mapping.items():
        print(f"Rule {rule_id}: {info['rule_name']} ({info['rule_type']})")
    
    return rule_mapping

def analyze_feedback_by_rule():
    """按规则分析反馈数据"""
    print("\n=== 按规则分析反馈数据 ===")
    
    df = pd.read_excel('业务反馈结果.xls')
    
    # 按rule_id和status统计
    rule_status_stats = df.groupby(['rule_id', 'status']).size().unstack(fill_value=0)
    print("按规则ID和状态统计:")
    print(rule_status_stats)
    
    # 计算每个规则的状态=2（用户拒绝）的比例
    rule_stats = df.groupby('rule_id').agg({
        'status': ['count', lambda x: sum(x == 2)]
    }).round(2)
    rule_stats.columns = ['total_count', 'rejected_count']
    rule_stats['rejection_rate'] = (rule_stats['rejected_count'] / rule_stats['total_count'] * 100).round(2)
    
    print(f"\n各规则拒绝率统计:")
    print(rule_stats)
    
    return df

if __name__ == '__main__':
    rule_mapping = analyze_rules()
    feedback_df = analyze_feedback_by_rule() 