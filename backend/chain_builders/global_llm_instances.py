from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

global_llm = ChatOpenAI()