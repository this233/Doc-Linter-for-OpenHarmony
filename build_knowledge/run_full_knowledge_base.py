#!/usr/bin/env python3
"""
完整知识库构建运行脚本
根据数据量和系统资源调整参数
"""

from parallel_knowledge_builder import ParallelKnowledgeBaseBuilder
import time

def main():
    print("="*60)
    print("开发者文档编写助手 - 知识库构建系统")
    print("="*60)
    
    # 数据统计信息
    print("数据概览:")
    print("- 总数据量: 11,097 条反馈")
    print("- 规则数量: 9 个")
    print("- 各规则数据分布:")
    rule_counts = {
        3: 1207, 5: 608, 6: 210, 7: 2395, 8: 1147, 
        9: 158, 10: 243, 11: 1603, 12: 3526
    }
    for rule_id, count in rule_counts.items():
        print(f"  规则 {rule_id}: {count} 条")
    
    print("\n" + "="*60)
    print("配置选项:")
    
    # 配置参数
    max_workers = 25      # 并发线程数 (建议: 4-12)
    batch_size = 50      # 批处理大小 (建议: 20-100)
    
    print(f"- 并发线程数: {max_workers} (可调整: 4-12)")
    print(f"- 批处理大小: {batch_size} (可调整: 20-100)")
    print("- API重试次数: 3")
    print("- 中间结果保存: 启用")
    
    # 处理方案选择
    print("\n处理方案:")
    print("1. 测试方案: 处理规则7和8 (约3542条数据, 预计20-30分钟)")
    print("2. 完整方案: 处理所有9个规则 (全部11097条数据, 预计60-90分钟)")
    print("3. 自定义方案: 选择特定规则")
    
    choice = input("\n请选择处理方案 (1/2/3): ").strip()
    
    if choice == "1":
        rule_ids = [7, 8]
        print(f"选择测试方案，处理规则: {rule_ids}")
    elif choice == "2":
        rule_ids = [3, 5, 6, 7, 8, 9, 10, 11, 12]
        print(f"选择完整方案，处理所有规则: {rule_ids}")
    elif choice == "3":
        print("可选规则: 3, 5, 6, 7, 8, 9, 10, 11, 12")
        rule_input = input("请输入要处理的规则ID (用逗号分隔): ").strip()
        try:
            rule_ids = [int(x.strip()) for x in rule_input.split(",")]
            print(f"选择自定义方案，处理规则: {rule_ids}")
        except:
            print("输入格式错误，使用默认测试方案")
            rule_ids = [7, 8]
    else:
        print("无效选择，使用默认测试方案")
        rule_ids = [7, 8]
    
    # 确认开始
    total_data = sum(rule_counts.get(rule_id, 0) for rule_id in rule_ids)
    estimated_time = total_data * 2 / 60  # 粗略估算：每条数据2秒
    
    print(f"\n预计处理 {total_data} 条数据，估算时间: {estimated_time:.1f} 分钟")
    
    confirm = input("\n确认开始构建知识库? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消构建")
        return
    
    # 开始构建
    print("\n" + "="*60)
    print("开始构建知识库...")
    print("="*60)
    
    start_time = time.time()
    
    try:
        # 创建并行构建器
        builder = ParallelKnowledgeBaseBuilder(max_workers=max_workers)
        
        # 构建知识库
        complete_kb = builder.build_complete_knowledge_base(
            rule_ids=rule_ids,
            batch_size=batch_size
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "="*60)
        print("构建完成!")
        print(f"总耗时: {elapsed_time/60:.1f} 分钟")
        
        # 统计结果
        total_positive = sum(len(kb.get("正面示例", [])) for kb in complete_kb.values())
        total_negative = sum(len(kb.get("反面示例", [])) for kb in complete_kb.values())
        
        print(f"生成正面示例: {total_positive} 个")
        print(f"生成反面示例: {total_negative} 个")
        print(f"总有效案例: {total_positive + total_negative} 个")
        
        print("\n输出文件:")
        print("- complete_knowledge_base.json (完整知识库)")
        for rule_id in rule_ids:
            print(f"- knowledge_base_rule_{rule_id}_complete.json")
        print("- intermediate_results/ (中间结果目录)")
        
    except KeyboardInterrupt:
        print("\n用户中断，已保存中间结果")
    except Exception as e:
        print(f"\n构建过程中出错: {e}")
        print("请检查中间结果目录 intermediate_results/")

if __name__ == "__main__":
    main() 