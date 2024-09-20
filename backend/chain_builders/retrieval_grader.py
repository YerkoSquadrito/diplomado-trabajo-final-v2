from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from .global_llm_instances import global_llm
from langchain_core.runnables import Runnable
import os

# Data model to use as structured output
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

system_prompt = """You are a grader assessing relevance of a retrieved document to a user question. \n 
If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

def build_retrieval_grader_chain(
        llm = global_llm,
        system_prompt = system_prompt,
        grader = GradeDocuments
    ) -> Runnable:
    """
    Builds a retrieval grader chain that assesses the relevance of a retrieved document to a user question.

    Chain input must be a dictionary with:
    - question: The user question.
    - document: The retrieved document to be graded.

    Inputs:
        llm (ChatOpenAI): The language model to use. Defaults to gpt-4o-mini.
        system_prompt (str): The system prompt for the grader. Defaults to binary grading.
        grader (BaseModel): The structured output schema for the grader. Defaults to binary grading.
    
    Returns:
        The retrieval grader chain.
    """
    
    structured_llm_grader = llm.with_structured_output(grader)

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
        ]
    )

    retrieval_grader = grade_prompt | structured_llm_grader
    
    return retrieval_grader
