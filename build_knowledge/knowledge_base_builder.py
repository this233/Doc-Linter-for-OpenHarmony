import pandas as pd
import json
import requests
from typing import Dict, List, Any
import time

class KnowledgeBaseBuilder:
    def __init__(self):
        self.api_key = "siq3nBr8C75Pv89E0CQaKq4c3KTCpOREj8Umj8OMCM5ByKkBrHxm-IOPiLuFlEOjnU3HFE5Hv-sfLzShM8CCoA"
        self.url = "https://api.modelarts-maas.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
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

    def call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        data = {
            "model": "DeepSeek-R1",
            "messages": [
                {"role": "system", "content": "你是一个专业的文档质量分析专家，擅长分析文档编写规则和用户反馈。"},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.url, headers=self.headers, data=json.dumps(data), verify=False)
            if response.status_code == 200:
                result = response.json()
                print(f"llm call result: {result}")
                return result['choices'][0]['message']['content']
            else:
                print(f"API调用失败: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            print(f"API调用异常: {e}")
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
        response = self.call_llm(prompt)
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
        response = self.call_llm(prompt)
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
        response = self.call_llm(prompt)
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
        response = self.call_llm(prompt)
        return response.replace("触发条件：", "").strip()

    def process_feedback_data(self, df: pd.DataFrame, rule_id: int, sample_size: int = None) -> Dict[str, Any]:
        """处理特定规则的反馈数据"""
        rule_data = df[df['rule_id'] == rule_id].copy()
        
        if sample_size:
            rule_data = rule_data.sample(min(sample_size, len(rule_data)))
        
        positive_examples = []  # 用户拒绝的案例（正面示例）
        negative_examples = []  # 用户接受的案例（反面示例）
        
        print(f"处理规则 {rule_id} ({self.rule_mapping[rule_id]['rule_name']})...")
        print(f"总计 {len(rule_data)} 条数据")
        
        for idx, row in rule_data.iterrows():
            print(f"处理第 {idx+1}/{len(rule_data)} 条数据...")
            
            if row['status'] == 2:  # 用户拒绝
                if pd.notna(row['reason_feedback']):
                    # 判断用户理由是否有效
                    ref_sentence = row['reference_sentence'] if pd.notna(row['reference_sentence']) else ""
                    prob_context = row['problem_context'] if pd.notna(row['problem_context']) else ""
                    if self.judge_effectiveness(row['reason_feedback'], row['fixed_sentence'], row['problematic_sentence'], ref_sentence, prob_context):
                        # 提取注意事项
                        attention_points = self.extract_attention_points(row)
                        
                        positive_example = {
                            "defect_id": row['defect_id'],
                            "sentence": row['problematic_sentence'],
                            "reference_sentence": row['reference_sentence'] if pd.notna(row['reference_sentence']) else "",
                            "line_num": row['problematic_line_num'],
                            "context": row['problem_context'] if pd.notna(row['problem_context']) else "",
                            "用户拒绝的修改": row['fixed_sentence'],
                            "注意事项": attention_points
                        }
                        positive_examples.append(positive_example)
                        print(f"  添加正面示例: {row['defect_id']}")
            else:  # 用户接受
                # 判断案例是否典型
                ref_sentence = row['reference_sentence'] if pd.notna(row['reference_sentence']) else ""
                prob_context = row['problem_context'] if pd.notna(row['problem_context']) else ""
                if self.judge_typicality(row['problematic_sentence'], row['fixed_sentence'], row['reason'], self.rule_mapping[rule_id]['rule_name'], ref_sentence, prob_context):
                    # 提取触发条件
                    trigger_conditions = self.extract_trigger_conditions(row)
                    
                    negative_example = {
                        "defect_id": row['defect_id'],
                        "sentence": row['problematic_sentence'],
                        "reference_sentence": row['reference_sentence'] if pd.notna(row['reference_sentence']) else "",
                        "line_num": row['problematic_line_num'],
                        "context": row['problem_context'] if pd.notna(row['problem_context']) else "",
                        "修改建议": row['reason'],
                        "更改后示例": row['fixed_sentence'],
                        "触发条件": trigger_conditions
                    }
                    negative_examples.append(negative_example)
                    print(f"  添加反面示例: {row['defect_id']}")
            
            # 添加延迟避免API限制
            time.sleep(0.1)
        
        return {
            "规则ID": rule_id,
            "规则名称": self.rule_mapping[rule_id]['rule_name'],
            "规则描述": f"待提取 - {self.rule_mapping[rule_id]['rule_name']}的规则描述",
            "正面示例": positive_examples,
            "反面示例": negative_examples
        }

    def build_knowledge_base_sample(self, rule_ids: List[int], sample_size: int = 5):
        """构建小规模知识库样本"""
        df = pd.read_excel('业务反馈结果.xls')
        knowledge_base = {}
        
        for rule_id in rule_ids:
            rule_kb = self.process_feedback_data(df, rule_id, sample_size)
            knowledge_base[rule_id] = rule_kb
            
            # 保存单个规则的结果
            with open(f'knowledge_base_rule_{rule_id}_sample.json', 'w', encoding='utf-8') as f:
                json.dump(rule_kb, f, ensure_ascii=False, indent=2)
            
            print(f"规则 {rule_id} 样本知识库已保存")
        
        return knowledge_base

if __name__ == '__main__':
    builder = KnowledgeBaseBuilder()
    
    # 先测试规则7和规则8的小样本
    print("开始构建小规模知识库样本...")
    sample_kb = builder.build_knowledge_base_sample([7, 8], sample_size=3)
    
    print("样本知识库构建完成！") 