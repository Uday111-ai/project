from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class MessageRequest(BaseModel):
    message: str


@app.post("/message")
def message(data: MessageRequest):
    print("Received:", data.message)

    return {
        "message": "hello"
    }