"""
Unit tests that run offline without requiring a live Neo4j database instance.
These tests validate Pydantic schemas, business logic validation rules,
FastAPI route registrations, and Cypher script syntax integrity.
"""
import pytest
import os
from datetime import date
from pydantic import ValidationError

from backend.models.schemas import (
    HotelCreate,
    RoomCategoryCreate,
    RoomCreate,
    RoomStatusUpdate,
    DepartmentCreate,
    StaffCreate,
    GuestCreate,
    ReservationCreate,
    RoomSearch,
)
from backend.main import app


class TestPydanticSchemas:
    """Validate data modeling constraints and validation rules."""

    def test_hotel_valid_and_invalid(self):
        hotel = HotelCreate(
            hotel_id="H001",
            name="Grand Palace",
            location="Mumbai",
            rating=4.5
        )
        assert hotel.hotel_id == "H001"
        assert hotel.rating == 4.5

        # Invalid rating > 5
        with pytest.raises(ValidationError):
            HotelCreate(hotel_id="H001", name="Grand", location="Mumbai", rating=5.5)

        # Invalid rating < 0
        with pytest.raises(ValidationError):
            HotelCreate(hotel_id="H001", name="Grand", location="Mumbai", rating=-1.0)

    def test_room_category_validation(self):
        cat = RoomCategoryCreate(category_name="Deluxe", rent=3500.0)
        assert cat.rent == 3500.0

        # Rent must be gt 0
        with pytest.raises(ValidationError):
            RoomCategoryCreate(category_name="Free", rent=0.0)

    def test_room_validation(self):
        room = RoomCreate(
            room_no=101,
            status="Available",
            hotel_id="H001",
            category_name="Deluxe"
        )
        assert room.room_no == 101
        assert room.status == "Available"

        # Room number must be > 0
        with pytest.raises(ValidationError):
            RoomCreate(room_no=0, hotel_id="H001", category_name="Deluxe")

    def test_room_status_update_regex(self):
        valid1 = RoomStatusUpdate(status="Available")
        valid2 = RoomStatusUpdate(status="Occupied")
        valid3 = RoomStatusUpdate(status="Maintenance")
        assert valid1.status == "Available"
        assert valid2.status == "Occupied"
        assert valid3.status == "Maintenance"

        with pytest.raises(ValidationError):
            RoomStatusUpdate(status="UnderRepair")

    def test_guest_gender_regex(self):
        g_male = GuestCreate(
            guest_id="G001",
            name="John Doe",
            contact_info="9876543210",
            nationality="Indian",
            gender="Male"
        )
        assert g_male.gender == "Male"

        with pytest.raises(ValidationError):
            GuestCreate(
                guest_id="G002",
                name="Jane",
                contact_info="123",
                nationality="Indian",
                gender="Alien"
            )

    def test_reservation_schema_parsing(self):
        res = ReservationCreate(
            res_id="R001",
            check_in_date=date(2026, 11, 1),
            check_out_date=date(2026, 11, 5),
            guest_id="G001",
            room_no=101,
            staff_id="S001"
        )
        assert res.res_id == "R001"
        assert res.check_out_date > res.check_in_date


class TestRouteRegistrations:
    """Verify that all required API endpoints are mounted on the FastAPI application."""

    def test_expected_routes_exist(self):
        route_paths = [route.path for route in app.routes]
        
        expected_endpoints = [
            "/api/health",
            "/api/dashboard/stats",
            "/api/dashboard/room-availability",
            "/api/dashboard/recent-reservations",
            "/api/hotels/",
            "/api/hotels/{hotel_id}",
            "/api/rooms/",
            "/api/rooms/categories",
            "/api/rooms/search",
            "/api/guests/",
            "/api/guests/search",
            "/api/reservations/",
            "/api/reservations/{res_id}/cancel",
            "/api/staff/",
            "/api/recommendations/hotels/{guest_id}",
            "/api/recommendations/rooms/{guest_id}",
            "/api/recommendations/popular-by-nationality/{nationality}",
            "/api/recommendations/guest-journey/{guest_id}",
            "/api/graph/data",
        ]
        
        for ep in expected_endpoints:
            assert ep in route_paths, f"Expected endpoint {ep} not found in registered routes"


class TestCypherScriptsIntegrity:
    """Verify all 7 Cypher scripts exist, are non-empty, and contain expected statements."""

    @pytest.fixture
    def cypher_dir(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, "cypher")

    def test_all_seven_cypher_files_exist(self, cypher_dir):
        expected_files = [
            "01_constraints.cypher",
            "02_seed_data.cypher",
            "03_crud_queries.cypher",
            "04_traversal_queries.cypher",
            "05_aggregation_queries.cypher",
            "06_recommendation_queries.cypher",
            "07_reset.cypher",
        ]
        for fname in expected_files:
            fpath = os.path.join(cypher_dir, fname)
            assert os.path.isfile(fpath), f"Missing Cypher file: {fname}"
            content = open(fpath, "r", encoding="utf-8").read()
            assert len(content.strip()) > 50, f"Cypher file {fname} is too short or empty"

    def test_constraints_file_contains_all_entity_constraints(self, cypher_dir):
        fpath = os.path.join(cypher_dir, "01_constraints.cypher")
        content = open(fpath, "r", encoding="utf-8").read()
        for label in ["Hotel", "RoomCategory", "Room", "Department", "Staff", "Guest", "Reservation"]:
            assert label in content, f"Constraint for {label} missing in 01_constraints.cypher"

    def test_seed_data_contains_merge_statements(self, cypher_dir):
        fpath = os.path.join(cypher_dir, "02_seed_data.cypher")
        content = open(fpath, "r", encoding="utf-8").read()
        assert "MERGE" in content, "02_seed_data.cypher must use idempotent MERGE statements"
        assert "HAS_ROOM" in content
        assert "BELONGS_TO" in content
        assert "HAS_DEPARTMENT" in content
        assert "EMPLOYS" in content
        assert "MADE" in content
        assert "BOOKS" in content
        assert "PROCESSES" in content
