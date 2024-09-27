from chain_builders.global_llm_instances import global_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional

class UserSchema(BaseModel):
    user_name: Optional[str] = Field(description="The user name mentioned by the human in his last message, which will be used as session_id. Use upper case always.")

identifyier_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Your only task is to identify the user name mentioned in the last message."),
            ("human", "{message}"),
        ]
    )

structured_llm = global_llm.with_structured_output(UserSchema)

user_identifier_chain = identifyier_prompt | structured_llm


# from langchain.memory.chat_message_histories.redis import RedisChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
import os

redis_url = os.getenv('REDIS_URL')

def retrieve_history(session_id):
  history = RedisChatMessageHistory(session_id=session_id, url=redis_url)
  return history