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
        """创建向量存储"""
        # 如果向量存储已存在，直接返回
        if self.vector_store:
            print("向量存储已存在，跳过创建")
            return
            
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
            if use_existing_store:
                if not self.vector_store:
                    print("Warning: No existing vector store found")
                    return [self._get_default_question() for _ in range(5)]
                print("Using existing vector store...")
            else:
                print("Creating vector store...")
                self._create_vector_store(context)
            
            print("Generating questions...")
            # 获取所有相关文档块
            all_chunks = []
            for i in range(5):  # 生成5个问题
                # 使用不同的查询来获取不同的文档块
                query = f"重要概念 {i+1}"
                chunks = self._get_relevant_chunks(query, k=2)
                if chunks:
                    all_chunks.append(chunks)
            
            if not all_chunks:
                print("Warning: No relevant chunks found")
                return [self._get_default_question() for _ in range(5)]
            
            # 为每个文档块生成一个问题
            valid_questions = []
            for i, chunks in enumerate(all_chunks):
                print(f"正在为第 {i+1} 个文档块生成问题...")
                print(f"文档块内容: {chunks[:200]}...")  # 只打印前200个字符
                
                # 生成问题
                response = self.llm.invoke(
                    self.question_template.format_messages(
                        context=chunks
                    )
                )
                
                try:
                    # 提取并解析JSON
                    json_str = self._extract_json_from_response(response.content)
                    questions = json.loads(json_str)
                    
                    if not isinstance(questions, list) or len(questions) == 0:
                        print(f"Warning: Invalid response format for chunk {i+1}")
                        continue
                    
                    # 验证问题
                    q = questions[0]  # 只取第一个问题
                    
                    # 检查必要字段
                    if not all(k in q for k in ["question", "options", "correct_answer", "explanation"]):
                        print(f"Warning: Question missing required fields: {q}")
                        continue
                        
                    # 检查选项格式
                    if not isinstance(q["options"], list) or len(q["options"]) != 4:
                        print(f"Warning: Invalid options format: {q['options']}")
                        continue
                        
                    # 检查答案格式
                    if not q["correct_answer"].startswith("选项"):
                        print(f"Warning: Invalid answer format: {q['correct_answer']}")
                        continue
                        
                    # 确保答案是选项之一
                    if q["correct_answer"] not in q["options"]:
                        print(f"Warning: Answer not in options: {q['correct_answer']}")
                        continue
                    
                    # 验证问题是否基于当前文档块
                    question_chunks = self._get_relevant_chunks(q["question"])
                    if not question_chunks or not any(chunk in question_chunks for chunk in chunks.split("\n")):
                        print(f"Warning: Question may not be based on current chunk: {q['question']}")
                        continue
                        
                    valid_questions.append(q)
                    print(f"成功生成第 {i+1} 个问题")
                    
                except Exception as e:
                    print(f"Error processing chunk {i+1}: {str(e)}")
                    continue
            
            if len(valid_questions) >= 5:
                print(f"Successfully generated {len(valid_questions)} valid questions")
                return valid_questions[:5]
            else:
                print(f"Only generated {len(valid_questions)} valid questions")
                # 如果问题不足，添加默认问题
                while len(valid_questions) < 5:
                    valid_questions.append(self._get_default_question())
                return valid_questions
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return [self._get_default_question() for _ in range(5)]
    
    def _get_default_question(self) -> Dict:
        """返回默认问题"""
        return {
            "question": "这是一个示例问题",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": "选项A",
            "explanation": "这是一个示例解释"
        }

    def generate_questions_directly(self, topic: str) -> List[Dict]:
        """直接基于主题生成问题，不需要上传文件"""
        try:
            print(f"正在为主题 '{topic}' 生成问题...")
            
            # 创建提示模板
            direct_template = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的问答游戏出题者。请基于给定的主题生成5个问答题目。
                每个问题必须包含：
                1. 问题文本
                2. 4个选项（使用"选项A"、"选项B"、"选项C"、"选项D"的格式）
                3. 正确答案（必须是选项之一）
                4. 解释说明

                请直接返回JSON格式的问题列表，格式如下：
                [
                    {
                        "question": "问题1",
                        "options": ["选项A", "选项B", "选项C", "选项D"],
                        "correct_answer": "选项A",
                        "explanation": "解释1"
                    }
                ]"""),
                ("user", f"主题：{topic}")
            ])
            
            # 生成问题
            print("正在调用语言模型生成问题...")
            response = self.llm.invoke(direct_template.format_messages())
            print(f"语言模型响应: {response.content}")
            
            # 提取并解析JSON
            json_str = self._extract_json_from_response(response.content)
            print(f"提取的JSON字符串: {json_str}")
            
            try:
                questions = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {str(e)}")
                raise ValueError(f"无法解析生成的问题: {str(e)}")
            
            # 验证问题格式
            if not isinstance(questions, list):
                print(f"响应不是列表格式: {type(questions)}")
                raise ValueError("生成的问题格式不正确")
            
            if len(questions) < 5:
                print(f"警告：只生成了 {len(questions)} 个问题，需要5个")
                # 如果问题数量不足，添加默认问题
                while len(questions) < 5:
                    questions.append(self._get_default_question())
            
            # 验证每个问题
            valid_questions = []
            for i, q in enumerate(questions):
                print(f"验证第 {i+1} 个问题...")
                # 检查必要字段
                if not all(k in q for k in ["question", "options", "correct_answer", "explanation"]):
                    print(f"问题缺少必要字段: {q}")
                    continue
                    
                # 检查选项格式
                if not isinstance(q["options"], list) or len(q["options"]) != 4:
                    print(f"选项格式无效: {q['options']}")
                    continue
                    
                # 检查答案格式
                if not q["correct_answer"].startswith("选项"):
                    print(f"答案格式无效: {q['correct_answer']}")
                    continue
                    
                # 确保答案是选项之一
                if q["correct_answer"] not in q["options"]:
                    print(f"答案不在选项中: {q['correct_answer']}")
                    continue
                
                valid_questions.append(q)
                print(f"第 {i+1} 个问题验证通过")
            
            if len(valid_questions) >= 5:
                print(f"成功生成 {len(valid_questions)} 个有效问题")
                return valid_questions[:5]
            else:
                print(f"只生成了 {len(valid_questions)} 个有效问题")
                # 如果问题不足，添加默认问题
                while len(valid_questions) < 5:
                    valid_questions.append(self._get_default_question())
                return valid_questions
            
        except Exception as e:
            print(f"生成问题时出错: {str(e)}")
            raise Exception(f"生成问题失败: {str(e)}") 