"""
Inspectra - WebSocket Hub for Real-Time Inspection Telemetry
"""

import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from ..inspection import inspection_manager

async def handle_inspection_ws(websocket: WebSocket, inspection_id: str):
    await websocket.accept()
    queue = inspection_manager.subscribe(inspection_id)
    try:
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=120.0)
            await websocket.send_json(event)
            if event.get("type") in ["complete", "error"]:
                break
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception:
        pass
    finally:
        inspection_manager.unsubscribe(inspection_id)
        try:
            await websocket.close()
        except Exception:
            pass

