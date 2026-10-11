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
        assert response.status_code in [200, 201]

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
        response = test_client.post("/api/reservations/", json={
            "res_id": "R001",
            "guest_id": "G001",
            "room_no": 101,
            "staff_id": "S001",
            "check_in_date": "2027-12-01",
            "check_out_date": "2027-12-05",
        })
        assert response.status_code == 409

    def test_maintenance_room_cannot_be_booked(self, test_client):
        """Room 105 is under maintenance and should be rejected."""
        response = test_client.post("/api/reservations/", json={
            "res_id": "RTEST_MAINT",
            "guest_id": "G001",
            "room_no": 105,
            "staff_id": "S001",
            "check_in_date": "2027-08-01",
            "check_out_date": "2027-08-05",
        })
        assert response.status_code == 400
        assert "maintenance" in response.json()["detail"].lower()

    def test_non_overlapping_bookings_succeed(self, test_client):
        """Two bookings on the same room with distinct date ranges should both succeed."""
        resp1 = test_client.post("/api/reservations/", json={
            "res_id": "RTEST_NON1",
            "guest_id": "G001",
            "room_no": 301,
            "staff_id": "S006",
            "check_in_date": "2027-01-10",
            "check_out_date": "2027-01-15",
        })
        assert resp1.status_code in [200, 201]

        resp2 = test_client.post("/api/reservations/", json={
            "res_id": "RTEST_NON2",
            "guest_id": "G002",
            "room_no": 301,
            "staff_id": "S006",
            "check_in_date": "2027-01-16",
            "check_out_date": "2027-01-20",
        })
        assert resp2.status_code in [200, 201]

        # Cleanup
        test_client.post("/api/reservations/RTEST_NON1/cancel")
        test_client.post("/api/reservations/RTEST_NON2/cancel")

    def test_concurrent_double_booking(self, test_client):
        """Two concurrent booking attempts for the same room on overlapping dates: exactly one must succeed."""
        from concurrent.futures import ThreadPoolExecutor

        def attempt_booking(res_id, guest_id):
            return test_client.post("/api/reservations/", json={
                "res_id": res_id,
                "guest_id": guest_id,
                "room_no": 204,
                "staff_id": "S004",
                "check_in_date": "2027-09-01",
                "check_out_date": "2027-09-10",
            })

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(attempt_booking, "RCONC_1", "G001")
            fut2 = executor.submit(attempt_booking, "RCONC_2", "G002")
            res1 = fut1.result()
            res2 = fut2.result()

        status_codes = sorted([res1.status_code, res2.status_code])
        # Exactly one must succeed (200 or 201) and the second must be rejected with 409 Conflict
        assert status_codes[0] in [200, 201], f"Expected one 201/200, got {status_codes}"
        assert status_codes[1] == 409, f"Expected second to be 409 Conflict, got {status_codes}"

        # Cleanup
        test_client.post("/api/reservations/RCONC_1/cancel")
        test_client.post("/api/reservations/RCONC_2/cancel")

    def test_recommendation_excludes_visited_hotels(self, test_client):
        """Recommendations for G001 must not include Grand Palace Hotel (H001) which G001 already visited."""
        response = test_client.get("/api/recommendations/hotels/G001")
        assert response.status_code == 200
        recs = response.json().get("recommendations", [])
        hotel_ids = [r["hotel_id"] for r in recs]
        assert "H001" not in hotel_ids

    def test_create_staff_endpoint(self, test_client):
        """Creating a new staff member and validating duplicate rejection."""
        # Success creation
        resp = test_client.post("/api/staff/", json={
            "staff_id": "S099",
            "name": "Pooja Hegde",
            "age": 27,
            "salary": 38000.0,
            "contact_info": "9876500099",
            "dept_id": "D001"
        })
        assert resp.status_code == 201
        assert resp.json()["staff_id"] == "S099"

        # Duplicate ID should return 409
        dup_resp = test_client.post("/api/staff/", json={
            "staff_id": "S099",
            "name": "Pooja Hegde",
            "age": 27,
            "salary": 38000.0,
            "contact_info": "9876500099",
            "dept_id": "D001"
        })
        assert dup_resp.status_code == 409

        # Invalid dept should return 404
        bad_dept = test_client.post("/api/staff/", json={
            "staff_id": "S100",
            "name": "Test Person",
            "age": 30,
            "salary": 30000.0,
            "contact_info": "9876500100",
            "dept_id": "D_INVALID"
        })
        assert bad_dept.status_code == 404

