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
