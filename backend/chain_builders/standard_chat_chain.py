from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseChatModel
from .global_llm_instances import global_llm
import os

def build_standard_chat_chain(
    prompt: ChatPromptTemplate,
    llm = global_llm,
) -> Runnable:
    """
    Builds a question re-writer chain that converts an input question to a better version optimized for vectorstore retrieval.
    
    Chain input can be a string or a dictionary with:
    - question: The user question.
    
    Inputs:
    chat_prompt_template (ChatPromptTemplate): The chat prompt template.
    llm (ChatOpenAI): The language model to use. Defaults to gpt-4o-mini.
    
    Returns:
    The chat chain.
    """
    chain = prompt | llm | StrOutputParser()
    return chain