import re
import json
import hashlib
import html
import os
from bs4 import BeautifulSoup
from langchain.schema import Document
from typing import Dict, List

class LawCleaner:
    def __init__(self):
        self.article_pattern = re.compile(r'(第[一二三四五六七八九十百千0-9]+条)')
        self.chapter_pattern = re.compile(r'(第[一二三四五六七八九十百千0-9]+章[^\n]*)')
        self.section_pattern = re.compile(r'(第[一二三四五六七八九十百千0-9]+节[^\n]*)')
        self.processed_ids = set()

    def clean_html(self, html_text: str) -> str:
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            text = html.unescape(text)
            text = text.replace('　', ' ')
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            print(f"[ERROR] clean_html: {e}")
            return str(html_text)

    def split_articles(self, text: str) -> List[tuple]:
        articles = []
        current_chapter = ""
        current_section = ""
        buffer = []
        article_number = ""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            chap_match = self.chapter_pattern.match(line)
            if chap_match:
                current_chapter = chap_match.group(1)
                continue
            sec_match = self.section_pattern.match(line)
            if sec_match:
                current_section = sec_match.group(1)
                continue
            art_match = self.article_pattern.match(line)
            if art_match:
                if buffer and article_number:
                    articles.append((current_chapter, current_section, ''.join(buffer).strip()))
                article_number = art_match.group(1)
                buffer = [line]
            else:
                buffer.append(line)
        if buffer and article_number:
            articles.append((current_chapter, current_section, ''.join(buffer).strip()))
        return articles

    def generate_id(self, law_name: str, article_number: str, content: str) -> str:
        content_hash = hashlib.md5(f"{law_name}_{article_number}_{content[:100]}".encode('utf-8')).hexdigest()
        return content_hash

    def clean_laws_from_category(self, category: Dict) -> List[Document]:
        documents = []
        category_name = category.get('category_name', '')
        for law in category.get('laws', []):
            law_name = law.get('title') or law.get('metadata', {}).get('完整标题') or law.get('metadata', {}).get('title') or ''
            law_url = law.get('url', '')
            meta = law.get('metadata', {})
            law_content = law.get('content', '')
            if not isinstance(law_content, str):
                if isinstance(law_content, dict):
                    law_content = law_content.get('text') or law_content.get('zh') or next(iter(law_content.values()), '')
                else:
                    law_content = str(law_content)
            if not law_content or not law_name:
                print(f"[WARN] 跳过空内容或无名法规: {law}")
                continue
            cleaned_content = self.clean_html(law_content)
            articles = self.split_articles(cleaned_content)
            if not articles:
                articles = [("", "", cleaned_content)]
            for chapter, section, article_text in articles:
                article_number_match = self.article_pattern.search(article_text)
                article_number = article_number_match.group(1) if article_number_match else ""
                doc_id = self.generate_id(law_name, article_number, article_text)
                if doc_id in self.processed_ids:
                    print(f"[DEBUG] 跳过重复: {doc_id}")
                    continue
                self.processed_ids.add(doc_id)
                metadata = {
                    "law_name": law_name,
                    "chapter": chapter,
                    "section": section,
                    "article_number": article_number,
                    "url": law_url,
                    "id": doc_id,
                    "source": "pkulaw",
                    "category": category_name
                }
                if isinstance(meta, dict):
                    for k, v in meta.items():
                        if k not in metadata:
                            metadata[k] = v
                doc = Document(page_content=article_text, metadata=metadata)
                print(f"[DEBUG] 添加法条: {law_name} {article_number} 长度: {len(article_text)}")
                documents.append(doc)
        return documents

    def clean_laws_file(self, input_path: str, output_path: str) -> None:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] 读取输入文件失败: {e}")
            return
        all_documents = []
        if isinstance(raw_data, dict) and 'laws' in raw_data:
            print(f"[DEBUG] 处理分类: {raw_data.get('category_name', '')}")
            docs = self.clean_laws_from_category(raw_data)
            all_documents.extend(docs)
        elif isinstance(raw_data, list) and raw_data and 'laws' in raw_data[0]:
            for idx, category in enumerate(raw_data):
                print(f"[DEBUG] 处理分类: {category.get('category_name', '')} (第{idx+1}类)")
                docs = self.clean_laws_from_category(category)
                all_documents.extend(docs)
        else:
            print("[ERROR] 输入数据不是期望的分类-法规列表结构")
            return
        print(f"[DEBUG] 总共生成 {len(all_documents)} 个Document")
        output_data = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in all_documents
        ]
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 清洗完成，输出 {len(output_data)} 条Document到 {output_path}")
        except Exception as e:
            print(f"[ERROR] 写入输出文件失败: {e}")

if __name__ == "__main__":
    cleaner = LawCleaner()
    cleaner.clean_laws_file(
        "laws_xianfa_2552.json",  # 你的测试文件名
        "vector_data/processed/laws_cleaned.json"
    )
