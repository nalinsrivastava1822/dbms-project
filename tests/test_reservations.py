"""
Test reservation operations: creation, validation, overlap prevention, cancellation.
"""
import pytest
from datetime import date, timedelta


@pytest.mark.requires_neo4j
class TestReservations:
    def test_list_reservations(self, test_client):
        """Verify reservation listing."""
        response = test_client.get("/api/reservations/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_reservation_invalid_dates(self, test_client):
        """Check-out must be after check-in."""
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST01",
            "guest_id": "G001",
            "room_no": 101,
            "staff_id": "S001",
            "check_in_date": "2026-12-15",
            "check_out_date": "2026-12-10",  # Before check-in
        })
        assert response.status_code == 400
        assert "Check-out" in response.json()["detail"]

    def test_create_reservation_same_dates(self, test_client):
        """Check-out same as check-in should fail."""
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST02",
            "guest_id": "G001",
            "room_no": 101,
            "staff_id": "S001",
            "check_in_date": "2026-12-15",
            "check_out_date": "2026-12-15",
        })
        assert response.status_code == 400

    def test_create_reservation_invalid_guest(self, test_client):
        """Non-existent guest should fail."""
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST03",
            "guest_id": "GXXX",
            "room_no": 101,
            "staff_id": "S001",
            "check_in_date": "2026-12-15",
            "check_out_date": "2026-12-20",
        })
        assert response.status_code == 404
        assert "Guest" in response.json()["detail"]

    def test_create_reservation_invalid_room(self, test_client):
        """Non-existent room should fail."""
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST04",
            "guest_id": "G001",
            "room_no": 9999,
            "staff_id": "S001",
            "check_in_date": "2026-12-15",
            "check_out_date": "2026-12-20",
        })
        assert response.status_code == 404
        assert "Room" in response.json()["detail"]

    def test_create_reservation_invalid_staff(self, test_client):
        """Non-existent staff should fail."""
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST05",
            "guest_id": "G001",
            "room_no": 101,
            "staff_id": "SXXX",
            "check_in_date": "2026-12-15",
            "check_out_date": "2026-12-20",
        })
        assert response.status_code == 404
        assert "Staff" in response.json()["detail"]

    def test_create_and_cancel_reservation(self, test_client):
        """Create a reservation and then cancel it."""
        # Create
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST10",
            "guest_id": "G001",
            "room_no": 104,
            "staff_id": "S001",
            "check_in_date": "2027-06-01",
            "check_out_date": "2027-06-05",
        })
        if response.status_code == 409:
            pytest.skip("Reservation RTEST10 already exists or room overlap")
        assert response.status_code == 200

        # Cancel
        cancel_resp = test_client.post("/api/reservations/RTEST10/cancel")
        assert cancel_resp.status_code == 200
        assert "cancelled" in cancel_resp.json()["message"].lower()

    def test_cancel_already_cancelled(self, test_client):
        """Cancelling an already-cancelled reservation should fail."""
        # First ensure RTEST10 is cancelled (from previous test)
        response = test_client.post("/api/reservations/RTEST10/cancel")
        if response.status_code == 404:
            pytest.skip("RTEST10 not available")
        assert response.status_code == 400
        assert "already cancelled" in response.json()["detail"].lower()

    def test_cancel_nonexistent_reservation(self, test_client):
        """Cancelling non-existent reservation should return 404."""
        response = test_client.post("/api/reservations/RXXX/cancel")
        assert response.status_code == 404

    def test_overlapping_reservation(self, test_client):
        """Creating overlapping reservation for same room should fail."""
        # Create first reservation
        resp1 = test_client.post("/api/reservations/", json={
            "res_id": "RTEST20",
            "guest_id": "G002",
            "room_no": 201,
            "staff_id": "S004",
            "check_in_date": "2027-07-01",
            "check_out_date": "2027-07-10",
        })
        if resp1.status_code == 409:
            pytest.skip("Room 201 already has a conflicting reservation")

        # Attempt overlapping reservation on same room
        resp2 = test_client.post("/api/reservations/", json={
            "res_id": "RTEST21",
            "guest_id": "G003",
            "room_no": 201,
            "staff_id": "S004",
            "check_in_date": "2027-07-05",
            "check_out_date": "2027-07-12",
        })
        assert resp2.status_code == 409
        assert "overlapping" in resp2.json()["detail"].lower()

        # Cleanup
        test_client.post("/api/reservations/RTEST20/cancel")

    def test_duplicate_reservation_id(self, test_client):
        """Duplicate reservation ID should fail."""
        # Use existing seed data ID
        response = test_client.post("/api/reservations/", json={
            "res_id": "R001",
            "guest_id": "G001",
            "room_no": 101,
            "staff_id": "S001",
            "check_in_date": "2027-12-01",
            "check_out_date": "2027-12-05",
        })
        # Either 409 (dup ID) or 409 (overlap) — both valid
        assert response.status_code == 409
