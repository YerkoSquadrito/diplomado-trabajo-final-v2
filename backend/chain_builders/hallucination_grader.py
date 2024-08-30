from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import Runnable
import os

# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

system_prompt = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""

def build_hallucination_grader_chain(
        llm = AzureChatOpenAI(
            deployment_name=os.getenv('AZURE_COMPLETIONS_DEPLOYMENT_NAME'), 
            model_version=os.getenv('AZURE_COMPLETIONS_MODEL_VERSION'), 
            temperature=0 
        ),
        system_prompt = system_prompt,
        output_schema = GradeHallucinations,
) -> Runnable:
    """
    Builds a hallucination grader chain using a language model (LLM) and a structured output grader. This assesses whether an LLM generation is grounded in / supported by a set of retrieved facts.

    Chain input must be a dictionary with:
    - documents: The retrieved documents
    - generation: The AI generated response to be graded

    Inputs:
        llm (ChatOpenAI): The language model to use. Defaults to gpt-4o-mini.
        system_prompt (str): The system prompt for the grader. Defaults to binary grading.
        output_schema (BaseModel): The structured output schema for the grader. Defaults to a binary grading.
    
    Returns:
        hallucination_grader: The hallucination grader chain.
    """

    structured_llm_grader = llm.with_structured_output(output_schema)

    hallucination_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
        ]
    )

    hallucination_grader = hallucination_prompt | structured_llm_grader

    return hallucination_grader