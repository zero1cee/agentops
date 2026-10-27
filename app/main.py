
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import database


app = FastAPI(
    title="AgentOps API",
    description="A local-first monitoring API for AI agent executions.",
    version="0.2.0",
)


class TraceEventCreate(BaseModel):
    trace_id: str = Field(min_length=1, max_length=100)

    event_type: Literal[
        "agent_start",
        "tool_call",
        "llm_call",
        "agent_end",
        "error",
    ]

    name: str = Field(min_length=1, max_length=200)
    status: Literal["success", "error", "running"]
    duration_ms: Optional[float] = Field(default=None, ge=0)

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class TraceEvent(TraceEventCreate):
    event_id: str


@app.on_event("startup")
def startup_event():
    database.init_db()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "agentops",
        "storage": "sqlite",
    }


@app.post("/events", response_model=TraceEvent, status_code=201)
def create_event(event: TraceEventCreate):
    saved_event = TraceEvent(
        event_id=str(uuid4()),
        **event.dict(),
    )

    database.insert_event(saved_event)
    return saved_event


@app.get("/events", response_model=List[TraceEvent])
def list_events(trace_id: Optional[str] = None):
    stored_events = database.get_events(trace_id=trace_id)

    return [
        TraceEvent(**event)
        for event in stored_events
    ]


@app.get("/events/{event_id}", response_model=TraceEvent)
def get_event(event_id: str):
    event = database.get_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return TraceEvent(**event)


@app.get("/analytics")
def get_analytics(trace_id: Optional[str] = None):
    stored_events = database.get_events(trace_id=trace_id)

    total_events = len(stored_events)
    failed_events = sum(
        1 for event in stored_events
        if event["status"] == "error"
    )

    completed_durations = [
        event["duration_ms"]
        for event in stored_events
        if event["duration_ms"] is not None
    ]

    average_duration_ms = (
        sum(completed_durations) / len(completed_durations)
        if completed_durations
        else None
    )

    event_type_counts = {}
    for event in stored_events:
        event_type = event["event_type"]
        event_type_counts[event_type] = (
            event_type_counts.get(event_type, 0) + 1
        )

    return {
        "trace_id": trace_id,
        "total_events": total_events,
        "failed_events": failed_events,
        "success_events": sum(
            1 for event in stored_events
            if event["status"] == "success"
        ),
        "running_events": sum(
            1 for event in stored_events
            if event["status"] == "running"
        ),
        "average_duration_ms": average_duration_ms,
        "event_type_counts": event_type_counts,
    }


@app.get("/traces/{trace_id}")
def get_trace_summary(trace_id: str):
    stored_events = database.get_events(trace_id=trace_id)

    if not stored_events:
        raise HTTPException(
            status_code=404,
            detail="Trace not found",
        )

    ordered_events = sorted(
        stored_events,
        key=lambda event: event["timestamp"],
    )

    failed_events = [
        event for event in ordered_events
        if event["status"] == "error"
    ]

    start_events = [
        event for event in ordered_events
        if event["event_type"] == "agent_start"
    ]

    end_events = [
        event for event in ordered_events
        if event["event_type"] == "agent_end"
    ]

    if failed_events:
        trace_status = "error"
    elif not end_events:
        trace_status = "running"
    else:
        trace_status = "success"

    start_time = (
        start_events[0]["timestamp"]
        if start_events else None
    )

    end_time = (
        end_events[-1]["timestamp"]
        if end_events else None
    )

    trace_duration_ms = None

    if start_time and end_time:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)

        trace_duration_ms = round(
            (end_dt - start_dt).total_seconds() * 1000,
            2,
        )

    event_durations = [
        event["duration_ms"]
        for event in ordered_events
        if event["duration_ms"] is not None
    ]

    return {
        "trace_id": trace_id,
        "status": trace_status,
        "event_count": len(ordered_events),
        "start_time": start_time,
        "end_time": end_time,
        "trace_duration_ms": trace_duration_ms,
        "total_event_duration_ms": sum(event_durations),
        "failed_event_count": len(failed_events),
        "events": ordered_events,
    }
