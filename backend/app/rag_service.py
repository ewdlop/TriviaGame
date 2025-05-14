from langchain.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
import json
from typing import List, Dict

class RAGService:
    def __init__(self):
        # 使用Ollama的embeddings
        self.embeddings = OllamaEmbeddings(model="llama2")
        # 使用Ollama的LLM
        self.llm = ChatOllama(model="llama2", temperature=0.7)
        
        # 初始化提示模板
        self.question_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的问答游戏出题者。基于给定的文档内容，生成5个有趣且具有教育意义的问答题目。
            请确保：
            1. 问题清晰明确
            2. 选项合理且具有迷惑性
            3. 解释详细且易于理解
            4. 问题内容要基于提供的文档内容
            
            请以JSON格式返回，包含以下字段的数组：
            [
                {
                    "question": "问题文本",
                    "options": ["选项A", "选项B", "选项C", "选项D"],
                    "correct_answer": "正确答案",
                    "explanation": "详细解释"
                }
            ]"""),
            ("user", "文档内容：{context}")
        ])

    def generate_questions(self, doc_id: str, context: str) -> List[Dict]:
        """生成问题"""
        try:
            # 生成问题
            response = self.llm.invoke(
                self.question_template.format_messages(
                    context=context
                )
            )
            
            # 解析响应
            questions = json.loads(response.content)
            return questions
        except json.JSONDecodeError:
            # 如果解析失败，返回一个默认问题
            return [{
                "question": "这是一个示例问题",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "correct_answer": "选项A",
                "explanation": "这是一个示例解释"
            }] 