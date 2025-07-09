import os
import uuid

from langchain_core.documents import Document
from tqdm import tqdm

from app import FaissEmbeddings
def add_metadata_db():
    config_url = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config_embedding.ini"))
    faiss_embeddings = FaissEmbeddings(config_url=config_url)
    metadata_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/law_names.txt"))
    documents = []
    documents_uuids = []
    with open(metadata_path) as f:
        total_lines = sum(1 for _ in f)
    with open(metadata_path) as f:
        for line in tqdm(f, total=total_lines, desc="Processing documents"):
            line = line.strip()
            file_one = Document(line)
            documents.append(file_one)
            uids = str(uuid.uuid4())
            documents_uuids.append(uids)
    faiss_embeddings.add_doc(documents, documents_uuids)
    print("Added {} documents".format(len(documents)))
    save_path = os.path.join(os.path.dirname(__file__), "../app/metadata_db")
    print("Saving metadata to {}".format(save_path))
    faiss_embeddings.save_to_file(save_path,"metadata_index")
    print("Saved metadata to {}".format(save_path))
def main():
    add_metadata_db()
if __name__ == "__main__":
    main()