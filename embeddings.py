from langchain_huggingface import HuggingFaceEmbeddings

def load_embeddings(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
    try:
        emb = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={"device": device})
        print("Embedding model loaded successfully")
        return emb
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        return None
