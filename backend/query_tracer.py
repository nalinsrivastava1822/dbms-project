"""
Live Backend Query Inspector Tracer.
Instruments and captures actual Cypher query executions against Neo4j / Simulator.
Provides timing, parameter sanitization, record counts, and thread-safe history buffering.
"""
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import base64
import time
from typing import Any, Dict, List, Optional


# Context variables for per-request tracing in FastAPI
request_trace_var: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar("request_trace_var", default=None)
request_endpoint_var: ContextVar[str] = ContextVar("request_endpoint_var", default="")
request_action_var: ContextVar[str] = ContextVar("request_action_var", default="")

# Thread-safe ring buffer of recent queries (max 150)
_history_lock = None
_MAX_HISTORY = 150
_query_counter = 0
_query_history: deque = deque(maxlen=_MAX_HISTORY)

SENSITIVE_KEYS = {"password", "pass", "pwd", "token", "secret", "auth", "api_key", "cookie", "access_token"}


def _get_lock():
    global _history_lock
    if _history_lock is None:
        import threading
        _history_lock = threading.Lock()
    return _history_lock


def sanitize_value(v: Any) -> Any:
    """Recursively serialize and sanitize values for JSON representation."""
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    if isinstance(v, (datetime, )):
        return v.isoformat()
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if isinstance(v, (list, tuple, set)):
        return [sanitize_value(item) for item in v]
    if isinstance(v, dict):
        return {
            k: ("********" if any(s in str(k).lower() for s in SENSITIVE_KEYS) else sanitize_value(val))
            for k, val in v.items()
        }
    return str(v)


def sanitize_parameters(parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a sanitized copy of query parameters with passwords/tokens masked."""
    if not parameters:
        return {}
    sanitized = {}
    for k, v in parameters.items():
        if any(s in str(k).lower() for s in SENSITIVE_KEYS):
            sanitized[k] = "********"
        else:
            sanitized[k] = sanitize_value(v)
    return sanitized


def format_cypher_text(query: str) -> str:
    """Clean up Cypher query indentation while preserving full query structure."""
    lines = [line.rstrip() for line in query.strip().splitlines()]
    # Remove uniform leading indentation if present
    non_empty = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    min_indent = min(non_empty) if non_empty else 0
    cleaned_lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
    return "\n".join(cleaned_lines)


class QueryTracer:
    """Manages recording and retrieval of actual backend Cypher executions."""

    @staticmethod
    def record_execution(
        query: str,
        parameters: Optional[Dict[str, Any]],
        database_mode: str,
        duration_ms: float,
        status: str,
        records_count: int = 0,
        error: Optional[str] = None,
        action: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        global _query_counter

        # Derive action/endpoint from contextvars if not explicitly supplied
        effective_action = action or request_action_var.get() or "Neo4j Database Operation"
        effective_endpoint = endpoint or request_endpoint_var.get() or "Direct Database Execution"

        with _get_lock():
            _query_counter += 1
            query_id = _query_counter

        entry = {
            "id": query_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "time_display": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "action": effective_action,
            "endpoint": effective_endpoint,
            "database": database_mode,
            "cypher": format_cypher_text(query),
            "parameters": sanitize_parameters(parameters),
            "duration_ms": duration_ms,
            "status": status,
            "records_count": records_count,
            "error": error,
        }

        # Append to thread-safe global history
        with _get_lock():
            _query_history.append(entry)

        # Append to per-request trace list if within an active HTTP request
        trace_list = request_trace_var.get()
        if trace_list is not None:
            trace_list.append(entry)

        return entry

    @staticmethod
    def get_history(limit: int = 100) -> List[Dict[str, Any]]:
        with _get_lock():
            return list(_query_history)[-limit:]

    @staticmethod
    def clear_history():
        with _get_lock():
            _query_history.clear()

    @staticmethod
    def encode_traces(traces: List[Dict[str, Any]]) -> str:
        """Encode trace list as base64 JSON for safe HTTP header transport."""
        json_bytes = json.dumps(traces).encode("utf-8")
        return base64.b64encode(json_bytes).decode("ascii")


def infer_action_name(method: str, path: str) -> str:
    """Map API endpoints to human-readable academic demonstration action names."""
    m = method.upper()
    p = path.rstrip("/")

    # Rooms
    if p.endswith("/api/rooms/search"):
        return "Search Available Rooms"
    if p.endswith("/api/rooms/categories"):
        return "Fetch Room Categories"
    if p.endswith("/api/rooms") and m == "GET":
        return "List All Rooms"
    if p.endswith("/api/rooms") and m == "POST":
        return "Create New Room"
    if "/api/rooms/" in p and p.endswith("/status"):
        return "Update Room Status"

    # Reservations
    if p.endswith("/api/reservations") and m == "GET":
        return "List All Reservations"
    if p.endswith("/api/reservations") and m == "POST":
        return "Create Atomic Reservation"
    if "/api/reservations/" in p and p.endswith("/cancel"):
        return "Cancel Reservation"

    # Guests
    if p.endswith("/api/guests/login"):
        return "Guest Authentication & Profile"
    if p.endswith("/api/guests/search"):
        return "Search Guests by Name/Nationality"
    if p.endswith("/api/guests") and m == "GET":
        return "List Guests"
    if p.endswith("/api/guests") and m == "POST":
        return "Register New Guest"
    if "/api/guests/" in p and p.endswith("/reservations"):
        return "Fetch Guest Reservation History"
    if "/api/guests/" in p and m == "GET":
        return "Fetch Guest Details"

    # Hotels
    if p.endswith("/api/hotels") and m == "GET":
        return "List Hotels"
    if "/api/hotels/" in p and p.endswith("/rooms"):
        return "Fetch Hotel Rooms Traversal"
    if "/api/hotels/" in p and p.endswith("/departments"):
        return "Fetch Hotel Departments Traversal"
    if "/api/hotels/" in p and m == "GET":
        return "Get Hotel Profile"

    # Dashboard
    if p.endswith("/api/dashboard/stats"):
        return "Load Dashboard Overview Metrics"
    if p.endswith("/api/dashboard/room-availability"):
        return "Check Live Room Availability"
    if p.endswith("/api/dashboard/recent-reservations"):
        return "Load Recent Reservations"
    if p.endswith("/api/dashboard/revenue-analytics"):
        return "Compute Revenue Analytics"

    # Recommendations
    if "/api/recommendations/hotels" in p:
        return "Collaborative Hotel Recommendations"
    if "/api/recommendations/rooms" in p:
        return "Collaborative Room Recommendations"
    if "/api/recommendations/popular-by-nationality" in p:
        return "Popular Hotels by Nationality"
    if "/api/recommendations/guest-journey" in p:
        return "Multi-Hop Guest Journey Traversal"

    # Staff
    if p.endswith("/api/staff") and m == "GET":
        return "List Staff Directory"
    if p.endswith("/api/staff") and m == "POST":
        return "Create Staff Member"
    if "/api/staff/by-department" in p:
        return "Filter Staff by Department"
    if "/api/staff/" in p and p.endswith("/reservations"):
        return "Fetch Staff Processing History"

    # Graph
    if p.endswith("/api/graph/data"):
        return "Query Full Graph Topology"

    return f"{m} {p}"
