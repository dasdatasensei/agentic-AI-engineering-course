"""Section 8 exercise — Project 4: REST API wrapper.

Expose your Section 6 three-agent team via FastAPI with SSE streaming and
JWT authentication. Run with:

    uvicorn exercise:app --reload

then test with:

    curl -X POST http://localhost:8000/v1/research/submit \\
      -H "Content-Type: application/json" \\
      -d '{"brief": "test brief"}'
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ERA Platform API — Section 8 exercise")


class ResearchBrief(BaseModel):
    brief: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str


@app.post("/v1/research/submit", response_model=RunStatusResponse)
async def submit_research(payload: ResearchBrief) -> RunStatusResponse:
    """TODO: implement — kick off the Section 6 agent team as a background
    task, return a run_id immediately (Lecture 8.1, 8.3).
    """
    raise NotImplementedError("Implement submit_research")


@app.get("/v1/research/{run_id}/stream")
async def stream_research(run_id: str) -> object:
    """TODO: implement SSE streaming of agent progress events
    (Lecture 8.2).
    """
    raise NotImplementedError("Implement stream_research")
