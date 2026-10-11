"""
Test guest operations.
"""
import pytest


@pytest.mark.requires_neo4j
class TestGuests:
    def test_list_guests(self, test_client):
        """Verify guest listing."""
        response = test_client.get("/api/guests/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_guests_by_name(self, test_client):
        """Search guests by name."""
        response = test_client.get("/api/guests/search?name=John")
        assert response.status_code == 200
        guests = response.json()
        for g in guests:
            assert "john" in g["name"].lower()

    def test_search_guests_by_nationality(self, test_client):
        """Search guests by nationality."""
        response = test_client.get("/api/guests/search?nationality=Indian")
        assert response.status_code == 200
        guests = response.json()
        for g in guests:
            assert "indian" in g["nationality"].lower()

    def test_get_guest_detail(self, test_client):
        """Get guest with reservation history."""
        response = test_client.get("/api/guests/G001")
        if response.status_code == 404:
            pytest.skip("Guest G001 not in database")
        assert response.status_code == 200
        data = response.json()
        assert data["guest_id"] == "G001"
        assert "reservations" in data

    def test_guest_not_found(self, test_client):
        """Verify 404 for non-existent guest."""
        response = test_client.get("/api/guests/GXXX")
        assert response.status_code == 404

    def test_create_and_verify_guest(self, test_client):
        """Create a new guest and verify it exists."""
        guest_data = {
            "guest_id": "GTEST01",
            "name": "Test User",
            "contact_info": "0000000000",
            "nationality": "TestLand",
            "gender": "Other"
        }
        response = test_client.post("/api/guests/", json=guest_data)
        assert response.status_code == 200

        # Verify
        verify = test_client.get("/api/guests/GTEST01")
        assert verify.status_code == 200
        assert verify.json()["name"] == "Test User"

        # Cleanup: we leave it — it won't affect other tests

    def test_create_duplicate_guest(self, test_client):
        """Attempt to create a duplicate guest."""
        guest_data = {
            "guest_id": "GTEST01",
            "name": "Duplicate User",
            "contact_info": "1111111111",
            "nationality": "TestLand",
            "gender": "Male"
        }
        response = test_client.post("/api/guests/", json=guest_data)
        assert response.status_code == 409
