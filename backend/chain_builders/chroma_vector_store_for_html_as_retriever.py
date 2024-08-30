from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import BSHTMLLoader
from langchain.schema import Document
from langchain_community.document_loaders import UnstructuredPDFLoader
import os

def build_retriever():
    """
    Builds and returns a retriever object for document retrieval. This retriever is built using Chroma as a vector store and OpenAI embeddings. The vector store is loaded with the parsing of html documents from Accenture's Internal Web Pages and other PDFs.

    Returns:
        retriever: A retriever object for document retrieval.
    """
    # Set embeddings
    embd = AzureOpenAIEmbeddings(azure_deployment=os.getenv('AZURE_EMBEDDINGS_DEPLOYMENT_NAME'))

    # Docs to index
    urls = [
        "./kdb/benefits_360.html",
        "./kdb/nuestra_cultura.html",
        "./kdb/recursos_humanos.html",
        "./kdb/service_and_support_finanzas.html",
        "./kdb/service_and_support_marketing.html",
        "./kdb/service_and_support_workplace.html",
        "./kdb/service_and_support_legales.html",
        "./kdb/LEARNING AT ACCENTURE CHILE.pdf"
    ]

    # Load
    def loader(file_path):
        if file_path.endswith(".html"):
            return BSHTMLLoader(file_path, open_encoding="utf-8")
        elif file_path.endswith(".pdf"):
            return UnstructuredPDFLoader(file_path)
    docs = [loader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    docs_list = [Document(page_content=doc.page_content.replace('\n\n\n',''))  for doc in docs_list if doc]

    # Split
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=300
    )
    doc_splits = text_splitter.split_documents(docs_list)

    # Add to vectorstore
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=embd,
    )
    retriever = vectorstore.as_retriever()
    return retriever