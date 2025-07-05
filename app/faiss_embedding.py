import uuid
from langchain_community.docstore import InMemoryDocstore
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import faiss
from app.config import get_config
from typing import Optional



class FaissEmbeddings:
    def __init__(self, folder_path: Optional[str] = None,index_name: Optional[str] = None):
        """初始化"""
        base_url = get_config("ollama", "BASE_URL", "./config/config_embedding.ini")
        model = get_config("ollama", "MODEL", "./config/config_embedding.ini")
        self.embeddings = OllamaEmbeddings(base_url=base_url, model=model)

        if folder_path and index_name:
            self.vectorstore = FAISS.load_local(
                folder_path=folder_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
                index_name=index_name,
            )
        else:
            embedding_dim = len(self.embeddings.embed_query("test"))
            index = faiss.IndexHNSWFlat(embedding_dim, 32)
            self.vectorstore = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={}
            )

    def add_text(self, text: str,uid:str):
        """加入文本，测试用"""
        self.vectorstore.add_texts([text], uuid=uid)

    def add_doc(self, documents: list[Document], uuids: list[str]):
        """加入文档"""
        self.vectorstore.add_documents(documents=documents, ids=uuids)

    def delete_documents(self, uids: list[str]):
        """删除文档"""
        self.vectorstore.delete(uuids=uids)

    def research(self, text: str, k: int = 1, fil: str = None):
        """检索函数"""
        results = self.vectorstore.similarity_search_with_score(query=text, k=k, filter=fil)
        return results

    def save_to_file(self, folder_path: str,save_name: str):
        """将向量存储保存到指定目录"""
        self.vectorstore.save_local(
            folder_path=folder_path,
            index_name=save_name  # 可自定义索引文件名
        )

    def load_from_file(self, folder_path: str,index_name: str):
        """从指定目录加载向量存储"""
        self.vectorstore = FAISS.load_local(
            folder_path=folder_path,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True,
            index_name=index_name
        )

    def return_faiss_vectorstore(self):
        """返回向量库，用于更复杂操作"""
        return self.vectorstore

def main():
    """测试"""
    faiss_embeddings = FaissEmbeddings()
    faiss_embeddings.add_text("LangChain is the framework for building context-aware reasoning applications", str(
        uuid.uuid4()))
    #faiss_embeddings.save_to_file("./","db_faiss")
    results=faiss_embeddings.research("langchain")
    print(results[0].page_content)

    """测试相关函数"""
    """
    def add_text(self,text:str):
        self.vectorstore.add_texts([text])
    def add_document(self,texts:list):
        self.vectorstore.add_documents(texts)
    def retriever_text(self,text:str):
        retrieve_a = self.vectorstore.as_retriever()
        return retrieve_a.invoke(text)
    """
    """
    document_1 = Document(
    page_content="I had chocolate chip pancakes and scrambled eggs for breakfast this morning.",
    metadata={"source": "tweet"},
    )
    document_2 = Document()
    documents = [document_1, document_2]
    uuids = [str(uuid4()) for _ in range(len(documents))]
    """



"""embeddings测试main"""
"""
def main():
    text = "LangChain is the framework for building context-aware reasoning applications"
    faiss_embeddings = FaissEmbeddings()
    faiss_embeddings.add_text(text)
    result = faiss_embeddings.retriever_text("What is LangChain?")
    print(result[0].page_content)
    
"""

if __name__ == "__main__":
    main()