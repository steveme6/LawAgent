[简体中文](./README_zh.md)|English
# Installation Guide
This project provides an intelligent agent for legal applications, offering knowledge-based Q&A functionality utilizing Faiss vector retrieval and LangChain.

## Using uv (Recommended)

1. Install uv  
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Run the program  
```bash
uv run main.py
```

## Using Python

1. Install Python 3.12  
2. Install dependencies  
```bash
pip install -r requirements.txt
```

3. Run the program  
```bash
python main.py
```

---

To start the frontend, go to the `web/frontend` directory and run the following commands to install dependencies and start the development server:

```bash
cd web/frontend
npm install
npm run dev
```

---
