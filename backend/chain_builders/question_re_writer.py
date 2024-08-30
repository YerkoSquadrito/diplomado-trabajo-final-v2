from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseChatModel
import os

# Prompt
system_prompt = """You are a question re-writer that converts an input question to a better version that is optimized \n 
for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "Here is the initial question: \n\n {question} \n Formulate an improved question"),
    ]
)

def build_question_re_writer_chain(
        llm = AzureChatOpenAI(
            deployment_name=os.getenv('AZURE_COMPLETIONS_DEPLOYMENT_NAME'), 
            model_version=os.getenv('AZURE_COMPLETIONS_MODEL_VERSION'), 
            temperature=0 
        ),
        prompt: ChatPromptTemplate = re_write_prompt
) -> Runnable:
    """
    Builds a question re-writer chain that converts an input question to a better version optimized for vectorstore retrieval.
    
    Chain input can be a string or a dictionary with:
    - question: The user question.
    
    Inputs:
        llm (ChatOpenAI): The language model to use. Defaults to gpt-4o-mini.
        system_prompt (str): The system prompt for the re-writer. Defaults to a simple question re-writing prompt.
    
    Returns:
        The question re-writer chain.
    """

    question_rewriter = prompt | llm | StrOutputParser()

    return question_rewriter