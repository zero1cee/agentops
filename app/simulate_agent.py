
import time
import uuid

import httpx


API_URL = "http://127.0.0.1:8000"
TRACE_ID = "trace-" + str(uuid.uuid4())[:8]


def send_event(
    event_type,
    name,
    status="success",
    duration_ms=None,
):
    payload = {
        "trace_id": TRACE_ID,
        "event_type": event_type,
        "name": name,
        "status": status,
    }

    if duration_ms is not None:
        payload["duration_ms"] = duration_ms

    response = httpx.post(
        API_URL + "/events",
        json=payload,
        timeout=10.0,
    )
    response.raise_for_status()

    print("Recorded:", event_type, "-", name, "-", status)


def run_simulation():
    print("Starting AgentOps simulation")
    print("Trace ID:", TRACE_ID)

    send_event("agent_start", "document_assistant")
    time.sleep(0.2)

    send_event(
        "tool_call",
        "search_documents",
        duration_ms=120,
    )
    time.sleep(0.2)

    send_event(
        "llm_call",
        "generate_answer",
        duration_ms=450,
    )
    time.sleep(0.2)

    send_event("agent_end", "document_assistant")

    print("\nSimulation complete!")
    print("View events at:", API_URL + "/docs")
    print(
        "Filter events with trace_id:",
        TRACE_ID,
    )


if __name__ == "__main__":
    run_simulation()
