from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import Runnable
import os

# Data model
class GradeAnswer(BaseModel):
    """Binary score to assess wether the answer addresses the question."""
    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

# Prompt
system_prompt = """You are a grader assessing whether an answer addresses / resolves a question \n 
Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""

def build_answer_grader_chain(
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv('AZURE_COMPLETIONS_DEPLOYMENT_NAME'), 
            model_version=os.getenv('AZURE_COMPLETIONS_MODEL_VERSION'), 
            temperature=0 
        ),
        system_prompt = system_prompt,
        output_schema = GradeAnswer
) -> Runnable:
    """
    Builds and returns an answer grader chain, which answers wether the answer addresses the question.

    Chain input must be a dictionary with:
    - question: The question answered
    - generation: The AI generated response to be graded
    
    Inputs:
        llm (ChatOpenAI): The language model to use. Defaults to gpt-4o-mini.
        system_prompt (str): The system prompt for the grader. Defaults to binary grading.

    Returns:
        answer_grader: The answer grader chain.
    """
    
    structured_llm_grader = llm.with_structured_output(output_schema)
    
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
        ]
    )

    answer_grader = answer_prompt | structured_llm_grader

    return answer_grader
