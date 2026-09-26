from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from collabpilot.bootstrap import create_application, get_settings
from collabpilot.domain.errors import AgentError
from collabpilot.domain.models import ChatResult


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=50_000)
    session_id: UUID | None = None
    provider: str | None = None
    model: str | None = None


def create_api() -> FastAPI:
    api = FastAPI(title="CollabPilot API", version="0.1.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:8001",
            "http://localhost:8001",
        ],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "name": get_settings().app.name}

    @api.post("/v1/chat", response_model=ChatResult)
    async def chat(request: ChatRequest) -> ChatResult:
        try:
            return await create_application().chat(
                content=request.message,
                session_id=request.session_id,
                provider_name=request.provider,
                model=request.model,
            )
        except AgentError as exc:
            raise HTTPException(
                status_code=400,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc

    @api.post("/v1/chat/stream")
    async def chat_stream(request: ChatRequest) -> StreamingResponse:
        async def events():
            queue: asyncio.Queue[dict | None] = asyncio.Queue()

            async def on_delta(text: str) -> None:
                await queue.put({"type": "delta", "content": text})

            async def run_chat() -> None:
                try:
                    result = await create_application().chat(
                        content=request.message,
                        session_id=request.session_id,
                        provider_name=request.provider,
                        model=request.model,
                        on_delta=on_delta,
                    )
                    await queue.put({"type": "done", "result": result.model_dump(mode="json")})
                except AgentError as exc:
                    await queue.put(
                        {
                            "type": "error",
                            "error": {"code": exc.code, "message": str(exc)},
                        }
                    )
                finally:
                    await queue.put(None)

            task = asyncio.create_task(run_chat())
            try:
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            finally:
                await task

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return api


app = create_api()
