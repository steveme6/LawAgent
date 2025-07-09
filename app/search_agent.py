import asyncio
import os
import re
from app import OriginAgent
from app import FaissEmbeddings

def extract_output(model_output):
    match = re.search(r'</think>\s*(.*?)$', model_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

class SearchAgent:
    def __init__(self,folder_path: str,index_name: str,database_url:str,config_url:str):
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config_embedding.ini"))
        self.embedding = FaissEmbeddings(config_path,folder_path,index_name)
        self.prompt = "你是一个生成查询的智能体，你只需要输出查询的一个关键词即可，如用户输入“鹦鹉法规”，你输出：鹦鹉，用户输入:{input}"
        self.origin = OriginAgent(config_url=config_url,database_url=database_url,prompt=self.prompt)
    async def search(self,query,fil: dict = None):
        chain = self.origin.return_chain()
        result = chain.invoke(query)
        output = extract_output(result)
        print(str(output))
        new_output = str(output)
        search_result = self.embedding.research(new_output,k=128718,fil=fil)
        first_results = []
        page_results = []

        for i in range(len(search_result)):
            if new_output in search_result[i][0].metadata.get("law_name","") and new_output in search_result[i][0].page_content:
                first_results.append(search_result[i][0])
            elif new_output not in search_result[i][0].metadata.get("law_name","") and new_output in search_result[i][0].page_content:
                page_results.append(search_result[i][0])
        return [first_results,page_results]


async def main():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config.ini"))
    database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../history_db/history.db"))
    search_agent = SearchAgent("/home/admin/LawAgent/app/faiss_db","law_index",config_url=config_path,database_url=database_path)
    results=await search_agent.search(" 国家重点保护野生动物驯养繁殖许可证管理办法")
    if results and len(results)<3:
        for i in range (len(results)):
            print(results[i])
    elif results and len(results)>3:
        for i in range (3):
            print(results[i])
if __name__ == "__main__":
    asyncio.run(main())