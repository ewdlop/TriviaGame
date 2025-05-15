from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from rag_service import RAGService
from document_service import DocumentService
import uvicorn
import os
from tempfile import NamedTemporaryFile
import tempfile

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
    topic: str

class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        print(f"Received file: {file.filename}, content type: {file.content_type}")
        
        # 创建临时文件
        with NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            temp_path = temp_file.name
            
        print(f"File saved to: {temp_path}")
        
        try:
            # 处理文档
            document_service.process_document(temp_path)
            
            # 获取文档内容
            content = document_service.get_document_content(temp_path)
            
            # 生成问题
            questions = rag_service.generate_questions(
                "temp_doc",
                content
            )
            
            return {"questions": questions}
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
                print(f"Temporary file deleted: {temp_path}")
            except Exception as e:
                print(f"Error deleting temporary file: {e}")
                
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/upload")
async def upload_file_new(file: UploadFile = File(...)):
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # 获取文档内容
        content = document_service.get_document_content(temp_path)
        
        # 生成问题
        questions = rag_service.generate_questions(file.filename, content)
        
        # 删除临时文件
        os.unlink(temp_path)
        
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-directly")
async def generate_questions_directly(request: GenerateRequest):
    try:
        print(f"收到生成问题请求，主题: {request.topic}")
        if not request.topic or not request.topic.strip():
            raise HTTPException(status_code=400, detail="主题不能为空")
            
        questions = rag_service.generate_questions_directly(request.topic)
        print(f"成功生成 {len(questions)} 个问题")
        return {"questions": questions}
    except Exception as e:
        print(f"生成问题时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成问题失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True) 