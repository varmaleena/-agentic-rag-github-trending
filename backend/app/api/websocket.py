import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.routes import graph_config, record_query_history
from app.graph.graph import app_graph

logger = logging.getLogger(__name__)
ws_router = APIRouter(tags=["WebSocket Streaming"])


@ws_router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                data = json.loads(await websocket.receive_text())
                query = data.get("query") if isinstance(data, dict) else None
            except ValueError:
                query = None
            if not isinstance(query, str) or not query.strip():
                await websocket.send_json({"type": "error", "message": "A nonempty query is required."})
                continue

            started = time.monotonic()
            try:
                async for mode, event in app_graph.astream(
                    {"query": query.strip()}, config=graph_config(), stream_mode=["custom", "values"]
                ):
                    if mode == "custom":
                        await websocket.send_json(event)
                    else:
                        state = event
                record = record_query_history(state, time.monotonic() - started)
                if record["answer"]:
                    await websocket.send_json({"type": "stream_end", **record})
                else:
                    await websocket.send_json({"type": "error", "message": record["error"]})
            except WebSocketDisconnect:
                raise
            except Exception:
                logger.exception("WebSocket query failed")
                await websocket.send_json({"type": "error", "message": "Query execution failed."})
    except WebSocketDisconnect:
        return
