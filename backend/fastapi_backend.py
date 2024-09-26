from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, filter_messages
from chatbot_multi_agent import chatbot
from indentificacion_usuario import user_identifier_chain, retrieve_history

app = FastAPI()

class Messages(BaseModel):
    message: str
    user_name: str

@app.post("/chat")
async def chat(input_data: Messages):
    redis_history = retrieve_history(input_data.user_name)
    redis_history.add_user_message(input_data.message)
    graph_response = chatbot.invoke({"chat_history": redis_history.messages})
    ai_text_response = filter_messages(graph_response["chat_history"], include_types=[AIMessage])[-1].content
    redis_history.add_ai_message(ai_text_response)
    return {"response": {"chat_history": redis_history.messages}}

class MessageInput(BaseModel):
    message: str

@app.post("/identify")
async def identify(input_data: MessageInput):
    response = user_identifier_chain.invoke({'message':input_data.message})
    if response.user_name:
        chat_history = retrieve_history(response.user_name).messages
        return {"response": {'user_name': response.user_name, 'chat_history': chat_history}}
    else:
        return {"response": {'user_name': None, 'chat_history': []}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)