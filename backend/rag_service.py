from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.chroma import Chroma
from langchain.schema import Document
import json
from typing import List, Dict
import re

class RAGService:
    def __init__(self):
        # 使用Ollama的embeddings
        self.embeddings = OllamaEmbeddings(model="llama2")
        # 使用Ollama的LLM
        self.llm = ChatOllama(model="llama2", temperature=0.7)
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 初始化向量存储
        self.vector_store = None
        
        # 尝试加载现有的向量存储
        try:
            self.vector_store = Chroma(
                collection_name="document_chunks",
                embedding_function=self.embeddings,
                persist_directory="chroma_db"
            )
            print("已加载现有的向量存储")
        except:
            print("未找到现有的向量存储")
        
        # 初始化提示模板
        self.question_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的问答游戏出题者。基于给定的文档内容，生成5个有趣且具有教育意义的问答题目。
            请确保：
            1. 问题必须基于提供的文档内容
            2. 问题要考察文档中的重要概念和细节
            3. 选项合理且具有迷惑性
            4. 解释要详细说明为什么这个答案是正确的
            5. 选项必须使用"选项A"、"选项B"、"选项C"、"选项D"的格式
            6. 正确答案必须是选项之一（"选项A"、"选项B"、"选项C"或"选项D"）
            7. 必须生成5个问题
            
            请严格按照以下JSON格式返回，不要添加任何其他内容：
            [
                {
                    "question": "问题文本",
                    "options": ["选项A", "选项B", "选项C", "选项D"],
                    "correct_answer": "选项A",
                    "explanation": "详细解释"
                }
            ]"""),
            ("user", "文档内容：{context}")
        ])

    def _extract_json_from_response(self, response: str) -> str:
        """从响应中提取JSON字符串"""
        # 尝试找到JSON数组的开始和结束
        match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
        if match:
            return match.group(0)
        return response

    def _create_vector_store(self, text: str):
        """创建向量存储"""
        print("开始处理文档...")
        # 分割文本
        chunks = self.text_splitter.split_text(text)
        print(f"文档已分割为 {len(chunks)} 个块")
        
        # 创建文档
        documents = [Document(page_content=chunk) for chunk in chunks]
        print("正在创建向量存储...")
        
        # 分批处理文档
        batch_size = 10
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"正在处理第 {batch_num}/{total_batches} 批文档 (共 {len(batch)} 个文档块)...")
            
            if i == 0:
                # 第一批创建向量存储
                self.vector_store = Chroma.from_documents(
                    batch,
                    embedding=self.embeddings,
                    collection_name="document_chunks",
                    persist_directory="chroma_db"
                )
            else:
                # 后续批次添加到向量存储
                self.vector_store.add_documents(batch)
            
            print(f"第 {batch_num} 批文档处理完成")
        
        print("所有文档处理完成")

    def _get_relevant_chunks(self, query: str, k: int = 3) -> str:
        """获取相关文本块"""
        if not self.vector_store:
            return ""
        
        # 搜索相关文本块
        docs = self.vector_store.similarity_search(query, k=k)
        # 合并文本块
        return "\n".join(doc.page_content for doc in docs)

    def generate_questions(self, doc_id: str, context: str, use_existing_store: bool = False) -> List[Dict]:
        """生成问题"""
        try:
            if not use_existing_store:
                print("Creating vector store...")
                # 创建向量存储
                self._create_vector_store(context)
            elif not self.vector_store:
                print("Warning: No existing vector store found, creating new one...")
                self._create_vector_store(context)
            else:
                print("Using existing vector store...")
            
            print("Generating questions...")
            # 获取相关文档块
            relevant_chunks = self._get_relevant_chunks(context, k=5)
            if not relevant_chunks:
                print("Warning: No relevant chunks found")
                return [self._get_default_question() for _ in range(5)]
            
            # 生成问题
            response = self.llm.invoke(
                self.question_template.format_messages(
                    context=relevant_chunks
                )
            )
            
            print(f"Raw response: {response.content}")
            
            # 提取并解析JSON
            json_str = self._extract_json_from_response(response.content)
            print(f"Extracted JSON: {json_str}")
            
            questions = json.loads(json_str)
            
            # 验证问题格式
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            
            if len(questions) < 5:
                print(f"Warning: Only generated {len(questions)} questions, expected 5")
                # 如果问题数量不足，添加默认问题
                while len(questions) < 5:
                    questions.append(self._get_default_question())
            
            # 验证每个问题
            for q in questions:
                if not all(k in q for k in ["question", "options", "correct_answer", "explanation"]):
                    raise ValueError("Question missing required fields")
                if not isinstance(q["options"], list) or len(q["options"]) != 4:
                    raise ValueError("Options must be a list of 4 items")
                # 确保答案是选项之一
                if q["correct_answer"] not in q["options"]:
                    q["correct_answer"] = q["options"][0]  # 默认使用第一个选项作为正确答案
                
                # 验证问题是否基于文档内容
                relevant_chunks = self._get_relevant_chunks(q["question"])
                if not relevant_chunks:
                    print(f"Warning: Question '{q['question']}' may not be based on document content")
                    # 如果问题不基于文档内容，重新生成
                    new_response = self.llm.invoke(
                        self.question_template.format_messages(
                            context=relevant_chunks
                        )
                    )
                    try:
                        new_question = json.loads(self._extract_json_from_response(new_response.content))[0]
                        q.update(new_question)
                    except:
                        print(f"Failed to regenerate question: {q['question']}")
            
            print(f"Generated {len(questions)} questions")
            return questions
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return [self._get_default_question() for _ in range(5)]
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return [self._get_default_question() for _ in range(5)]
    
    def _get_default_question(self) -> Dict:
        """返回默认问题"""
        return {
            "question": "这是一个示例问题",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": "选项A",
            "explanation": "这是一个示例解释"
        } 