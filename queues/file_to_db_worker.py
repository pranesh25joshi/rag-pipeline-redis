from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import tempfile
from langchain_community.document_loaders import PyMuPDFLoader


load_dotenv()


def file_embedding_and_loading(file_content, filename, collection_name="ragpdf"):
    """
    Process uploaded file content and store embeddings in Qdrant.
    
    Args:
        file_content: Binary content of the uploaded file
        filename: Original filename
        collection_name: Qdrant collection name
    """
    temp_file_path = None
    try:
        # Save file content to a temporary file on the worker
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Load and process the PDF
        loader = PyMuPDFLoader(file_path=temp_file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=400
        )
        chunk = text_splitter.split_documents(docs)

        embedding_model = GoogleGenerativeAIEmbeddings(
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

        print(f"Processed and stored {len(chunk)} chunks from {filename} in Qdrant collection '{collection_name}'.")

        return f"File '{filename}' processed and indexed successfully. {len(chunk)} chunks stored."
    except Exception as e:
        print(f"Error processing file {filename}: {e}")
        return f"Error processing file: {e}"
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)