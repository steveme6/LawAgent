简体中文|[English](./README.md)  
本项目提供了一个用于法律的智能体，可以提供知识问答，采用faiss向量检索以及langchain。

# 快速使用
在使用之前请本地安装好ollama  
并且拉取一个LLM模型，Embedding模型，在config目录下修改api地址，以及模型名称。  
## 使用uv（推荐）

---
1. 安装 uv  
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 安装 git lfs 并拉取大文件  
```bash
git lfs install
git lfs pull
```

3. 运行项目  
```bash
uv run run.py
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
# 重启 bash
nvm install
cd web/frontend
npm install
npm run dev
```
---

## 使用 Python

1. 安装 Python 3.12  
2. 安装依赖  
```bash
pip install -r requirements.txt
```
3. 运行项目
```bash
python run.py
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
# 重启 bash
nvm install
cd web/frontend
npm install
npm run dev
```
