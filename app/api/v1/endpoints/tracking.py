import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.websocket("/rides/{ride_id}")
async def ride_tracking_socket(websocket: WebSocket, ride_id: uuid.UUID) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "ride_id": str(ride_id)})
    try:
        while True:
            payload = await websocket.receive_json()
            await websocket.send_json({"type": "location_update", "ride_id": str(ride_id), "payload": payload})
    except WebSocketDisconnect:
        return
