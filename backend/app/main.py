from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from rag_service import RAGService
from document_service import DocumentService

load_dotenv()

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 初始化服务
rag_service = RAGService()
document_service = DocumentService()

class QuestionRequest(BaseModel):
    question: str
    difficulty: Optional[str] = "medium"

class QuestionResponse(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

@app.get("/")
async def root():
    return {"message": "Trivia Game API"}

@app.post("/api/upload-document")
async def upload_document(file: UploadFile = File(...)):
    try:
        # 保存上传的文件
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 处理文档
        document_service.process_document(file_path)
        
        return {"message": "文档上传并处理成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/api/generate-question", response_model=QuestionResponse)
def generate_question(request: QuestionRequest):
    try:
        question_data = rag_service.generate_question(
            request.question,
            request.difficulty
        )
        return question_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 