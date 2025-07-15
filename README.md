[简体中文](./README_zh.md)|English
# Installation Guide
This project provides an intelligent agent for legal applications, offering knowledge-based Q&A functionality utilizing Faiss vector retrieval and LangChain.
1. Install Ollama locally as per the instructions on the official website (https://ollama.com/).  
2. Pull the desired LLM model and Embedding model using the following commands in your terminal:  
     ollama pull <llm_model_name>   # e.g., ollama pull llama3  
     ollama pull <embedding_model_name>   # e.g., ollama pull nomic-embed-text  
3. Navigate to the config directory of your project and edit the configuration file (e.g., config.yaml or config.json). Update the following settings:  
     - Set the API base URL to the local Ollama server (default: http://localhost:11434)  
     - Set the LLM model name to the one you pulled (e.g., "llama3")  
     - Set the Embedding model name to the one you pulled (e.g., "nomic-embed-text")  

## Using uv (Recommended)
---
1. Install uv  
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Run the program  
```bash
uv run run.py
#install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
#restart bash
nvm install
cd web/frontend
npm install
npm run dev
```
---
## Using Python

1. Install Python 3.12  
2. Install dependencies  
```bash
pip install -r requirements.txt
```
3. Run the program
```bash
python run.py
#install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
#restart bash
nvm install
cd web/frontend
npm install
npm run dev
```
---

