import asyncio
import re
from app import OriginAgent
from app import FaissEmbeddings

def extract_output(model_output):
    match = re.search(r'</think>\s*(.*?)$', model_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

class SearchAgent:
    def __init__(self,folder_path: str,index_name: str):
        self.embedding = FaissEmbeddings(folder_path,index_name)
        self.prompt = "你是一个生成查询的智能体，你只需要输出查询的一个关键词即可，如用户输入“鹦鹉法规”，你输出：鹦鹉，用户输入:{input}"
        self.origin = OriginAgent(prompt=self.prompt)
    async def search(self,query,fil: dict = None):
        chain = self.origin.return_chain()
        result = chain.invoke(query)
        output = extract_output(result)
        print(str(output))
        new_output = str(output)
        search_result = self.embedding.research(new_output,k=7000,fil=fil)
        results = []
        for i in range(len(search_result)):
            if new_output in search_result[i][0].metadata.get("law_name",""):
                results.append(search_result[i][0])
            elif new_output in search_result[i][0].page_content:
                results.append(search_result[i][0])
        return results


async def main():
    search_agent = SearchAgent("/home/admin/LawAgent/app/faiss_db","law_index")
    results=await search_agent.search(" 试用期最多可以约定多久")
    if results and len(results)<3:
        for i in range (len(results)):
            print(results[i])
    elif results and len(results)>3:
        for i in range (3):
            print(results[i])
if __name__ == "__main__":
    asyncio.run(main())