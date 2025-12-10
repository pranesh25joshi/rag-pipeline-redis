import os
from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from google import genai


load_dotenv()


def query_processing(query, collection_name="ragpdf",top_k=5):
    
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API = os.getenv("QDRANT_API")

    vector_db = QdrantVectorStore.from_existing_collection(
        embedding=embedding_model,
        url=QDRANT_URL,
        api_key=QDRANT_API,
        collection_name=collection_name
    )

    search_result = vector_db.similarity_search(query=query, k=top_k)

    context = "\n\n".join([r.page_content for r in search_result])

    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Context: {context}\n\nQuery: {query}\n\nProvide a detailed answer based on the context."
        )
        response = response.text
    except Exception as e:
        print(f"There is an error in the process: {e}")
        return "There was an error processing your request."


    return response
