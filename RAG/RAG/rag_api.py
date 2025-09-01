#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统网络接口
提供RESTful API来访问RAG检索功能
"""

import os
import json
import time
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from rag_system import RAGSystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="RAG System API",
    description="RAG检索系统API接口",
    version="1.0.0"
)

# 全局RAG系统实例
rag_system: Optional[RAGSystem] = None

# 请求模型
class RetrievalRequest(BaseModel):
    rule_id: str = Field(..., description="规则ID")
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=36, description="返回的最相似结果数量", ge=1, le=100)

class BuildVectorDBRequest(BaseModel):
    json_path: str = Field(default="results/complete_knowledge_base.json", description="知识库JSON文件路径")

class LoadVectorDBRequest(BaseModel):
    path: str = Field(default="vector_db", description="向量数据库路径")

class SaveVectorDBRequest(BaseModel):
    path: str = Field(default="vector_db", description="向量数据库保存路径")

# 响应模型
class RetrievalResult(BaseModel):
    content_dict: Dict[str, Any] = Field(..., description="检索到的文本内容（字典格式）")
    similarity: float = Field(..., description="相似度分数")

class RetrievalResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    rule_id: str = Field(..., description="规则ID")
    query: str = Field(..., description="查询文本")
    positive: list[RetrievalResult] = Field(..., description="正面示例（用户拒绝的修改）")
    negative: list[RetrievalResult] = Field(..., description="反面示例（用户接受的修改）")
    total_results: int = Field(..., description="返回结果总数")
    processing_time: float = Field(..., description="处理时间（秒）")

# 初始化RAG系统
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化RAG系统"""
    global rag_system
    try:
        logger.info("正在初始化RAG系统...")
        rag_system = RAGSystem()
        
        # 尝试加载已存在的向量数据库
        try:
            rag_system.load_vector_db()
            logger.info("成功加载已存在的向量数据库")
        except FileNotFoundError:
            logger.warning("未找到已存在的向量数据库，需要手动构建")
        
        logger.info("RAG系统初始化完成")
    except Exception as e:
        logger.error(f"RAG系统初始化失败: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global rag_system
    rag_system = None
    logger.info("RAG系统已关闭")

# API接口
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "retrieve": "/retrieve - 执行RAG检索",
            "build_db": "/build_db - 构建向量数据库",
            "load_db": "/load_db - 加载向量数据库",
            "save_db": "/save_db - 保存向量数据库",
            "health": "/health - 健康检查"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    # 检查向量数据库是否已加载
    db_loaded = hasattr(rag_system, 'index') and rag_system.index is not None
    
    return {
        "status": "healthy",
        "rag_system_initialized": True,
        "vector_db_loaded": db_loaded,
        "timestamp": time.time()
    }

@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    """RAG检索接口"""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    if not hasattr(rag_system, 'index') or rag_system.index is None:
        raise HTTPException(status_code=503, detail="向量数据库未加载，请先构建或加载数据库")
    
    start_time = time.time()
    
    try:
        # 执行检索
        results = rag_system.retrieve(
            rule_id=request.rule_id,
            query=request.query,
            top_k=request.top_k
        )
        
        processing_time = time.time() - start_time
        
        # 转换结果格式
        positive_results = [
            RetrievalResult(
                content_dict=result["content_dict"],
                similarity=result["similarity"],
            )
            for result in results["positive"]
        ]
        
        negative_results = [
            RetrievalResult(
                content_dict=result["content_dict"],
                similarity=result["similarity"],
            )
            for result in results["negative"]
        ]
        
        return RetrievalResponse(
            success=True,
            rule_id=request.rule_id,
            query=request.query,
            positive=positive_results,
            negative=negative_results,
            total_results=len(positive_results) + len(negative_results),
            processing_time=processing_time
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"检索过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

@app.post("/build_db")
async def build_vector_db(request: BuildVectorDBRequest, background_tasks: BackgroundTasks):
    """构建向量数据库接口"""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    if not os.path.exists(request.json_path):
        raise HTTPException(status_code=404, detail=f"知识库文件不存在: {request.json_path}")
    
    def build_db_task():
        try:
            logger.info(f"开始构建向量数据库，使用文件: {request.json_path}")
            rag_system.build_vector_db(request.json_path)
            logger.info("向量数据库构建完成")
        except Exception as e:
            logger.error(f"构建向量数据库失败: {str(e)}")
    
    # 在后台执行构建任务
    background_tasks.add_task(build_db_task)
    
    return {
        "message": "向量数据库构建任务已启动",
        "json_path": request.json_path,
        "status": "building"
    }

@app.post("/load_db")
async def load_vector_db(request: LoadVectorDBRequest):
    """加载向量数据库接口"""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail=f"向量数据库路径不存在: {request.path}")
    
    try:
        rag_system.load_vector_db(request.path)
        return {
            "message": "向量数据库加载成功",
            "path": request.path,
            "rules_loaded": len(rag_system.index) if hasattr(rag_system, 'index') else 0
        }
    except Exception as e:
        logger.error(f"加载向量数据库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载失败: {str(e)}")

@app.post("/save_db")
async def save_vector_db(request: SaveVectorDBRequest):
    """保存向量数据库接口"""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    if not hasattr(rag_system, 'index') or rag_system.index is None:
        raise HTTPException(status_code=400, detail="没有可保存的向量数据库")
    
    try:
        rag_system.save_vector_db(request.path)
        return {
            "message": "向量数据库保存成功",
            "path": request.path,
            "rules_saved": len(rag_system.index)
        }
    except Exception as e:
        logger.error(f"保存向量数据库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

@app.get("/rules")
async def get_available_rules():
    """获取可用的规则列表"""
    global rag_system
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    if not hasattr(rag_system, 'index') or rag_system.index is None:
        raise HTTPException(status_code=503, detail="向量数据库未加载")
    
    rules = list(rag_system.index.keys())
    return {
        "rules": rules,
        "total_rules": len(rules)
    }

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误", "message": str(exc)}
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="启动RAG系统API服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8001, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    
    args = parser.parse_args()
    
    print(f"启动RAG系统API服务...")
    print(f"服务地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "rag_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    ) 