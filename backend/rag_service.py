from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.chroma import Chroma
from langchain.schema import Document
import json
from typing import List, Dict
import re
import os
import subprocess
import time
import platform

class RAGService:
    def __init__(self):
        try:
            print("正在初始化 RAGService...")
            
            # 检查 Ollama 服务是否运行
            system = platform.system()
            if system in ["Darwin", "Linux"]:  # 只在 Mac 或 Linux 上执行
                print("检查 Ollama 服务状态...")
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    
                    if 'ollama' not in result.stdout:
                        print("Ollama 服务未运行，尝试启动...")
                        subprocess.Popen(['ollama', 'serve'])
                        # 等待服务启动
                        time.sleep(5)
                        print("Ollama 服务已启动")
                    else:
                        print("Ollama 服务正在运行")
                except Exception as e:
                    print(f"检查 Ollama 服务时出错: {str(e)}")
                    raise Exception("无法检查或启动 Ollama 服务")
            else:
                print(f"当前操作系统 {system} 不支持自动检查 Ollama 服务")
            
            # 使用Ollama的embeddings
            print("正在初始化 Ollama embeddings...")
            try:
                self.embeddings = OllamaEmbeddings(model="llama2")
                print("Ollama embeddings 初始化成功")
            except Exception as e:
                print(f"初始化 embeddings 失败: {str(e)}")
                raise Exception(f"无法初始化 embeddings: {str(e)}")
            
            # 使用Ollama的LLM
            print("正在初始化 Ollama LLM...")
            try:
                self.llm = ChatOllama(model="llama2", temperature=0.7)
                # 测试连接
                test_response = self.llm.invoke("测试连接")
                if not test_response:
                    raise Exception("LLM 测试响应为空")
                print("Ollama LLM 初始化成功")
            except Exception as e:
                print(f"初始化 LLM 失败: {str(e)}")
                raise Exception(f"无法初始化 LLM: {str(e)}")
            
            # 初始化文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # 初始化向量存储
            self.vector_store = None
            
            # 尝试从chroma_db目录加载现有的向量存储
            try:
                if os.path.exists("chroma_db"):
                    print("正在从chroma_db目录加载向量存储...")
                    self.vector_store = Chroma(
                        collection_name="document_chunks",
                        embedding_function=self.embeddings,
                        persist_directory="chroma_db"
                    )
                    print("成功加载现有的向量存储")
                else:
                    print("未找到chroma_db目录")
            except Exception as e:
                print(f"加载向量存储时出错: {str(e)}")
                print("将创建新的向量存储")
            
            # 初始化直接主题问题生成模板
            self.topic_question_template = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的问答游戏出题者。请基于给定的主题生成5个有趣且具有教育意义的问答题目。
                请确保：
                1. 问题必须与主题相关
                2. 问题要考察主题中的重要概念和细节
                3. 选项合理且具有迷惑性
                4. 解释要详细说明为什么这个答案是正确的
                5. 选项必须使用"选项A"、"选项B"、"选项C"、"选项D"的格式
                6. 正确答案必须是选项之一（"选项A"、"选项B"、"选项C"或"选项D"）
                7. 必须生成5个问题
                
                请严格按照以下JSON格式返回，不要添加任何其他内容：
                {
                    "questions": [
                        {
                            "question": "问题文本",
                            "options": ["选项A", "选项B", "选项C", "选项D"],
                            "correct_answer": "选项A",
                            "explanation": "详细解释"
                        }
                    ]
                }"""),
                ("user", "主题：{context}")
            ])

            # 初始化文档问题生成模板
            self.document_question_template = ChatPromptTemplate.from_messages([
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
                {
                    "questions": [
                        {
                            "question": "问题文本",
                            "options": ["选项A", "选项B", "选项C", "选项D"],
                            "correct_answer": "选项A",
                            "explanation": "详细解释"
                        }
                    ]
                }"""),
                ("user", "文档内容：{context}")
            ])

            print("RAGService 初始化完成")
        except Exception as e:
            print(f"RAGService 初始化失败: {str(e)}")
            raise

    def _extract_json_from_response(self, response: str) -> str:
        """从响应中提取JSON字符串"""
        try:
            # 尝试找到JSON对象的开始和结束
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                # 如果没有找到JSON对象，尝试找JSON数组
                start_idx = response.find('[')
                end_idx = response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                print(f"无法在响应中找到JSON: {response}")
                raise ValueError("响应中不包含有效的JSON")
            
            json_str = response[start_idx:end_idx + 1]
            # 验证提取的字符串是否是有效的JSON
            json.loads(json_str)
            return json_str
        except Exception as e:
            print(f"提取JSON时出错: {str(e)}")
            print(f"原始响应: {response}")
            raise ValueError(f"无法从响应中提取有效的JSON: {str(e)}")

    def _create_vector_store(self, text: str):
            
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

    def _generate_questions_from_context(self, context: str, is_document: bool = True) -> List[Dict]:
        """从上下文中生成问题"""
        try:
            # 选择适当的模板
            template = self.document_question_template if is_document else self.topic_question_template
            
            # 调用LLM生成问题
            response = self.llm.invoke(template.format_messages(context=context))
            
            # 提取JSON
            json_str = self._extract_json_from_response(response.content)
            data = json.loads(json_str)
            
            # 验证问题格式
            if not isinstance(data, dict) or "questions" not in data:
                raise ValueError("生成的问题格式不正确")
            
            questions = data["questions"]
            if not isinstance(questions, list):
                raise ValueError("生成的问题不是列表格式")
            
            # 验证每个问题的格式
            for q in questions:
                if not all(k in q for k in ["question", "options", "correct_answer", "explanation"]):
                    raise ValueError("问题缺少必要的字段")
                if not isinstance(q["options"], list) or len(q["options"]) != 4:
                    raise ValueError("问题选项必须是包含4个选项的列表")
                if q["correct_answer"] not in q["options"]:
                    raise ValueError("正确答案必须是选项之一")
            
            return questions
        except Exception as e:
            print(f"生成问题时出错: {str(e)}")
            # 返回默认问题
            return [self._get_default_question()]

    def generate_questions(self, doc_id: str, context: str, use_existing_store: bool = False) -> List[Dict]:
        """从文档生成问题"""
        try:
            if use_existing_store:
                if not self.vector_store:
                    print("Warning: No existing vector store found")
                    return [self._get_default_question()]
                print("Using existing vector store...")
            else:
                print("Creating vector store...")
                self._create_vector_store(context)
            
            return self._generate_questions_from_context(context, is_document=True)
            
        except Exception as e:
            print(f"生成问题时出错: {str(e)}")
            return [self._get_default_question()]

    def generate_questions_directly(self, topic: str) -> List[Dict]:
        """直接从主题生成问题"""
        try:
            print(f"收到生成问题请求，主题: {topic}")
            if not topic or not topic.strip():
                raise ValueError("主题不能为空")
            
            # 使用主题作为上下文直接生成问题
            return self._generate_questions_from_context(topic, is_document=False)
            
        except Exception as e:
            print(f"生成问题时出错: {str(e)}")
            return [self._get_default_question()]
    
    def _get_default_question(self) -> Dict:
        """返回默认问题"""
        return {
            "question": "这是一个示例问题",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": "选项A",
            "explanation": "这是一个示例解释"
        } 