#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG API 测试客户端
演示如何使用RAG系统的网络接口
"""

import requests
import json
import time
from typing import Dict, Any

class RAGAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        RAG API客户端
        
        Args:
            base_url: API服务器的基础URL
        """
        self.base_url = base_url.rstrip('/')
        
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_rules(self) -> Dict[str, Any]:
        """获取可用的规则列表"""
        try:
            response = requests.get(f"{self.base_url}/rules")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def build_vector_db(self, json_path: str = "results/complete_knowledge_base.json") -> Dict[str, Any]:
        """构建向量数据库"""
        try:
            data = {"json_path": json_path}
            response = requests.post(f"{self.base_url}/build_db", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def load_vector_db(self, path: str = "vector_db") -> Dict[str, Any]:
        """加载向量数据库"""
        try:
            data = {"path": path}
            response = requests.post(f"{self.base_url}/load_db", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def save_vector_db(self, path: str = "vector_db") -> Dict[str, Any]:
        """保存向量数据库"""
        try:
            data = {"path": path}
            response = requests.post(f"{self.base_url}/save_db", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def retrieve(self, rule_id: str, query: str, top_k: int = 36) -> Dict[str, Any]:
        """执行RAG检索"""
        try:
            data = {
                "rule_id": rule_id,
                "query": query,
                "top_k": top_k
            }
            response = requests.post(f"{self.base_url}/retrieve", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

def print_json(data: Dict[str, Any], title: str = ""):
    """美化打印JSON数据"""
    if title:
        print(f"\n=== {title} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def test_api():
    """测试API功能"""
    client = RAGAPIClient()
    
    print("开始测试RAG API...")
    
    # 1. 健康检查
    print("\n1. 健康检查")
    health = client.health_check()
    print_json(health)
    
    if "error" in health:
        print("❌ API服务不可用，请确保服务器正在运行")
        return
    
    # 2. 获取根信息
    print("\n2. 获取API信息")
    try:
        response = requests.get(f"{client.base_url}/")
        print_json(response.json())
    except Exception as e:
        print(f"❌ 获取API信息失败: {e}")
    
    # 3. 检查向量数据库状态
    if not health.get("vector_db_loaded", False):
        print("\n3. 向量数据库未加载，尝试加载...")
        load_result = client.load_vector_db()
        print_json(load_result)
        
        if "error" in load_result:
            print("⚠️  向量数据库加载失败，可能需要先构建数据库")
            print("   使用以下命令构建数据库（需要有知识库JSON文件）：")
            print("   build_result = client.build_vector_db('path/to/knowledge_base.json')")
            return
    
    # 4. 获取可用规则
    print("\n4. 获取可用规则")
    rules = client.get_rules()
    print_json(rules)
    
    if "error" in rules:
        print("❌ 获取规则列表失败")
        return
    
    if not rules.get("rules"):
        print("⚠️  没有可用的规则")
        return
    
    # 5. 执行检索测试
    test_rule_id = rules["rules"][0]  # 使用第一个可用规则
    test_query = "开发者没有配置背板图"
    
    print(f"\n5. 执行检索测试")
    print(f"   规则ID: {test_rule_id}")
    print(f"   查询: {test_query}")
    
    start_time = time.time()
    result = client.retrieve(rule_id=test_rule_id, query=test_query, top_k=5)
    end_time = time.time()
    
    if "error" in result:
        print_json(result, "❌ 检索失败")
        return
    
    print(f"\n✅ 检索成功!")
    print(f"   处理时间: {end_time - start_time:.3f}秒")
    print(f"   服务器处理时间: {result.get('processing_time', 0):.3f}秒")
    print(f"   总结果数: {result.get('total_results', 0)}")
    print(f"   正面示例数: {len(result.get('positive', []))}")
    print(f"   反面示例数: {len(result.get('negative', []))}")
    
    # 显示检索结果概要
    print("\n6. 检索结果概要")
    
    print("\n正面示例 (用户拒绝的修改):")
    for i, example in enumerate(result.get("positive", [])[:3], 1):  # 只显示前3个
        print(f"  {i}. 相似度: {example['similarity']:.4f}")
        text_data = example['content_dict']
        print(f"     规则名称: {text_data.get('规则名称', 'N/A')}")
        print(f"     当前句子: {text_data.get('当前句子', 'N/A')[:50]}...")
        print(f"     用户拒绝的建议: {text_data.get('用户拒绝的建议', 'N/A')[:50]}...")
        print(text_data)
    
    print("\n反面示例 (用户接受的修改):")
    for i, example in enumerate(result.get("negative", [])[:3], 1):  # 只显示前3个
        print(f"  {i}. 相似度: {example['similarity']:.4f}")
        text_data = example['content_dict']
        print(f"     规则名称: {text_data.get('规则名称', 'N/A')}")
        print(f"     当前句子: {text_data.get('当前句子', 'N/A')[:50]}...")
        print(f"     用户接受的建议: {text_data.get('用户接受的建议', 'N/A')[:50]}...")
        print(text_data)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试RAG API")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务器URL")
    parser.add_argument("--rule-id", help="指定规则ID进行检索测试")
    parser.add_argument("--query", help="指定查询文本进行检索测试")
    parser.add_argument("--top-k", type=int, default=5, help="返回结果数量")
    
    args = parser.parse_args()
    
    client = RAGAPIClient(args.url)
    
    if args.rule_id and args.query:
        # 执行单次检索
        print(f"执行检索: 规则ID={args.rule_id}, 查询={args.query}")
        result = client.retrieve(args.rule_id, args.query, args.top_k)
        print_json(result, "检索结果")
    else:
        # 执行完整测试
        test_api()

if __name__ == "__main__":
    main() 