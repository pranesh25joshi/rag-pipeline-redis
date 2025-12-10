from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from langchain_community.document_loaders import PyMuPDFLoader


load_dotenv()


def file_embedding_and_loading(file_path, collection_name="ragpdf"):
    
    loader = PyMuPDFLoader(file_path=file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400
    )
    chunk = text_splitter.split_documents(docs)

    embedding_model= GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API = os.getenv("QDRANT_API")

    vector_db = QdrantVectorStore.from_documents(
        documents=chunk,
        embedding=embedding_model,
        url=QDRANT_URL,
        api_key=QDRANT_API,
        collection_name=collection_name
    )

    print(f"Processed and stored {len(chunk)} chunks from {file_path} in Qdrant.")

    os.remove(file_path)

    return "File processed and indexed successfully."
