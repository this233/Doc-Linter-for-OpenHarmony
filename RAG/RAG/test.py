from RAG.rag_system import RAGSystem
import json

rag_system = RAGSystem()
rag_system.load_vector_db()
answer = rag_system.retrieve("6", "误解",top_k=5)
rag_system.print_retrieve_result(answer)

# print("=== 完整结果 (JSON格式) ===")
# print(json.dumps(answer, ensure_ascii=False, indent=2))
