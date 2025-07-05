from bs4 import BeautifulSoup
import json
import re

def clean_html(raw_html):
    """
    去除HTML标签，保留纯文本
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    # 可选：去除多余空行
    text = re.sub(r'\n+', '\n', text)
    return text

def save_json(data, filename):
    """
    保存数据为JSON文件
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)