"""
Test room operations: listing, search, creation, status update.
"""
import pytest


@pytest.mark.requires_neo4j
class TestRooms:
    def test_list_rooms(self, test_client):
        """Verify room listing."""
        response = test_client.get("/api/rooms/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_categories(self, test_client):
        """Verify room categories listing."""
        response = test_client.get("/api/rooms/categories")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)

    def test_search_available_rooms(self, test_client):
        """Search for available rooms."""
        response = test_client.get("/api/rooms/search?status=Available")
        assert response.status_code == 200
        rooms = response.json()
        for room in rooms:
            assert room["status"] == "Available"

    def test_search_by_hotel(self, test_client):
        """Search rooms by hotel ID."""
        response = test_client.get("/api/rooms/search?hotel_id=H001")
        assert response.status_code == 200
        rooms = response.json()
        for room in rooms:
            assert room["hotel_id"] == "H001"

    def test_search_by_max_rent(self, test_client):
        """Search rooms by max rent."""
        response = test_client.get("/api/rooms/search?max_rent=3000")
        assert response.status_code == 200
        rooms = response.json()
        for room in rooms:
            assert room["rent"] <= 3000

    def test_search_combined_filters(self, test_client):
        """Search with multiple filters."""
        response = test_client.get("/api/rooms/search?hotel_id=H001&status=Available&max_rent=6000")
        assert response.status_code == 200
        rooms = response.json()
        for room in rooms:
            assert room["hotel_id"] == "H001"
            assert room["status"] == "Available"
            assert room["rent"] <= 6000

    def test_create_room_invalid_hotel(self, test_client):
        """Attempt to create room with non-existent hotel."""
        response = test_client.post("/api/rooms/", json={
            "room_no": 999, "hotel_id": "HXXX", "category_name": "Standard", "status": "Available"
        })
        assert response.status_code == 404

    def test_create_room_invalid_category(self, test_client):
        """Attempt to create room with non-existent category."""
        response = test_client.post("/api/rooms/", json={
            "room_no": 999, "hotel_id": "H001", "category_name": "SuperLuxury", "status": "Available"
        })
        assert response.status_code == 404

    def test_update_room_status(self, test_client):
        """Update room status."""
        response = test_client.patch("/api/rooms/101/status", json={"status": "Maintenance"})
        if response.status_code == 404:
            pytest.skip("Room 101 not in database")
        assert response.status_code == 200
        # Reset
        test_client.patch("/api/rooms/101/status", json={"status": "Available"})

    def test_update_room_invalid_status(self, test_client):
        """Attempt invalid status value."""
        response = test_client.patch("/api/rooms/101/status", json={"status": "InvalidStatus"})
        assert response.status_code == 422  # Pydantic validation error

    # =========================================================================
    # Phase 2 & 4: Smart Room Availability & Booking Tests
    # =========================================================================

    def test_search_rooms_invalid_date_ranges(self, test_client):
        """Reject check_out <= check_in and incomplete dates with HTTP 400."""
        # Check-out before check-in
        res1 = test_client.get("/api/rooms/search?check_in_date=2027-05-15&check_out_date=2027-05-10")
        assert res1.status_code == 400
        assert "after" in res1.json()["detail"].lower()

        # Same-day range
        res2 = test_client.get("/api/rooms/search?check_in_date=2027-05-15&check_out_date=2027-05-15")
        assert res2.status_code == 400
        assert "after" in res2.json()["detail"].lower()

        # Single date only
        res3 = test_client.get("/api/rooms/search?check_in_date=2027-05-15")
        assert res3.status_code == 400
        assert "both" in res3.json()["detail"].lower()

    def test_search_rooms_by_location(self, test_client):
        """Search rooms by city/location name."""
        res = test_client.get("/api/rooms/search?location=Mumbai")
        assert res.status_code == 200
        rooms = res.json()
        assert len(rooms) > 0
        for r in rooms:
            assert "mumbai" in r["location"].lower() or "mumbai" in r["hotel_name"].lower()

    def test_search_rooms_maintenance_excluded(self, test_client):
        """Rooms under Maintenance (e.g. Room 105) must never be returned in date search."""
        res = test_client.get("/api/rooms/search?check_in_date=2027-06-01&check_out_date=2027-06-05")
        assert res.status_code == 200
        room_numbers = [r["room_no"] for r in res.json()]
        assert 105 not in room_numbers

    def test_search_rooms_overlapping_active_reservation_excluded(self, test_client):
        """Room with active reservation during stay dates must be excluded."""
        # Seed has R001 active on Room 103 from 2026-10-10 to 2026-10-15
        res = test_client.get("/api/rooms/search?check_in_date=2026-10-11&check_out_date=2026-10-14")
        assert res.status_code == 200
        room_numbers = [r["room_no"] for r in res.json()]
        assert 103 not in room_numbers

    def test_search_rooms_future_stay_not_blocked_by_past_or_current_status(self, test_client):
        """A future stay date that does not overlap should return the room even if occupied now."""
        # R001 is on Room 103 for Oct 2026. For Dec 2026, Room 103 must be available.
        res = test_client.get("/api/rooms/search?check_in_date=2026-12-01&check_out_date=2026-12-05")
        assert res.status_code == 200
        room_numbers = [r["room_no"] for r in res.json()]
        assert 103 in room_numbers

    def test_search_rooms_calculates_nights_and_estimated_price(self, test_client):
        """Date-based search calculates nights and estimated total price."""
        res = test_client.get("/api/rooms/search?check_in_date=2027-03-01&check_out_date=2027-03-04")
        assert res.status_code == 200
        rooms = res.json()
        assert len(rooms) > 0
        for r in rooms:
            assert r["nights"] == 3
            assert r["estimated_total_price"] == round(r["rent"] * 3, 2)

    def test_cancellation_restores_room_availability(self, test_client):
        """Cancelling a reservation immediately restores room availability for those dates."""
        c_in = "2027-04-10"
        c_out = "2027-04-15"

        # 1. Create a reservation on Room 303
        book_res = test_client.post("/api/reservations/", json={
            "res_id": "R_AVAIL_TEST",
            "guest_id": "G001",
            "room_no": 303,
            "staff_id": "S006",
            "check_in_date": c_in,
            "check_out_date": c_out,
        })
        assert book_res.status_code in [200, 201]

        # 2. Search during that range: Room 303 must NOT be available
        search1 = test_client.get(f"/api/rooms/search?check_in_date={c_in}&check_out_date={c_out}")
        assert search1.status_code == 200
        assert 303 not in [r["room_no"] for r in search1.json()]

        # 3. Cancel the reservation
        cancel_res = test_client.post("/api/reservations/R_AVAIL_TEST/cancel?caller_guest_id=G001")
        assert cancel_res.status_code == 200

        # 4. Search again: Room 303 must now be available!
        search2 = test_client.get(f"/api/rooms/search?check_in_date={c_in}&check_out_date={c_out}")
        assert search2.status_code == 200
        assert 303 in [r["room_no"] for r in search2.json()]
