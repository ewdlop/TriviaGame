from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_service import RAGService
from document_service import DocumentService
import uvicorn

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
rag_service = RAGService()
document_service = DocumentService()

class GenerateRequest(BaseModel):
    document_type: str
    document_content: str

class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

@app.post("/api/generate")
async def generate_questions(request: GenerateRequest):
    try:
        # 处理文档并获取文档ID
        doc_id = document_service.process_document_with_cache(
            request.document_content,
            request.document_type
        )
        
        # 生成问题
        questions = rag_service.generate_questions(
            doc_id,
            request.document_content
        )
        
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True) 