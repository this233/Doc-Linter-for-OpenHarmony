import pandas as pd
import json
import requests
from typing import Dict, List, Any, Tuple
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os

class ParallelKnowledgeBaseBuilder:
    def __init__(self, max_workers: int = 50):
        self.api_key = "siq3nBr8C75Pv89E0CQaKq4c3KTCpOREj8Umj8OMCM5ByKkBrHxm-IOPiLuFlEOjnU3HFE5Hv-sfLzShM8CCoA"
        self.url = "https://api.modelarts-maas.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.max_workers = max_workers
        self.lock = threading.Lock()
        
        # 规则映射
        self.rule_mapping = {
            7: {'rule_name': '语言表达一致性', 'rule_type': 'INCONSISTENT'},
            8: {'rule_name': '错别字、拼写错误、错漏字', 'rule_type': 'SPELLING_ERRORS'},
            3: {'rule_name': '语句通顺', 'rule_type': 'FLUENT_ETC'},
            5: {'rule_name': '模糊词', 'rule_type': 'FUZZWORDS'},
            6: {'rule_name': '标点符号误用', 'rule_type': 'PUNCTUATION'},
            10: {'rule_name': '重复词和空格', 'rule_type': 'REPEAT_BLANKS_AND_WORDS'},
            11: {'rule_name': '冗余表达', 'rule_type': 'REDUNDANT_EXPRESSION'},
            12: {'rule_name': '混合规则', 'rule_type': 'MIX_RULE'},
            9: {'rule_name': '口语化表达', 'rule_type': 'COLLOQUIAL_EXPRESSION'}
        }

    def call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """带重试机制的LLM API调用"""
        for attempt in range(max_retries):
            try:
                data = {
                    "model": "DeepSeek-R1",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的文档质量分析专家，擅长分析文档编写规则和用户反馈。"},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "temperature": 0.3
                }
                
                response = requests.post(self.url, headers=self.headers, data=json.dumps(data), verify=False, timeout=60*3)
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    print(f"API调用失败 (尝试 {attempt+1}/{max_retries}): {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                print(f"API调用异常 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return ""

    def judge_effectiveness(self, reason_feedback: str, fixed_sentence: str, problematic_sentence: str, reference_sentence: str = "", problem_context: str = "") -> bool:
        """判断用户拒绝理由是否有效"""
        if not reason_feedback:
            return False
            
        context_info = ""
        if reference_sentence:
            context_info += f"\n参考句子: {reference_sentence}"
        if problem_context:
            context_info += f"\n问题上下文: {problem_context}"
            
        prompt = f"""
请判断用户的反馈理由是否有效。

原始问题句子: {problematic_sentence}
LLM修复建议: {fixed_sentence}
用户拒绝理由: {reason_feedback}{context_info}

请判断用户的拒绝理由是否有效。考虑以下因素：
1. 用户是否指出了修复的具体问题（即使表达简单）
2. 用户的反馈是否包含有用信息（如指出错误、不合适等）
3. 反馈是否能帮助理解为什么LLM的修复不当
4. 即使是简短的反馈，只要有明确指向性就算有效

无效的反馈通常是：完全无关、纯粹的情绪发泄、没有任何具体指向的抱怨。
有效的反馈包括：指出具体错误、说明不合适的原因、提及上下文不符等。

请只回答：有效 或 无效
"""
        response = self.call_llm_with_retry(prompt)
        return "有效" in response

    def judge_typicality(self, problematic_sentence: str, fixed_sentence: str, reason: str, rule_name: str, reference_sentence: str = "", problem_context: str = "") -> bool:
        """判断案例是否典型"""
        context_info = ""
        if reference_sentence:
            context_info += f"\n参考句子: {reference_sentence}"
        if problem_context:
            context_info += f"\n问题上下文: {problem_context}"
            
        prompt = f"""
请判断这个案例是否是"{rule_name}"规则的典型案例。

问题句子: {problematic_sentence}
修复建议: {fixed_sentence}
修复理由: {reason}
规则类型: {rule_name}{context_info}

请考虑以下因素：
1. 这个案例是否清晰地展示了该规则的核心问题
2. 修复建议是否恰当且有代表性
3. 这个案例是否能帮助其他用户理解该规则
4. 是否具有教学价值和参考意义

请只回答：典型 或 不典型
"""
        response = self.call_llm_with_retry(prompt)
        return "不典型" not in response

    def extract_attention_points(self, row: Dict[str, Any]) -> str:
        """提取LLM修复时的注意事项"""
        context_info = ""
        if pd.notna(row.get('reference_sentence', '')):
            context_info += f"\n参考句子: {row['reference_sentence']}"
        if pd.notna(row.get('problem_context', '')):
            context_info += f"\n问题上下文: {row['problem_context']}"
            
        prompt = f"""
基于用户的反馈，请提取LLM在修复"{self.rule_mapping[row['rule_id']]['rule_name']}"规则时的注意事项。

问题句子: {row['problematic_sentence']}
LLM的修复: {row['fixed_sentence']}
用户拒绝理由: {row['reason_feedback']}
修复理由: {row['reason']}{context_info}

请分析用户拒绝的原因，总结LLM在修复这类问题时容易犯的错误和需要注意的地方。
请提供具体、可操作的注意事项，帮助LLM避免类似错误。

请以"注意事项："开头，提供1-2句简洁、明确的建议。
"""
        response = self.call_llm_with_retry(prompt)
        return response.replace("注意事项：", "").strip()

    def extract_trigger_conditions(self, row: Dict[str, Any]) -> str:
        """提取规则的触发条件"""
        context_info = ""
        if pd.notna(row.get('reference_sentence', '')):
            context_info += f"\n参考句子: {row['reference_sentence']}"
        if pd.notna(row.get('problem_context', '')):
            context_info += f"\n问题上下文: {row['problem_context']}"
            
        prompt = f"""
基于这个成功的修复案例，请提取"{self.rule_mapping[row['rule_id']]['rule_name']}"规则的触发条件。

问题句子: {row['problematic_sentence']}
修复建议: {row['fixed_sentence']}
修复理由: {row['reason']}{context_info}

请分析这个案例，总结什么情况下应该触发这个规则，以及如何识别需要修复的问题。
请提供具体的触发条件和识别模式。

请以"触发条件："开头，提供1-2句明确、简短的条件描述。
"""
        response = self.call_llm_with_retry(prompt)
        return response.replace("触发条件：", "").strip()

    def process_single_row(self, row_data: Tuple[int, pd.Series, int]) -> Tuple[str, Dict[str, Any]]:
        """处理单行数据"""
        idx, row, rule_id = row_data
        
        try:
            if row['status'] == 2:  # 用户拒绝
                if pd.notna(row['reason_feedback']):
                    # 判断用户理由是否有效
                    ref_sentence = row['reference_sentence'] if pd.notna(row['reference_sentence']) else ""
                    prob_context = row['problem_context'] if pd.notna(row['problem_context']) else ""
                    
                    if self.judge_effectiveness(row['reason_feedback'], row['fixed_sentence'], row['problematic_sentence'], ref_sentence, prob_context):
                        # 提取注意事项
                        attention_points = self.extract_attention_points(row)
                        
                        return ("positive", {
                            "defect_id": row['defect_id'],
                            "sentence": row['problematic_sentence'],
                            "reference_sentence": ref_sentence,
                            "line_num": row['problematic_line_num'],
                            "context": prob_context,
                            "用户拒绝的修改": row['fixed_sentence'],
                            "注意事项": attention_points
                        })
            else:  # 用户接受
                # 判断案例是否典型
                ref_sentence = row['reference_sentence'] if pd.notna(row['reference_sentence']) else ""
                prob_context = row['problem_context'] if pd.notna(row['problem_context']) else ""
                
                if self.judge_typicality(row['problematic_sentence'], row['fixed_sentence'], row['reason'], self.rule_mapping[rule_id]['rule_name'], ref_sentence, prob_context):
                    # 提取触发条件
                    trigger_conditions = self.extract_trigger_conditions(row)
                    
                    return ("negative", {
                        "defect_id": row['defect_id'],
                        "sentence": row['problematic_sentence'],
                        "reference_sentence": ref_sentence,
                        "line_num": row['problematic_line_num'],
                        "context": prob_context,
                        "修改建议": row['reason'],
                        "更改后示例": row['fixed_sentence'],
                        "触发条件": trigger_conditions
                    })
        except Exception as e:
            print(f"处理行 {idx} 时出错: {e}")
            
        return ("skip", None)

    def process_rule_parallel(self, df: pd.DataFrame, rule_id: int, batch_size: int = 100) -> Dict[str, Any]:
        """并行处理特定规则的反馈数据"""
        rule_data = df[df['rule_id'] == rule_id].copy()
        
        print(f"处理规则 {rule_id} ({self.rule_mapping[rule_id]['rule_name']})...")
        print(f"总计 {len(rule_data)} 条数据")
        
        positive_examples = []
        negative_examples = []
        
        # 准备数据
        tasks = [(idx, row, rule_id) for idx, row in rule_data.iterrows()]
        
        # 分批处理以控制内存使用
        for batch_start in range(0, len(tasks), batch_size):
            batch_tasks = tasks[batch_start:batch_start + batch_size]
            batch_positive = []
            batch_negative = []
            
            print(f"处理批次 {batch_start//batch_size + 1}/{(len(tasks)-1)//batch_size + 1}")
            
            print(f"origin positive: {len([task for task in batch_tasks if task[1]['status'] == 2])}")
            print(f"origin negative: {len([task for task in batch_tasks if task[1]['status'] != 2])}")

            # 并行处理当前批次
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交任务
                future_to_task = {executor.submit(self.process_single_row, task): task for task in batch_tasks}
                
                # 收集结果
                for future in tqdm(as_completed(future_to_task), total=len(batch_tasks), desc="Processing"):
                    try:
                        result_type, result_data = future.result()
                        if result_type == "positive" and result_data:
                            batch_positive.append(result_data)
                        elif result_type == "negative" and result_data:
                            batch_negative.append(result_data)
                    except Exception as e:
                        print(f"任务执行出错: {e}")
            
            # 添加到总结果
            positive_examples.extend(batch_positive)
            negative_examples.extend(batch_negative)
            
            # 保存中间结果
            self.save_intermediate_results(rule_id, batch_start//batch_size + 1, batch_positive, batch_negative)
            
            print(f"批次完成 - 正面示例: {len(batch_positive)}, 反面示例: {len(batch_negative)}")
        
        result = {
            "规则ID": rule_id,
            "规则名称": self.rule_mapping[rule_id]['rule_name'],
            "规则描述": f"待提取 - {self.rule_mapping[rule_id]['rule_name']}的规则描述",
            "正面示例": positive_examples,
            "反面示例": negative_examples
        }
        
        print(f"规则 {rule_id} 处理完成 - 正面示例: {len(positive_examples)}, 反面示例: {len(negative_examples)}")
        return result

    def save_intermediate_results(self, rule_id: int, batch_num: int, positive: List, negative: List):
        """保存中间结果"""
        os.makedirs(f"intermediate_results/rule_{rule_id}", exist_ok=True)
        
        with open(f"intermediate_results/rule_{rule_id}/batch_{batch_num}_positive.json", 'w', encoding='utf-8') as f:
            json.dump(positive, f, ensure_ascii=False, indent=2)
        
        with open(f"intermediate_results/rule_{rule_id}/batch_{batch_num}_negative.json", 'w', encoding='utf-8') as f:
            json.dump(negative, f, ensure_ascii=False, indent=2)

    def build_complete_knowledge_base(self, rule_ids: List[int] = None, batch_size: int = 100):
        """构建完整的知识库"""
        df = pd.read_excel('业务反馈结果.xls')
        
        if rule_ids is None:
            rule_ids = list(self.rule_mapping.keys())
        
        print(f"开始构建完整知识库，处理规则: {rule_ids}")
        print(f"总数据量: {len(df)} 条")
        print(f"并行线程数: {self.max_workers}")
        print(f"批处理大小: {batch_size}")
        
        complete_knowledge_base = {}
        
        for rule_id in rule_ids:
            try:
                rule_kb = self.process_rule_parallel(df, rule_id, batch_size)
                complete_knowledge_base[rule_id] = rule_kb
                
                # 保存单个规则的最终结果
                with open(f'knowledge_base_rule_{rule_id}_complete.json', 'w', encoding='utf-8') as f:
                    json.dump(rule_kb, f, ensure_ascii=False, indent=2)
                
                print(f"规则 {rule_id} 知识库已保存到 knowledge_base_rule_{rule_id}_complete.json")
                
            except Exception as e:
                print(f"处理规则 {rule_id} 时出错: {e}")
                continue
        
        # 保存完整知识库
        with open('complete_knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(complete_knowledge_base, f, ensure_ascii=False, indent=2)
        
        print("完整知识库构建完成！")
        return complete_knowledge_base

if __name__ == '__main__':
    # 创建并行构建器，设置合适的并发数
    builder = ParallelKnowledgeBaseBuilder(max_workers=8)
    
    # 构建完整知识库
    print("开始构建完整知识库...")
    complete_kb = builder.build_complete_knowledge_base(
        rule_ids=[7, 8],  # 先测试两个规则
        batch_size=50     # 调整批处理大小
    )
    
    print("知识库构建完成！") 