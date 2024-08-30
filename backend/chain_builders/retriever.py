from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
import os

def build_retriever():
    """
    Builds and returns a retriever object for document retrieval. This retriever is built using Chroma as a vector store and OpenAI embeddings. The vector store is loaded with the parsing of html documents from Accenture's Internal Web Pages and other PDFs.

    Returns:
        retriever: A retriever object for document retrieval.
    """
    
    # Set embeddings
    embd = AzureOpenAIEmbeddings(deployment=os.getenv('AZURE_EMBEDDINGS_DEPLOYMENT_NAME'))

    # Add to vectorstore
    vectorstore = Chroma(
        collection_name="rag-chroma",
        embedding_function=embd,
        persist_directory="./kdb/"
    )
    retriever = vectorstore.as_retriever()
    return retriever