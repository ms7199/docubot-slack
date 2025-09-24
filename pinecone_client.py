from pinecone import Pinecone, ServerlessSpec
import os

def init_pinecone(index_name: str, dimension: int):
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    print("Pinecone client initialized", pc)

    index = None
    try:
        existing_indexes = [idx["name"] for idx in pc.list_indexes()]
        if index_name not in existing_indexes:
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"Created new index: {index_name}")
        index = pc.Index(index_name)
        print(f"Connected to index: {index_name}")
    except Exception as e:
        print(f"Pinecone setup error: {e}")
        index = None

    return pc, index
