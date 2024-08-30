from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import AzureChatOpenAI
import os

class MultiQuery(BaseModel):
  alternative_questions: list[str] = Field(description="A python list containing strings of each alternative question")

parser = PydanticOutputParser(pydantic_object=MultiQuery)
format_instructions = parser.get_format_instructions()


template = """ ## General instructions
{format_instructions}

## Task:
You are an AI language model assistant. Your task is to generate five
different versions of the given user question to retrieve relevant documents from a vector
database. By generating multiple perspectives on the user question, your goal is to help
the user overcome some of the limitations of the distance-based similarity search.

## Original question:
{question}"""

prompt = ChatPromptTemplate.from_template(
    template = template,
    partial_variables = {
        "format_instructions": format_instructions
    }
)

def build_multi_query_generation_chain(
        llm = AzureChatOpenAI(
            deployment_name=os.getenv('AZURE_COMPLETIONS_DEPLOYMENT_NAME'), 
            model_version=os.getenv('AZURE_COMPLETIONS_MODEL_VERSION'), 
            temperature=0 
        ),
        prompt = prompt,
        parser = parser
    ) -> Runnable:
    """
    Builds a chain for multi-query generation.

    Args:
        llm (ChatOpenAI): The language model used for generating responses.
        prompt (str): The prompt for generating queries.
        parser (Parser): The parser used for parsing the generated queries.

    Returns:
        Runnable: The chain for multi-query generation.

    """
    multi_query_chain =  prompt | llm | parser
    return multi_query_chain