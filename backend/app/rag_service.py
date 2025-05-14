from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
from typing import List, Dict
import json

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0.7)
        self.vectorstore = Chroma(
            persist_directory="./data",
            embedding_function=self.embeddings
        )
        
        # 初始化提示模板
        self.question_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的问答游戏出题者。基于给定的主题，生成一个有趣且具有教育意义的问答题目。
            请确保：
            1. 问题清晰明确
            2. 选项合理且具有迷惑性
            3. 解释详细且易于理解
            4. 难度符合要求
            
            请以JSON格式返回，包含以下字段：
            - question: 问题文本
            - options: 选项列表（4个选项）
            - correct_answer: 正确答案
            - explanation: 详细解释"""),
            ("user", "主题：{topic}\n难度：{difficulty}")
        ])

    async def generate_question(self, topic: str, difficulty: str) -> Dict:
        # 使用RAG检索相关上下文
        docs = self.vectorstore.similarity_search(topic, k=3)
        context = "\n".join([doc.page_content for doc in docs])
        
        # 生成问题
        response = await self.llm.ainvoke(
            self.question_template.format_messages(
                topic=topic,
                difficulty=difficulty
            )
        )
        
        try:
            # 解析响应
            question_data = json.loads(response.content)
            return question_data
        except json.JSONDecodeError:
            # 如果解析失败，返回一个默认问题
            return {
                "question": f"关于{topic}的基本问题",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "correct_answer": "选项A",
                "explanation": "这是一个示例解释"
            } 