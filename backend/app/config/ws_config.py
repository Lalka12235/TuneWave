from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connection: dict[str, list[WebSocket]] = {

        }


    async def connect(self,room_name,websocket: WebSocket):
        await websocket.accept()
        self.active_connection.setdefault(room_name,[]).append(websocket)


    def disconnect(self,room_name ,websocket: WebSocket):
        self.active_connection[room_name].remove(websocket)
        

    async def send_personal_message(self,message: str, websocket: WebSocket):
        await websocket.send_text(message)

    
    async def broadcast(self, room_name: str, message: str):
        for connection in self.active_connection.get((room_name,[])):
            await connection.send_text(message)


manager = ConnectionManager() 