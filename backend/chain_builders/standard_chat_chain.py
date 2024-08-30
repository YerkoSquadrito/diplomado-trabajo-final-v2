from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
import os

def build_standard_chat_chain(
    prompt: ChatPromptTemplate,
    llm = AzureChatOpenAI(
        deployment_name=os.getenv('AZURE_COMPLETIONS_DEPLOYMENT_NAME'), 
        model_version=os.getenv('AZURE_COMPLETIONS_MODEL_VERSION'), 
        temperature=0 
    ),
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