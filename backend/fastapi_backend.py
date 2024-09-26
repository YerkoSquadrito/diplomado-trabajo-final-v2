from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, filter_messages
from chatbot_multi_agent import chatbot
from indentificacion_usuario import user_identifier_chain, retrieve_history

app = FastAPI()

class Messages(BaseModel):
    chat_history: list

@app.post("/chat")
async def chat(messages: Messages):
    chat_history = [HumanMessage(item[1]) if item[0]=='human' else AIMessage(item[1]) for item in messages.chat_history]
    graph_response = chatbot.invoke({"chat_history": chat_history})
    chat_history = graph_response["chat_history"]
    response = filter_messages(chat_history, include_types=[AIMessage])[-1].content
    return {"response": f'{response}'}

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