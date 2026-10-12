"""
Test guest operations.
"""
import pytest
import os


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

    def test_get_next_guest_id(self, test_client):
        """Verify sequential next guest ID endpoint."""
        response = test_client.get("/api/guests/next-id")
        assert response.status_code == 200
        data = response.json()
        assert "next_id" in data
        assert data["next_id"].startswith("G")

    def test_guest_login_existing(self, test_client):
        """Verify logging in with an existing guest and password."""
        response = test_client.post("/api/guests/login", json={"name": "John Smith", "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_new"] is False
        assert data["guest"]["name"] == "John Smith"

    def test_guest_login_new_registration(self, test_client):
        """Verify registering a new guest through login endpoint."""
        payload = {
            "name": "AutoRegistered Guest",
            "email": "autoreg@hotelms.com",
            "phone": "555-0199",
            "password": "securepassword123",
            "nationality": "Canadian",
            "gender": "Female",
            "action": "register"
        }
        response = test_client.post("/api/guests/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_new"] is True
        assert data["guest"]["name"] == "AutoRegistered Guest"
        assert data["guest"]["nationality"] == "Canadian"
        assert data["guest"]["guest_id"].startswith("G")

        # Verify guest is present in general guest list
        list_res = test_client.get("/api/guests/")
        assert list_res.status_code == 200
        guest_names = [g["name"] for g in list_res.json()]
        assert "AutoRegistered Guest" in guest_names

    # =========================================================================
    # Required Regression & Feature Tests for Guest Login & Security
    # =========================================================================

    def test_1_existing_guest_login_with_valid_credentials(self, test_client):
        """1. Existing guest can log in successfully with valid credentials."""
        # By Guest ID + password
        res_id = test_client.post("/api/guests/login", json={"guest_id": "G001", "password": "password123"})
        assert res_id.status_code == 200
        d_id = res_id.json()
        assert d_id["success"] is True
        assert d_id["is_new"] is False
        assert d_id["guest"]["guest_id"] == "G001"
        assert d_id["guest"]["name"] == "John Smith"
        assert d_id.get("role") == "guest"

        # By existing contact info / phone + password
        res_phone = test_client.post("/api/guests/login", json={"phone": "1234567890", "password": "password123"})
        assert res_phone.status_code == 200
        d_phone = res_phone.json()
        assert d_phone["success"] is True
        assert d_phone["is_new"] is False
        assert d_phone["guest"]["guest_id"] == "G001"

        # By Guest ID + matching name + password
        res_both = test_client.post("/api/guests/login", json={"guest_id": "G001", "name": "John Smith", "password": "password123"})
        assert res_both.status_code == 200
        assert res_both.json()["guest"]["name"] == "John Smith"

    def test_2_new_guest_register_and_login_flow(self, test_client):
        """2. New guest can register/create an account and then log in successfully."""
        new_guest_payload = {
            "name": "Liam Neeson",
            "email": "liam.neeson@action.org",
            "phone": "555-0188",
            "password": "LiamPassword99",
            "nationality": "Irish",
            "gender": "Male",
            "action": "register"
        }
        # First registration
        reg_res = test_client.post("/api/guests/login", json=new_guest_payload)
        assert reg_res.status_code == 200
        reg_data = reg_res.json()
        assert reg_data["success"] is True
        assert reg_data["is_new"] is True
        assigned_id = reg_data["guest"]["guest_id"]
        assert assigned_id.startswith("G")
        assert reg_data["guest"]["name"] == "Liam Neeson"

        # Subsequent login using email and password
        login_res = test_client.post("/api/guests/login", json={"email": "liam.neeson@action.org", "password": "LiamPassword99"})
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert login_data["success"] is True
        assert login_data["is_new"] is False
        assert login_data["guest"]["guest_id"] == assigned_id

    def test_3_repeated_requests_do_not_create_duplicates(self, test_client):
        """3. Repeated requests for the same guest do not create duplicate Guest nodes."""
        payload = {
            "name": "Repeat Tester",
            "email": "repeat.tester@hotelms.com",
            "phone": "555-4321",
            "password": "repeatpass123",
            "nationality": "Indian",
            "gender": "Female"
        }
        # First call
        r1 = test_client.post("/api/guests/login", json=payload)
        assert r1.status_code == 200
        gid1 = r1.json()["guest"]["guest_id"]

        # Second call with same email
        r2 = test_client.post("/api/guests/login", json=payload)
        assert r2.status_code == 200
        assert r2.json()["is_new"] is False
        assert r2.json()["guest"]["guest_id"] == gid1

        # Third call
        r3 = test_client.post("/api/guests/login", json=payload)
        assert r3.status_code == 200
        assert r3.json()["is_new"] is False
        assert r3.json()["guest"]["guest_id"] == gid1

        # Verify in database: exactly ONE guest exists with this name and contact info
        list_all = test_client.get("/api/guests/").json()
        matches = [g for g in list_all if g.get("name") == "Repeat Tester"]
        assert len(matches) == 1, f"Expected 1 guest node, found {len(matches)}"

    def test_4_invalid_or_incomplete_input_rejected(self, test_client):
        """4. Invalid or incomplete input is rejected."""
        # A. Empty payload
        empty_res = test_client.post("/api/guests/login", json={})
        assert empty_res.status_code == 400
        assert "required" in empty_res.json()["detail"].lower()

        # B. Invalid email format
        bad_email = test_client.post("/api/guests/login", json={"email": "not-an-email", "password": "pass"})
        assert bad_email.status_code == 400
        assert "invalid email" in bad_email.json()["detail"].lower()

        # C. Invalid phone format
        bad_phone = test_client.post("/api/guests/login", json={"phone": "12", "password": "pass"})
        assert bad_phone.status_code == 400
        assert "invalid phone" in bad_phone.json()["detail"].lower()

        # D. Missing password when attempting to login merely with email/phone/id
        no_pw = test_client.post("/api/guests/login", json={"email": "nobody_exists@unknown.com"})
        assert no_pw.status_code == 401
        assert "password is required" in no_pw.json()["detail"].lower()

        # E. Missing name when trying to register a new guest with an unrecognized identifier
        missing_name = test_client.post("/api/guests/login", json={"email": "nobody_exists@unknown.com", "password": "validpassword"})
        assert missing_name.status_code == 400
        assert "name is required" in missing_name.json()["detail"].lower()

    def test_5_incorrect_credentials_do_not_grant_access(self, test_client):
        """5. Incorrect credentials do not grant access."""
        # A. Non-existent guest ID in explicit login mode
        bad_id = test_client.post("/api/guests/login", json={"guest_id": "G9999", "password": "anypassword", "action": "login"})
        assert bad_id.status_code == 401
        assert "not found" in bad_id.json()["detail"].lower() or "invalid credentials" in bad_id.json()["detail"].lower()

        # B. Non-existent email in explicit login mode
        bad_login_email = test_client.post("/api/guests/login", json={
            "email": "ghost_guest@nowhere.org",
            "password": "anypassword",
            "action": "login"
        })
        assert bad_login_email.status_code == 401

        # C. Guest ID with wrong name (credential mismatch)
        mismatch = test_client.post("/api/guests/login", json={
            "guest_id": "G001",
            "name": "Completely Wrong Person",
            "password": "password123"
        })
        assert mismatch.status_code == 401
        assert "not match" in mismatch.json()["detail"].lower()

        # D. Incorrect password for existing guest
        wrong_pw = test_client.post("/api/guests/login", json={
            "guest_id": "G001",
            "password": "completely_wrong_password"
        })
        assert wrong_pw.status_code == 401
        assert "incorrect password" in wrong_pw.json()["detail"].lower()

        # E. Do not authenticate merely on entering an email, phone, or guest ID
        just_id = test_client.post("/api/guests/login", json={"guest_id": "G001"})
        assert just_id.status_code == 401
        just_email = test_client.post("/api/guests/login", json={"email": "john@example.com"})
        assert just_email.status_code == 401

    def test_6_db_connection_failures_return_error_without_false_success(self, test_client):
        """6. Neo4j connection failures return a useful error without falsely reporting successful login."""
        from unittest.mock import patch

        # Simulate database failure during write transaction
        with patch("backend.routers.guests.db.run_write_transaction", side_effect=RuntimeError("Neo4j database connection lost")):
            res = test_client.post("/api/guests/login", json={
                "name": "Database Failure Test",
                "email": "dbfail@hotelms.com",
                "password": "testpassword123",
                "action": "register"
            })
            # Must return error, never report success
            assert res.status_code in [500, 503]
            assert "database" in res.json()["detail"].lower()

    def test_7_concurrent_requests_for_same_guest_do_not_create_duplicates(self, test_client):
        """7. Concurrent requests for the same new guest do not create duplicates."""
        from concurrent.futures import ThreadPoolExecutor

        guest_payload = {
            "name": "Parallel Guest",
            "email": "parallel.concurrent@hotelms.com",
            "phone": "555-7799",
            "password": "parallelpass123",
            "nationality": "Indian",
            "gender": "Female"
        }

        def submit_login():
            return test_client.post("/api/guests/login", json=guest_payload)

        # 4 concurrent requests
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(submit_login) for _ in range(4)]
            results = [f.result() for f in futures]

        # All requests must complete successfully
        for r in results:
            assert r.status_code == 200
            assert r.json()["success"] is True

        # All must have received the exact same guest_id
        gids = {r.json()["guest"]["guest_id"] for r in results}
        assert len(gids) == 1, f"Expected exactly 1 shared guest_id, got {gids}"

        # Verify database only contains 1 guest node for this email
        list_all = test_client.get("/api/guests/").json()
        matches = [g for g in list_all if g.get("contact_info") and "parallel.concurrent@hotelms.com" in g["contact_info"]]
        assert len(matches) == 1, f"Expected 1 guest node in DB, found {len(matches)}"

    def test_8_guest_login_does_not_grant_access_to_admin_or_staff_routes(self, test_client):
        """8. Guest login does not grant access to admin or staff routes."""
        # A. Guest login response role is "guest"
        res = test_client.post("/api/guests/login", json={"guest_id": "G001", "password": "password123"})
        assert res.status_code == 200
        data = res.json()
        assert data.get("role") == "guest"
        assert data.get("role") != "admin"
        assert data.get("role") != "staff"

        # B. Verify Auth definition restricts guest access:
        import os
        auth_js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "js", "auth.js")
        with open(auth_js_path, "r", encoding="utf-8") as f:
            auth_content = f.read()

        assert "guest: ['dashboard', 'hotels', 'rooms', 'guests', 'reservations', 'recommendations', 'graph']" in auth_content
        assert "'staff'" not in auth_content.split("guest:")[1].split("]")[0]

    # =========================================================================
    # Phase 3 & 4: Self-Service & IDOR Security Tests
    # =========================================================================

    def test_idor_unauthorized_guest_cannot_view_another_guest_data(self, test_client):
        """Prevent a guest from viewing another guest's profile or reservations (IDOR protection)."""
        # G001 trying to view G002 profile
        forbidden_profile = test_client.get("/api/guests/G002?caller_guest_id=G001")
        assert forbidden_profile.status_code == 403
        assert "forbidden" in forbidden_profile.json()["detail"].lower()

        # G001 trying to view G002 reservations
        forbidden_res = test_client.get("/api/guests/G002/reservations?caller_guest_id=G001")
        assert forbidden_res.status_code == 403
        assert "forbidden" in forbidden_res.json()["detail"].lower()

        # G001 viewing own profile succeeds
        own_profile = test_client.get("/api/guests/G001?caller_guest_id=G001")
        assert own_profile.status_code == 200

        # G001 viewing own reservations succeeds
        own_res = test_client.get("/api/guests/G001/reservations?caller_guest_id=G001")
        assert own_res.status_code == 200
        assert "upcoming" in own_res.json()
        assert "completed" in own_res.json()
        assert "cancelled" in own_res.json()

    def test_idor_unauthorized_guest_cannot_cancel_another_guest_reservation(self, test_client):
        """Prevent a guest from cancelling a reservation belonging to another guest."""
        # G001 has active reservation R001. G002 tries to cancel it.
        forbidden_cancel = test_client.post("/api/reservations/R001/cancel?caller_guest_id=G002")
        assert forbidden_cancel.status_code == 403
        assert "own account" in forbidden_cancel.json()["detail"].lower()
