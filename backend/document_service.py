from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
import os
from typing import List, Optional, Dict
import magic
import chromadb
from chromadb.config import Settings
from datetime import datetime, timedelta

class DocumentService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="llama2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.Client(Settings(
            persist_directory="./data",
            anonymized_telemetry=False
        ))
        
        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 文档缓存
        self._cache: Dict[str, Dict] = {}
        self._cache_expiry = timedelta(hours=1)  # 缓存过期时间

    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)

    def _get_cache_key(self, content: str) -> str:
        """生成缓存键"""
        return f"doc_{hash(content)}"

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        timestamp = cache_entry.get('timestamp')
        if not timestamp:
            return False
        return datetime.now() - timestamp < self._cache_expiry

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
        for i, split in enumerate(splits):
            self.collection.add(
                documents=[split.page_content],
                metadatas=[{"source": file_path}],
                ids=[f"{file_path}_{i}"]
            )

    def search_documents(self, query: str, k: int = 3) -> List[str]:
        """搜索相关文档片段"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return results['documents'][0] if results['documents'] else []

    def process_document_with_cache(self, content: str, doc_type: str) -> str:
        """处理文档并返回文档ID"""
        cache_key = self._get_cache_key(content)
        
        # 检查缓存
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            return self._cache[cache_key]['doc_id']
        
        # 处理新文档
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 存储到 ChromaDB
        self.collection.add(
            documents=[content],
            metadatas=[{"type": doc_type}],
            ids=[doc_id]
        )
        
        # 更新缓存
        self._cache[cache_key] = {
            'doc_id': doc_id,
            'timestamp': datetime.now()
        }
        
        return doc_id

    def search_documents_with_cache(self, query: str, n_results: int = 3) -> List[str]:
        """搜索相关文档内容"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results or not results['documents']:
            return []
            
        return results['documents'][0]

    def clear_expired_cache(self):
        """清理过期的缓存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if not self._is_cache_valid(entry)
        ]
        for key in expired_keys:
            del self._cache[key] 