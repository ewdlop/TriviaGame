from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from document_service import DocumentService
import os
from typing import List, Dict
import json

class RAGService:
    def __init__(self):
        # 使用Ollama的embeddings
        self.embeddings = OllamaEmbeddings(model="llama2")
        # 使用Ollama的LLM
        self.llm = Ollama(model="llama2", temperature=0.7)
        self.document_service = DocumentService()
        
        # 初始化提示模板
        self.question_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的问答游戏出题者。基于给定的主题和相关文档内容，生成一个有趣且具有教育意义的问答题目。
            请确保：
            1. 问题清晰明确
            2. 选项合理且具有迷惑性
            3. 解释详细且易于理解
            4. 难度符合要求
            5. 问题内容要基于提供的文档内容
            
            请以JSON格式返回，包含以下字段：
            - question: 问题文本
            - options: 选项列表（4个选项）
            - correct_answer: 正确答案
            - explanation: 详细解释"""),
            ("user", "主题：{topic}\n难度：{difficulty}\n相关文档内容：{context}")
        ])

    def generate_question(self, topic: str, difficulty: str) -> Dict:
        # 使用RAG检索相关上下文
        context = self.document_service.search_documents(topic)
        context_text = "\n".join(context)
        
        # 生成问题
        response = self.llm.invoke(
            self.question_template.format_messages(
                topic=topic,
                difficulty=difficulty,
                context=context_text
            )
        )
        
        try:
            # 解析响应
            question_data = json.loads(response)
            return question_data
        except json.JSONDecodeError:
            # 如果解析失败，返回一个默认问题
            return {
                "question": f"关于{topic}的基本问题",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "correct_answer": "选项A",
                "explanation": "这是一个示例解释"
            } 