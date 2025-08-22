#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补丁脚本：向正面示例添加reason字段并重命名为"用户拒绝的建议"
"""

import pandas as pd
import json
import glob
import os
from typing import Dict, Any

def load_reason_mapping(excel_path: str) -> Dict[int, str]:
    """
    从Excel文件中加载defect_id到reason的映射
    
    Args:
        excel_path: Excel文件路径
        
    Returns:
        defect_id到reason的映射字典
    """
    print(f"正在读取Excel文件: {excel_path}")
    df = pd.read_excel(excel_path)
    
    # 创建映射字典
    reason_mapping = {}
    for _, row in df.iterrows():
        defect_id = row['defect_id']
        defect_id = str(defect_id)
        reason = row['reason']
        if pd.notna(reason):
            reason_mapping[defect_id] = reason
    
    print(f"成功加载 {len(reason_mapping)} 条reason映射")
    return reason_mapping

def update_knowledge_base_file(file_path: str, reason_mapping: Dict[int, str]) -> bool:
    """
    更新单个knowledge_base文件
    
    Args:
        file_path: 文件路径
        reason_mapping: defect_id到reason的映射
        
    Returns:
        是否成功更新
    """
    try:
        print(f"正在处理文件: {file_path}")
        
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            datas = json.load(f)
        
        rules = list(datas.keys())
        updated_count = 0
        for rule in rules:
            data = datas[rule]
            # 更新正面示例
            positive_examples = data.get('正面示例', [])
            
            
            for example in positive_examples:
                defect_id = example.get('defect_id')
                defect_id = str(defect_id)
                if defect_id and defect_id in reason_mapping:
                    # 添加"用户拒绝的建议"字段
                    example['用户拒绝的建议'] = reason_mapping[defect_id]
                    updated_count += 1
                else:
                    print(f"defect_id {defect_id} 不在reason_mapping中")
        
        # 保存更新后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(datas, f, ensure_ascii=False, indent=2)
        
        print(f"  - 更新了 {updated_count} 个正面示例")
        return True
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("开始执行补丁脚本：添加reason字段到正面示例")
    print("=" * 60)
    
    # 配置文件路径
    excel_path = "results/业务反馈结果.xls"
    knowledge_base_pattern = "results/knowledge_base_rule_*_complete.json"
    
    # 1. 加载reason映射
    try:
        reason_mapping = load_reason_mapping(excel_path)
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
    
    # 2. 找到所有需要更新的文件
    # kb_files = glob.glob(knowledge_base_pattern)
    # kb_files.sort()  # 按文件名排序

    kb_files = ["results/complete_knowledge_base.json"]
    
    print(f"\n找到 {len(kb_files)} 个knowledge_base文件需要更新:")
    for f in kb_files:
        print(f"  - {f}")
    
    # 3. 逐个更新文件
    print(f"\n开始更新文件...")
    success_count = 0
    total_updated = 0
    
    for kb_file in kb_files:
        if update_knowledge_base_file(kb_file, reason_mapping):
            success_count += 1
    
    # 4. 输出结果
    print("\n" + "=" * 60)
    print("补丁执行完成!")
    print(f"成功更新: {success_count}/{len(kb_files)} 个文件")
    
    if success_count == len(kb_files):
        print("✅ 所有文件更新成功!")
    else:
        print("⚠️  部分文件更新失败，请检查错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main() 