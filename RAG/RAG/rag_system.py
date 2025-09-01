import os
import json
import time
# import asyncio
import faiss
import numpy as np
import torch
# import threading
from typing import List, Dict, Any, Optional, Generator, Tuple
# from concurrent.futures import ThreadPoolExecutor
# from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
# from pydantic import BaseModel, Field
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# from sentence_transformers import SentenceTransformer
# from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

# from document_processor import DocumentProcessor
# import LLM_api

from vllm import LLM
import json

# Constants
MAX_CONCURRENT_QUEUE = 16
MAX_REQUESTS_QUEUE = 64  # Maximum number of requests in queue
REQUEST_TIMEOUT = 15 # Timeout in seconds for waiting for a request slot
VECTOR_DB_PATH = "vector_db"
EMBEDDING_MODEL_NAME = "/mnt/data/m3e-large"
RERANKER_MODEL_NAME = "/mnt/data/bge-reranker-large"
DOCS_PATH = "./docs/zh-cn/"
TOP_K_RETRIEVAL = 36
TOP_K_RERANK = 5

loop = None

class RAGSystem:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {self.device}")
        # Initialize embedding model
        # self.embedding_model = HuggingFaceEmbeddings(
        #     model_name=EMBEDDING_MODEL_NAME,
        #     model_kwargs={'device': 'cuda'},
        #     encode_kwargs={'normalize_embeddings': True}
        # )
        self.embedding_model = LLM(model="/root/code/Qwen3-Embedding-4B", task="embed",dtype=torch.float16)
        print(f"Embedding model initialized: {self.embedding_model}")
        
        # # Initialize reranker model
        # self.rerank_tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL_NAME)
        # print(f"Reranker tokenizer initialized: {self.rerank_tokenizer}")
        # self.rerank_model = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL_NAME).to(self.device)
        # print(f"Reranker model initialized: {self.rerank_model}")
        
        # Initialize FAISS index
        self.index = None
        self.documents = []
        
        print(f"RAGSystem initialized")

    def build_vector_db(self, json_path: str = "results/complete_knowledge_base.json") -> None:
        """Build the vector database from documents."""
        # # print(f"Building vector database from {docs_path}...")
        # # Process documents
        # processor = DocumentProcessor()
        # self.documents = processor.process_directory(docs_path)
        # json.load 加载json文件：
        all_texts = {}
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, value in data.items(): # 遍历rule_id

                all_texts[key] = {"positive": [], "negative": []}
                for positive_example in value['正面示例']:
                    positive_example.pop('defect_id')
                    positive_example['规则名称'] = value['规则名称']
                    positive_example['当前句子'] = positive_example.pop('sentence')
                    positive_example['相关句子'] = positive_example.pop('reference_sentence')
                    positive_example['当前行号'] = positive_example.pop('line_num')
                    positive_example['上下文'] = positive_example.pop('context')
                    # "用户拒绝的修改"
                    # "注意事项"
                    # "用户拒绝的建议"
                    now_dict = {
                        "规则名称": positive_example['规则名称'],
                        "当前句子": positive_example['当前句子'],
                        "相关句子": positive_example['相关句子'],
                        "当前行号": positive_example['当前行号'],
                        "用户拒绝的建议": positive_example['用户拒绝的建议'],
                        "用户拒绝的修改": positive_example['用户拒绝的修改'],
                        "注意事项": positive_example['注意事项']
                    }

                    text = positive_example['上下文']
                    if text:
                        text = json.loads(text)
                        text = [(key, value) for key, value in text.items()]
                        text.sort(key=lambda x:int(x[0]))
                        text = "\n".join([f"{key}: {value}" for key, value in text])
                        now_dict["上下文"] = text
                    else:
                        now_dict["上下文"] = ""

                    all_texts[key]["positive"].append((positive_example['用户拒绝的建议'], now_dict))


                for negative_example in value['反面示例']:
                    negative_example.pop('defect_id')
                    negative_example['规则名称'] = value['规则名称']
                    negative_example['当前句子'] = negative_example.pop('sentence')
                    negative_example['相关句子'] = negative_example.pop('reference_sentence')
                    negative_example['当前行号'] = negative_example.pop('line_num')
                    negative_example['上下文'] = negative_example.pop('context')
                    # "修改建议"
                    # "更改后示例"
                    # "触发条件"
                    now_dict = {
                        "规则名称": negative_example['规则名称'],
                        "当前句子": negative_example['当前句子'],
                        "相关句子": negative_example['相关句子'],
                        "当前行号": negative_example['当前行号'],
                        "用户接受的建议": negative_example['修改建议'],
                        "用户接受的修改": negative_example['更改后示例'],
                        "触发条件": negative_example['触发条件']
                    }

                    text = negative_example['上下文']
                    if text:
                        text = json.loads(text)
                        text = [(key, value) for key, value in text.items()]
                        text.sort(key=lambda x:int(x[0]))
                        text = "\n".join([f"{key}: {value}" for key, value in text])
                        now_dict["上下文"] = text
                    else:
                        now_dict["上下文"] = ""

                    all_texts[key]["negative"].append((negative_example['修改建议'], now_dict))
        
        # Store texts for saving
        self.all_texts = all_texts
        
        # # Extract text for embedding
        # texts = [doc.page_content for doc in self.documents]
        all_embeddings = {}
        for key, value in all_texts.items():
            all_embeddings[key] = {}
            positive_outputs = self.embedding_model.embed([text for text, _ in value["positive"]])
            all_embeddings[key]["positive"] = [output.outputs.embedding for output in positive_outputs]
            negative_outputs = self.embedding_model.embed([text for text, _ in value["negative"]])
            all_embeddings[key]["negative"] = [output.outputs.embedding for output in negative_outputs]
            # print(all_embeddings[key]["positive"] )
        
        dimension = len(self.embedding_model.embed(["1"])[0].outputs.embedding)
        self.index = {}
        for key, value in all_embeddings.items():
            self.index[key] = {}
            self.index[key]["positive"] = faiss.IndexFlatL2(dimension)
            self.index[key]["negative"] = faiss.IndexFlatL2(dimension)
            self.index[key]["positive"].add(np.array(value["positive"], dtype=np.float32))
            self.index[key]["negative"].add(np.array(value["negative"], dtype=np.float32))
        
    
    def save_vector_db(self, path: str = VECTOR_DB_PATH) -> None:
        """Save the vector database to disk."""
        if not os.path.exists(path):
            os.makedirs(path)
        
        # Save FAISS indices for each rule
        for key in self.index.keys():
            rule_path = os.path.join(path, f"rule_{key}")
            if not os.path.exists(rule_path):
                os.makedirs(rule_path)
            faiss.write_index(self.index[key]["positive"], os.path.join(rule_path, "positive_index.faiss"))
            faiss.write_index(self.index[key]["negative"], os.path.join(rule_path, "negative_index.faiss"))
        
        # Save all texts
        with open(os.path.join(path, "all_texts.json"), "w", encoding="utf-8") as f:
            json.dump(self.all_texts, f, ensure_ascii=False, indent=2)
        
        print(f"Vector database saved to {path}")
    
    def load_vector_db(self, path: str = VECTOR_DB_PATH) -> None:
        """Load the vector database from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Vector database not found at {path}")
        
        # Load all texts
        with open(os.path.join(path, "all_texts.json"), "r", encoding="utf-8") as f:
            self.all_texts = json.load(f)
        
        # Load FAISS indices for each rule
        self.index = {}
        for key in self.all_texts.keys():
            rule_path = os.path.join(path, f"rule_{key}")
            if os.path.exists(rule_path):
                self.index[key] = {}
                self.index[key]["positive"] = faiss.read_index(os.path.join(rule_path, "positive_index.faiss"))
                self.index[key]["negative"] = faiss.read_index(os.path.join(rule_path, "negative_index.faiss"))
                
                # # Move indices to GPU if available
                # if torch.cuda.is_available():
                #     res = faiss.StandardGpuResources()
                #     self.index[key]["positive"] = faiss.index_cpu_to_gpu(res, 0, self.index[key]["positive"])
                #     self.index[key]["negative"] = faiss.index_cpu_to_gpu(res, 0, self.index[key]["negative"])
        
        print(f"Vector database loaded from {path} with {len(self.index)} rules")
    
    def retrieve(self, rule_id: str, query: str, top_k: int = TOP_K_RETRIEVAL) -> dict:
        """Retrieve relevant documents for a specific rule using vector similarity."""
        if rule_id not in self.index:
            raise ValueError(f"Rule ID {rule_id} not found in the vector database")
        
        # Generate query embedding
        query_outputs = self.embedding_model.embed([query])
        query_embedding = query_outputs[0].outputs.embedding
        
        # Search in positive examples
        positive_distances, positive_indices = self.index[rule_id]["positive"].search(
            np.array([query_embedding], dtype=np.float32), 
            min(top_k, self.index[rule_id]["positive"].ntotal)
        )
        
        # Search in negative examples
        negative_distances, negative_indices = self.index[rule_id]["negative"].search(
            np.array([query_embedding], dtype=np.float32), 
            min(top_k, self.index[rule_id]["negative"].ntotal)
        )
        
        # Prepare results
        results = {
            "positive": [],
            "negative": []
        }
        
        # Process positive examples
        for i, idx in enumerate(positive_indices[0]):
            if idx < len(self.all_texts[rule_id]["positive"]):
                text_dict = self.all_texts[rule_id]["positive"][idx][1]
                distance = positive_distances[0][i]
                similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity
                results["positive"].append({
                    "content_dict": text_dict,
                    "similarity": similarity,
                    # "distance": distance
                })
        
        # Process negative examples
        for i, idx in enumerate(negative_indices[0]):
            if idx < len(self.all_texts[rule_id]["negative"]):
                text_dict = self.all_texts[rule_id]["negative"][idx][1]
                distance = negative_distances[0][i]
                similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity
                results["negative"].append({
                    "content_dict": text_dict,
                    "similarity": similarity,
                    # "distance": distance
                })
        
        return results
    
    def print_retrieve_result(self, answer: dict):
        print("=== RAG检索结果 ===")
        print(f"规则ID: 6")
        print(f"查询: 开发者没有配置背板图.")
        print()

        print("正面示例 (用户拒绝的修改):")
        print("-" * 50)
        for i, example in enumerate(answer["positive"], 1):
            print(f"示例 {i}:")
            print(f"  相似度: {example['similarity']:.4f}")
            # print(f"  距离: {example['distance']:.4f}")
            print(f"  内容: {json.dumps(example['content_dict'], ensure_ascii=False, indent=4)}")
            print()

        print("反面示例 (用户接受的修改):")
        print("-" * 50)
        for i, example in enumerate(answer["negative"], 1):
            print(f"示例 {i}:")
            print(f"  相似度: {example['similarity']:.4f}")
            # print(f"  距离: {example['distance']:.4f}")
            print(f"  内容: {json.dumps(example['content_dict'], ensure_ascii=False, indent=4)}")
            print()


    def rerank(self, query: str, retrieval_results: List[Tuple[Document, float, str]], top_k: int = TOP_K_RERANK) -> List[Tuple[Tuple[Document, float, str], float]]:
        """Rerank retrieved documents using the reranker model."""
        if not retrieval_results:
            return []
        
        # Prepare pairs for reranking
        pairs = [(query, doc.page_content) for doc, _, _ in retrieval_results]
        
        # Tokenize pairs
        with self.rerank_tokenizer_lock:
            features = self.rerank_tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            ).to(self.device)
        
        # Get reranker scores
        with self.rerank_lock:
            with torch.no_grad():
                scores = self.rerank_model(**features).logits.squeeze(-1).cpu().tolist()
        
        # Combine with original results and sort by reranker score
        reranked_results = [(result, score) for result, score in zip(retrieval_results, scores)]
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return reranked_results[:top_k]
    
    def _get_rerank_merged(self, rerank_docs: List, query: str) -> str:
        """构建重排序结果的提示模板"""
        prompt = "使用以下包含在<context>标签中的信息，简洁和专业的回答<question>标签中包含的问题。 \n"
        prompt += "请注意，在回答的时候，如果需要使用到已知信息，需要引用已知信息。（比如在回答时添加[1]，然后在回答的最后补充[1]的所有元信息【包括：文件路径、分块位置、重排序分数】）\n"
        prompt += "如果无法从中得到答案，请说 \"无答案\"，不允许在答案中添加编造成分，答案请使用中文。\n\n"
        
        prompt += "-" * 50 + "\n"
        for (doc, orig_score, source), rerank_score in rerank_docs:
            prompt += f"文件路径: {doc.metadata.get('source', '未知')}\n"
            prompt += f"分块位置: " # "h1 > h2 > h3 > h4 > h5 > h6"
            first_h = True
            for i in range(1,7):
                if first_h:
                    prompt += f"h{i} {doc.metadata.get(f'h{i}', '未知')}"
                    first_h = False
                elif doc.metadata.get(f'h{i}'):
                    prompt += f" > h{i} {doc.metadata.get(f'h{i}', '未知')}"
            prompt += f"\n"
            prompt += f"检索来源: {source}\n"
            prompt += f"原始分数: {orig_score:.4f}\n"
            prompt += f"重排序分数: {rerank_score:.4f}\n"
            prompt += f"内容: {doc.page_content}\n"
            prompt += "-" * 50 + "\n"
            
        prompt += f"\n问题: {query}"
        return prompt
    
    async def process_query(self, query: str, use_rag: bool = True):
        """Process a query and return a streaming response.
        
        Args:
            query: The user's query
            use_rag: Whether to use RAG (True) or direct LLM query (False)
        """
        acquired = await self.request_queue.acquire()
        
        if not acquired:
            # 检查是请求队列满还是并发队列满导致的拒绝
            if self.request_queue.is_request_queue_full:
                print("服务器请求队列已满, rejecting request")
                # 请求队列已满
                yield JSONResponse(
                    status_code=503,
                    content={"error": "服务器请求队列已满，请稍后再试", "queue_full": True}
                )
            else:
                print(f"等待处理超时（{REQUEST_TIMEOUT}秒）, rejecting request")
                # 并发队列等待超时
                yield JSONResponse(
                    status_code=503,
                    content={"error": f"等待处理超时（{REQUEST_TIMEOUT}秒），请稍后再试", "timeout": True}
                )
            return
       
        
        try:
            if use_rag:
                # RAG流程: 检索、重排序、生成答案
                # Run retrieval in a thread to avoid blocking
                retrieval_results = await loop.run_in_executor(
                    self.executor, 
                    self.retrieve,
                    query
                )
                
                # Run reranking in a thread
                rerank_results = await loop.run_in_executor(
                    self.executor,
                    self.rerank,
                    query,
                    retrieval_results
                )
                
                # Generate prompt for LLM
                prompt = self._get_rerank_merged(rerank_results, query)
            else:
                # 直接LLM查询，不使用RAG
                prompt = query
            
            # Process with LLM and yield results
            async for chunk in LLM_api.query_deepseek_stream_async(prompt):
                if "error" in chunk:
                    yield json.dumps({"error": chunk["error"]}) + "\n"
                    return
                
                if "final_context" in chunk:
                    continue
                
                if "response" in chunk:
                    # Format response in OpenAI-like format
                    response_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "rag-system",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "content": chunk["response"]
                                },
                                "finish_reason": "stop" if chunk.get("done", False) else None
                            }
                        ]
                    }
                    yield json.dumps(response_chunk) + "\n"
        finally:
            # Always release the slot, even if an error occurs
            await self.request_queue.release()

 