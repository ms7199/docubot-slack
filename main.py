import os
from dotenv import load_dotenv
from pinecone_client import init_pinecone
from embeddings import load_embeddings
from pdf_processor import process_pdf_files, chunk_documents, store_documents
from slack_app import create_slack_app
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv(".env")

INDEX_NAME = "pdf-knowledge-base"
DIMENSION = 384

def main():
    # init pinecone
    pc, index = init_pinecone(INDEX_NAME, DIMENSION)

    # load embeddings
    embeddings = load_embeddings()

    # initialize KB if possible
    if embeddings and index:
        docs = process_pdf_files("./pdfs")
        if docs:
            chunks = chunk_documents(docs)
            if chunks:
                store_documents(index, embeddings, chunks)
                print("Knowledge base initialized.")
            else:
                print("No chunks created.")
        else:
            print("No PDF documents found to initialize.")
    else:
        print("Skipping KB init: missing embeddings or index.")

    # create slack app and start
    app = create_slack_app(index, embeddings)
    try:
        print("Starting Slack app...")
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    except Exception as e:
        print("Error starting Slack app:", e)

if __name__ == "__main__":
    main()