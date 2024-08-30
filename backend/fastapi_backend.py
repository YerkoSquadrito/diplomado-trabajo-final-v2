from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, filter_messages
from chatbot_multi_agent import chatbot

app = FastAPI()

class Message(BaseModel):
    text: list


@app.post("/chat")
async def chat(message: Message):
    chat_history = [HumanMessage(item[1]) if item[0]=='human' else AIMessage(item[1]) for item in message.text ]
    graph_response = chatbot.invoke({"messages": chat_history})
    chat_history = graph_response["messages"]
    response = filter_messages(chat_history, include_types=[AIMessage])[-1].content
    return {"response": f'{response}'}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)