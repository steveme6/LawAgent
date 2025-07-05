import re
import json
import os
import glob
from langchain_core.documents import Document
from typing import Dict, List

class LawCleaner:
    def __init__(self):
        self.article_pattern = re.compile(r'(第[一二三四五六七八九十百千0-9]+条)')
        self.chapter_pattern = re.compile(r'(第[一二三四五六七八九十百千0-9]+章)')

    def clean_text(self, text: str) -> str:
        """清理文本内容，处理换行符和空白字符"""
        try:
            # 替换\n\r和\r\n为标准换行符
            text = text.replace('\n\r', '\n').replace('\r\n', '\n').replace('\r', '\n')
            # 替换全角空格为半角空格
            text = text.replace('　', ' ')
            # 规范化空白字符，但保留换行符
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                # 去掉每行首尾空格，但保留行间结构
                cleaned_line = re.sub(r'[ \t]+', ' ', line.strip())
                cleaned_lines.append(cleaned_line)
            return '\n'.join(cleaned_lines).strip()
        except Exception as e:
            print(f"[ERROR] clean_text: {e}")
            return str(text)

    def split_articles(self, text: str) -> List[Dict[str, str]]:
        """
        根据“第x条”拆分法律文本，并提取章节信息。
        """
        has_articles = self.article_pattern.search(text)
        if not has_articles:
            return [{"text": text, "article_number": "", "chapter": ""}]

        articles = []
        buffer = []
        lines = text.split('\n')
        current_chapter = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            chapter_match = self.chapter_pattern.match(line)
            if chapter_match:
                current_chapter = chapter_match.group(1)

            art_match = self.article_pattern.match(line)
            if art_match:
                if buffer:
                    article_text = '\n'.join(buffer).strip()
                    article_number_match = self.article_pattern.search(article_text)
                    article_number = article_number_match.group(1) if article_number_match else ""
                    articles.append({
                        "text": article_text,
                        "article_number": article_number,
                        "chapter": current_chapter
                    })
                buffer = [line]
            else:
                buffer.append(line)
        
        if buffer:
            article_text = '\n'.join(buffer).strip()
            article_number_match = self.article_pattern.search(article_text)
            article_number = article_number_match.group(1) if article_number_match else ""
            articles.append({
                "text": article_text,
                "article_number": article_number,
                "chapter": current_chapter
            })
            
        return articles

    def clean_laws_from_category(self, category: Dict, is_split_file: bool = False) -> List[Document]:
        documents = []
        category_name = category.get('category_name', '')
        for law in category.get('laws', []):
            law_name = law.get('title') or law.get('metadata', {}).get('完整标题') or law.get('metadata', {}).get('title') or ''
            meta = law.get('metadata', {})
            law_content = law.get('content', '')
            if not law_content or not law_name:
                print(f"[WARN] 跳过空内容或无名法规: {law}")
                continue

            cleaned_content = self.clean_text(law_content)
            articles = self.split_articles(cleaned_content)

            for article_info in articles:
                article_text = article_info["text"]
                # 如果拆分后只有一个文档且内容为空，则跳过
                if len(articles) == 1 and not article_text:
                    continue

                metadata = {
                    "law_name": law_name,
                    "category": category_name,
                    "article_number": article_info["article_number"],
                    "chapter": article_info["chapter"]
                }
                if is_split_file:
                    full_title = meta.get('完整标题') if isinstance(meta, dict) else None
                    if full_title:
                        metadata["完整标题"] = full_title

                doc = Document(page_content=article_text, metadata=metadata)
                debug_info = f"添加法条: {law_name}"
                if article_info['chapter']:
                    debug_info += f" 章节: {article_info['chapter']}"
                if article_info['article_number']:
                    debug_info += f" 条文: {article_info['article_number']}"
                debug_info += f" 长度: {len(article_text)}"
                print(f"[DEBUG] {debug_info}")
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

    # 输入目录：data/raw
    input_dir = "../data/raw"

    # 输出目录：当前 preprocessing 目录
    output_dir = "."

    # 获取所有 JSON 文件
    json_files = glob.glob(os.path.join(input_dir, "*.json"))

    print(f"[INFO] 发现 {len(json_files)} 个JSON文件需要处理")

    processed_count = 0
    failed_count = 0

    for input_file in json_files:
        # 获取文件名（不包含路径和扩展名）
        filename = os.path.basename(input_file)
        filename_without_ext = os.path.splitext(filename)[0]

        # 生成输出文件名
        output_filename = f"{filename_without_ext}_cleaned.json"
        output_path = os.path.join(output_dir, output_filename)

        print(f"\n[INFO] 正在处理: {filename}")

        try:
            # 处理文件并获取文档
            with open(input_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            current_documents = []
            if isinstance(raw_data, dict) and 'laws' in raw_data:
                print(f"[DEBUG] 处理分类: {raw_data.get('category_name', '')}")
                docs = cleaner.clean_laws_from_category(raw_data, is_split_file=False)
                current_documents.extend(docs)
            elif isinstance(raw_data, list) and raw_data and 'laws' in raw_data[0]:
                for idx, category in enumerate(raw_data):
                    print(f"[DEBUG] 处理分类: {category.get('category_name', '')} (第{idx+1}类)")
                    docs = cleaner.clean_laws_from_category(category, is_split_file=False)
                    current_documents.extend(docs)
            else:
                print("[ERROR] 输入数据不是期望的分类-法规列表结构")
                continue

            print(f"[DEBUG] 当前文件生成 {len(current_documents)} 个Document")

            # 检查是否需要拆分文件（条文数大于100）
            if len(current_documents) > 100:
                print(f"[INFO] 文档数量 {len(current_documents)} 超过100条，开始拆分文件")

                # 计算需要拆分成多少个文件
                chunk_size = 100
                num_chunks = (len(current_documents) + chunk_size - 1) // chunk_size

                # 重新处理原始数据，为拆分文件生成包含完整标题的文档
                split_documents = []
                if isinstance(raw_data, dict) and 'laws' in raw_data:
                    docs = cleaner.clean_laws_from_category(raw_data, is_split_file=True)
                    split_documents.extend(docs)
                elif isinstance(raw_data, list) and raw_data and 'laws' in raw_data[0]:
                    for category in raw_data:
                        docs = cleaner.clean_laws_from_category(category, is_split_file=True)
                        split_documents.extend(docs)

                # 转换为可序列化的格式
                split_output_data = [
                    {"page_content": doc.page_content, "metadata": doc.metadata}
                    for doc in split_documents
                ]

                for i in range(num_chunks):
                    start_idx = i * chunk_size
                    end_idx = min((i + 1) * chunk_size, len(split_output_data))
                    chunk_data = split_output_data[start_idx:end_idx]

                    # 生成拆分文件名
                    if i == 0:
                        # 第一个文件保持原名
                        chunk_output_path = output_path
                    else:
                        # 后续文件添加_(1), _(2)等后缀
                        chunk_filename = f"{filename_without_ext}_cleaned_({i}).json"
                        chunk_output_path = os.path.join(output_dir, chunk_filename)

                    # 保存拆分后的文件
                    with open(chunk_output_path, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, ensure_ascii=False, indent=2)

                    print(f"[SUCCESS] 拆分文件 {i+1}/{num_chunks}: {os.path.basename(chunk_output_path)} (包含 {len(chunk_data)} 条Document)")

                print(f"[SUCCESS] 文件拆分完成，共生成 {num_chunks} 个文件")
            else:
                # 文档数量不超过100，正常保存单个文件（不包含完整标题）
                output_data = [
                    {"page_content": doc.page_content, "metadata": doc.metadata}
                    for doc in current_documents
                ]

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                print(f"[SUCCESS] 成功处理: {filename} -> {output_filename}")
                print(f"[SUCCESS] 输出 {len(output_data)} 条Document")

            processed_count += 1
        except Exception as e:
            print(f"[ERROR] 处理文件 {filename} 时出错: {e}")
            failed_count += 1
            continue

    print(f"\n[SUMMARY] 批量处理完成:")
    print(f"[SUMMARY] 成功处理: {processed_count} 个文件")
    print(f"[SUMMARY] 处理失败: {failed_count} 个文件")
    print(f"[SUMMARY] 总文件数: {len(json_files)} 个文件")
