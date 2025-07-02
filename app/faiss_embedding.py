from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
import asyncio

from nltk.data import retrieve

from config import get_config
class FaissEmbeddings:
    def __init__(self):
        base_url = get_config("ollama","MODEL","../config/config_embedding.ini")
        model = get_config("ollama","MODEL","../config/model_embedding.ini")
        self.embeddings = OllamaEmbeddings(base_url=base_url,model=model)
        self.vectorstore = InMemoryVectorStore(embedding=self.embeddings)
    def add_text(self,text:str):
        self.vectorstore.add_texts(text)
    def add_document(self,texts:list):
        self.vectorstore.add_documents(texts)
    def retriever_text(self,text:str):
        retrieve_doc = self.vectorstore.as_retriever()
        return 
