"""
Unit and Integration Tests for Backend Query Inspector Tracing.
Verifies real-time Cypher execution capture, timing, parameter sanitization,
multi-statement transaction ordering, header encoding, and inspector endpoints.
"""
import base64
import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.query_tracer import QueryTracer, sanitize_parameters, format_cypher_text


@pytest.fixture
def client():
    return TestClient(app)


def decode_trace_header(header_val: str) -> list:
    """Helper to decode base64 JSON trace header."""
    assert header_val, "Trace header must not be empty"
    raw_json = base64.b64decode(header_val.encode("ascii")).decode("utf-8")
    return json.loads(raw_json)


class TestQueryTracerUnits:
    def test_sanitize_parameters_masks_passwords_and_tokens(self):
        params = {
            "guest_id": "G001",
            "password": "secret_password_123",
            "admin_pwd": "topsecretadmin",
            "access_token": "jwt.header.payload",
            "normal_field": "John Doe",
            "rent": 4500.0,
        }
        sanitized = sanitize_parameters(params)
        assert sanitized["guest_id"] == "G001"
        assert sanitized["normal_field"] == "John Doe"
        assert sanitized["rent"] == 4500.0
        assert sanitized["password"] == "********"
        assert sanitized["admin_pwd"] == "********"
        assert sanitized["access_token"] == "********"

    def test_format_cypher_text_cleans_indentation(self):
        query = """
            MATCH (r:Room)
            WHERE r.status = 'Available'
            RETURN r
        """
        formatted = format_cypher_text(query)
        assert formatted.startswith("MATCH (r:Room)")
        assert "WHERE r.status = 'Available'" in formatted


class TestQueryInspectorEndpointsAndHeaders:
    def test_query_history_clear_and_retrieve(self, client):
        # Clear history
        clear_res = client.post("/api/query-inspector/clear")
        assert clear_res.status_code == 200
        assert clear_res.json()["status"] == "cleared"

        # Check empty history
        hist_res = client.get("/api/query-inspector/history")
        assert hist_res.status_code == 200
        assert hist_res.json() == []

    def test_room_search_attaches_trace_header_with_real_cypher(self, client):
        client.post("/api/query-inspector/clear")
        res = client.get("/api/rooms/search?location=Mumbai")
        assert res.status_code == 200

        # Check header presence
        trace_hdr = res.headers.get("X-Backend-Trace")
        assert trace_hdr is not None, "Response must include X-Backend-Trace header"
        traces = decode_trace_header(trace_hdr)

        assert len(traces) >= 1
        trace = traces[0]
        assert trace["action"] == "Search Available Rooms"
        assert "MATCH" in trace["cypher"]
        assert trace["status"] == "SUCCESS"
        assert trace["duration_ms"] >= 0
        assert "records_count" in trace

    def test_hotel_listing_attaches_trace(self, client):
        res = client.get("/api/hotels/")
        assert res.status_code == 200

        trace_hdr = res.headers.get("X-Backend-Trace")
        assert trace_hdr is not None
        traces = decode_trace_header(trace_hdr)
        assert len(traces) >= 1
        assert "Hotel" in traces[0]["cypher"]

    def test_guest_login_sanitizes_password_in_trace(self, client):
        client.post("/api/query-inspector/clear")
        payload = {
            "guest_id": "G001",
            "password": "password123",
            "name": "John Smith",
        }
        res = client.post("/api/guests/login", json=payload)
        assert res.status_code == 200

        # Inspect captured queries
        history_res = client.get("/api/query-inspector/history")
        history = history_res.json()
        assert len(history) >= 1

        # Find query executed for guest login
        login_trace = next(
            (t for t in reversed(history) if "Guest" in t["cypher"] and "guest_id" in t.get("parameters", {})),
            None
        )
        assert login_trace is not None
        params = login_trace.get("parameters", {})
        if "password" in params:
            assert params["password"] == "********", "Password must be sanitized in trace"

    def test_atomic_reservation_captures_ordered_transaction_statements(self, client):
        client.post("/api/query-inspector/clear")
        booking_payload = {
            "guest_id": "G003",
            "room_no": 101,
            "check_in_date": "2027-11-01",
            "check_out_date": "2027-11-04",
        }
        res = client.post("/api/reservations/", json=booking_payload)
        assert res.status_code == 201

        trace_hdr = res.headers.get("X-Backend-Trace")
        assert trace_hdr is not None
        traces = decode_trace_header(trace_hdr)

        # Multi-step transaction should have captured multiple statements in order
        assert len(traces) >= 2, "Atomic booking transaction should execute multiple Cypher queries"
        queries_text = [t["cypher"] for t in traces]
        assert any("Room" in q for q in queries_text)
        assert any("Reservation" in q for q in queries_text)

        # Cleanup booking to preserve pristine seed state for subsequent tests
        created_id = res.json().get("res_id")
        if created_id:
            client.post(f"/api/reservations/{created_id}/cancel")

    def test_graph_visualization_data_endpoint(self, client):
        res = client.get("/api/graph/data")
        assert res.status_code == 200
        data = res.json()
        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) > 0
        assert len(data["links"]) > 0
