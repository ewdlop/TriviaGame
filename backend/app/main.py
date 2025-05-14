from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from rag_service import RAGService

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

# 初始化RAG服务
rag_service = RAGService()

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