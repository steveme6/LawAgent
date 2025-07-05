import uuid
import json
import os
import glob
from langchain_community.docstore import InMemoryDocstore
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import faiss
from config import get_config
from typing import Optional


class FaissEmbeddings:
    def __init__(self, folder_path: Optional[str] = None):
        """初始化"""
        base_url = get_config("ollama", "BASE_URL", "config/config_embedding.ini")
        model = get_config("ollama", "MODEL", "config/config_embedding.ini")
        self.embeddings = OllamaEmbeddings(base_url=base_url, model=model)

        if folder_path:
            self.vectorstore = FAISS.load_local(
                folder_path=folder_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            index = faiss.IndexFlatL2(len(self.embeddings.embed_query("123")))
            self.vectorstore = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={}
            )

    def add_text(self, text: str, uid: str):
        """加入文本，测试用"""
        self.vectorstore.add_texts([text], uuid=uid)

    def add_doc(self, documents: list[Document], uuids: list[str]):
        """加入文档"""
        self.vectorstore.add_documents(documents=documents, ids=uuids)

    def delete_documents(self, uids: list[str]):
        """删除文档"""
        self.vectorstore.delete(uuids=uids)

    def research(self, text: str, k: int = 1, fil: dict = None):
        """检索函数"""
        results = self.vectorstore.similarity_search(query=text, k=k, filter=fil)
        return results

    def save_to_file(self, folder_path: str, save_name: str):
        """将向量存储保存到指定目录"""
        self.vectorstore.save_local(
            folder_path=folder_path,
            index_name=save_name  # 可自定义索引文件名
        )

    def load_from_file(self, folder_path: str):
        """从指定目录加载向量存储"""
        self.vectorstore = FAISS.load_local(
            folder_path=folder_path,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )

    def return_faiss_vectorstore(self):
        """返回向量库，用于更复杂操作"""
        return self.vectorstore

def main():
    """批量加载法律文档数据到向量数据库"""
    # 初始化 FaissEmbeddings
    faiss_embeddings = FaissEmbeddings()

    # 获取所有 JSON 文件
    json_files = glob.glob("../preprocessing/*.json")

    if not json_files:
        print("在 ../preprocessing/ 目录下没有找到 JSON 文件")
        return

    print(f"发现 {len(json_files)} 个 JSON 文件需要处理")

    all_documents = []
    all_uuids = []
    processed_count = 0
    failed_count = 0

    for json_file_path in json_files:
        filename = os.path.basename(json_file_path)
        print(f"\n正在处理: {filename}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换为 Document 对象列表
            current_documents = []
            current_uuids = []

            for item in data:
                doc = Document(
                    page_content=item['page_content'],
                    metadata=item['metadata']
                )
                current_documents.append(doc)
                current_uuids.append(str(uuid.uuid4()))

            # 立即添加当前文件的文档到向量数据库
            if current_documents:
                print(f"正在添加 {len(current_documents)} 个文档到向量数据库...")
                faiss_embeddings.add_doc(current_documents, current_uuids)
                print(f"成功添加 {len(current_documents)} 个文档")

                # 累计统计
                all_documents.extend(current_documents)
                all_uuids.extend(current_uuids)
                processed_count += 1
            else:
                print("该文件没有有效文档")

        except FileNotFoundError:
            print(f"文件不存在: {json_file_path}")
            failed_count += 1
        except json.JSONDecodeError:
            print(f"JSON 文件格式错误: {json_file_path}")
            failed_count += 1
        except Exception as e:
            print(f"处理文件 {filename} 时发生错误: {e}")
            failed_count += 1

    # 保存向量数据库到文件
    if all_documents:
        print(f"\n正在保存向量数据库...")
        try:
            faiss_embeddings.save_to_file("../data/faiss_db", "law_index")
            print("向量数据库已成功保存到 ../data/faiss_db/law_index")

            # 测试检索功能
            print("\n测试检索功能:")
            results = faiss_embeddings.research("不动产登记", k=3)
            for i, result in enumerate(results):
                print(f"结果 {i+1}: {result.page_content[:100]}...")
                print(f"法律名称: {result.metadata.get('law_name', '未知')}")
                print(f"分类: {result.metadata.get('category', '未知')}")
                print("-" * 50)

        except Exception as e:
            print(f"保存向量数据库时发生错误: {e}")
    else:
        print("没有成功加载任何文档")

    print(f"\n处理总结:")
    print(f"成功处理: {processed_count} 个文件")
    print(f"处理失败: {failed_count} 个文件")
    print(f"总文档数: {len(all_documents)} 个")

if __name__ == "__main__":
    main()