"""
Test hotel operations.
"""
import pytest


@pytest.mark.requires_neo4j
class TestHotels:
    def test_list_hotels(self, test_client):
        """Verify hotel listing returns data."""
        response = test_client.get("/api/hotels/")
        assert response.status_code == 200
        hotels = response.json()
        assert isinstance(hotels, list)

    def test_get_hotel_detail(self, test_client):
        """Verify hotel detail with rooms and departments."""
        response = test_client.get("/api/hotels/H001")
        if response.status_code == 404:
            pytest.skip("Hotel H001 not in database — seed data may not be loaded")
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_id"] == "H001"
        assert "rooms" in data
        assert "departments" in data

    def test_get_hotel_not_found(self, test_client):
        """Verify 404 for non-existent hotel."""
        response = test_client.get("/api/hotels/HXXX")
        assert response.status_code == 404

    def test_hotel_rooms(self, test_client):
        """Verify hotel rooms endpoint."""
        response = test_client.get("/api/hotels/H001/rooms")
        assert response.status_code == 200
        rooms = response.json()
        assert isinstance(rooms, list)

    def test_hotel_departments(self, test_client):
        """Verify hotel departments endpoint."""
        response = test_client.get("/api/hotels/H001/departments")
        assert response.status_code == 200
        depts = response.json()
        assert isinstance(depts, list)
