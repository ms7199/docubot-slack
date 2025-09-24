import os, hashlib
from datetime import datetime
from typing import List
import PyPDF2
from langchain.schema import Document
from embeddings import load_embeddings
from utils import create_document_hash

# chunking from langchain
from langchain.text_splitter import RecursiveCharacterTextSplitter

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {e}")
        return ""

def process_pdf_files(pdf_directory: str = "./pdfs") -> List[Document]:
    documents = []
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory, exist_ok=True)
        print(f"Please add your PDF files to {pdf_directory}")
        return documents

    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return documents

    for filename in pdf_files:
        pdf_path = os.path.join(pdf_directory, filename)
        print(f"Processing {filename}...")
        text = extract_text_from_pdf(pdf_path)
        if text.strip():
            doc = Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "file_path": pdf_path,
                    "processed_at": datetime.now().isoformat()
                }
            )
            documents.append(doc)
            print(f"Processed {filename}")
        else:
            print(f"No text found in {filename}")
    return documents

def chunk_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200):
    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len)
    chunked = []
    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                chunked.append(Document(page_content=chunk, metadata={**doc.metadata, "chunk_id": i, "total_chunks": len(chunks)}))
    return chunked

def store_documents(index, embeddings, documents):
    if not index or not embeddings or not documents:
        print("Cannot store documents: missing index, embeddings, or documents")
        return

    vectors = []
    for doc in documents:
        embedding = embeddings.embed_query(doc.page_content)
        doc_hash = create_document_hash(doc.page_content)
        vector_id = f"{doc.metadata['source']}_{doc.metadata.get('chunk_id',0)}_{doc_hash[:8]}"
        metadata = {
            "source": doc.metadata["source"],
            "chunk_id": str(doc.metadata.get("chunk_id", 0)),
            "content_preview": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content
        }
        vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1 if vectors else 1}")

    print(f"Stored {len(vectors)} chunks in Pinecone")
