import os
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from openai import OpenAI
from template import html_template


load_dotenv()

openai_key = os.environ['OPENAI_API_KEY']

app = FastAPI()
client = OpenAI(api_key=openai_key)
active_client: WebSocket | None = None



async def get_openai_response(message: str) -> str:
    response = client.chat.completions.create(
        model='gpt-4-turbo',
        messages=[
            {'role': 'system', 'content': 'You are storyteller'},
            {'role':'user','content':message}
        ]
    )
    return response.choices[0].message.content

@app.get('/')
async def get():
    return HTMLResponse(html_template)


@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: int):
        global active_client
        if active_client is not None:
            await websocket.close(code=1000)
            return

        active_client = websocket
        await active_client.accept()
        try:
            while True:
                data = await active_client.receive_text()
                response = await get_openai_response(data)
                await active_client.send_text(f'Your message: {data}')
                await active_client.send_text(f'OpenAI wrote: {response}')
        except WebSocketDisconnect:
            active_client = None
            await active_client.send_text('You left the chat') if active_client else None