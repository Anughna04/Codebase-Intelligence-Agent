import os
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from .ast_parser import PythonASTParser

class GlobalCodeContext:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.parser = PythonASTParser()
        # Initialize Gemini embeddings. Requires GOOGLE_API_KEY in env.
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.vector_store = None

    def build_index_for_repo(self):
        """Walks the repository, chunks Python files, and builds the FAISS index from scratch dynamically."""
        print(f"Building dynamic FAISS index for: {self.repo_path}...")
        all_chunks = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common ignores to prevent noise/errors
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules', '.venv']]
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    chunks = self.parser.parse_file(full_path)
                    for chunk in chunks:
                        metadata = {
                            "file_path": chunk["file_path"],
                            "entity_name": chunk["entity_name"],
                            "entity_type": chunk["entity_type"],
                            "start_line": chunk["start_line"],
                            "end_line": chunk["end_line"]
                        }
                        # Prepend entity type and name to content for better retrieval scoring
                        content_desc = f"{chunk['entity_type']} {chunk['entity_name']} defined in {chunk['file_path']}:\n\n{chunk['code_content']}"
                        doc = Document(page_content=content_desc, metadata=metadata)
                        all_chunks.append(doc)

        if not all_chunks:
            print("No indexable Python code found.")
            return

        print(f"Embedding {len(all_chunks)} semantic chunks into FAISS...")
        # Since it builds dynamically on run as requested, no persistence to disk
        self.vector_store = FAISS.from_documents(all_chunks, self.embeddings)
        print(f"Successfully built FAISS index with {len(all_chunks)} vectors.")

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """Performs similarity retrieval on the dynamic FAISS index."""
        if not self.vector_store:
            self.build_index_for_repo()
            
        if not self.vector_store: # Double-check after attempt
            return []

        return self.vector_store.similarity_search(query, k=top_k)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    ctx = GlobalCodeContext(os.getcwd())
    ctx.build_index_for_repo()
    results = ctx.search("parser implementation", top_k=2)
    for res in results:
        print(res.metadata["file_path"], "->", res.metadata["entity_name"])
