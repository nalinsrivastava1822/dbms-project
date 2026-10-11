"""
Test dashboard aggregate endpoints.
"""
import pytest


@pytest.mark.requires_neo4j
class TestDashboard:
    def test_dashboard_stats(self, test_client):
        """Verify dashboard stats return expected keys."""
        response = test_client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        for key in ["hotels", "rooms", "guests", "staff", "reservations"]:
            assert key in data
            assert isinstance(data[key], int)
            assert data[key] >= 0

    def test_room_availability(self, test_client):
        """Verify room availability breakdown."""
        response = test_client.get("/api/dashboard/room-availability")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for hotel in data:
            assert "hotel_name" in hotel
            assert "available" in hotel
            assert "occupied" in hotel
            assert "total" in hotel
            assert hotel["total"] == hotel["available"] + hotel["occupied"] + hotel["maintenance"]

    def test_recent_reservations(self, test_client):
        """Verify recent reservations endpoint."""
        response = test_client.get("/api/dashboard/recent-reservations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # Limited to 10
        for res in data:
            assert "res_id" in res
            assert "guest_name" in res
            assert "status" in res
