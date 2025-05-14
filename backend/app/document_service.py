from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
import os
from typing import List, Optional
import magic

class DocumentService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="llama2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vectorstore = Chroma(
            persist_directory="./data",
            embedding_function=self.embeddings
        )

    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)

    def process_document(self, file_path: str) -> None:
        """处理文档并存储到向量数据库"""
        file_type = self._get_file_type(file_path)
        
        # 根据文件类型选择加载器
        if file_type == 'application/pdf':
            loader = PyPDFLoader(file_path)
        elif file_type in ['text/plain', 'text/markdown']:
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

        # 加载文档
        documents = loader.load()
        
        # 分割文档
        splits = self.text_splitter.split_documents(documents)
        
        # 存储到向量数据库
        self.vectorstore.add_documents(splits)
        self.vectorstore.persist()

    def search_documents(self, query: str, k: int = 3) -> List[str]:
        """搜索相关文档片段"""
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs] 