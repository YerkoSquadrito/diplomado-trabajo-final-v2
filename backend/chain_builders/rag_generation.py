from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from .global_llm_instances import global_llm
from langchain_core.runnables import Runnable
import os

def build_rag_chain(
        llm = global_llm,
        prompt = hub.pull("rlm/rag-prompt")
    ) -> Runnable:
    """
    Builds and returns a RAG (Retrieve, Answer, Generate) chain for generating responses based on a question and relevant documents. 
    This chain lacks of a retriever, therefore it's up to the user to provide the documents to the chain, or to modify the chain to include a retriever.
    This chain uses a prompt template from the hub. Again, it's up to the user to modify the prompt to fit their needs.

    Chain input must be a dictionary with:
    - question: The user question.
    - document: The retrieved documents

    Inputs:
        llm (ChatOpenAI): The language model to use. Defaults to GPT-3.5-turbo.
        prompt (Runnable): The prompt to use for the RAG pipeline. Defaults to a hub prompt.
    
    Returns:
        rag_chain (RAGPipeline): The RAG pipeline for generating responses.
    """

    # Chain
    rag_chain = prompt | llm | StrOutputParser()

    return rag_chain