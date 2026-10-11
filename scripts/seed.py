"""
Idempotent Database Seeder — Seeds the Neo4j database with sample data.
Uses MERGE to prevent duplicate records on re-run.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config import get_driver


def run_constraints(driver):
    """Create uniqueness constraints and indexes."""
    constraints = [
        "CREATE CONSTRAINT hotel_id_unique IF NOT EXISTS FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE",
        "CREATE CONSTRAINT room_no_unique IF NOT EXISTS FOR (r:Room) REQUIRE r.room_no IS UNIQUE",
        "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:RoomCategory) REQUIRE c.category_name IS UNIQUE",
        "CREATE CONSTRAINT dept_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.dept_id IS UNIQUE",
        "CREATE CONSTRAINT staff_id_unique IF NOT EXISTS FOR (s:Staff) REQUIRE s.staff_id IS UNIQUE",
        "CREATE CONSTRAINT guest_id_unique IF NOT EXISTS FOR (g:Guest) REQUIRE g.guest_id IS UNIQUE",
        "CREATE CONSTRAINT res_id_unique IF NOT EXISTS FOR (r:Reservation) REQUIRE r.res_id IS UNIQUE",
    ]
    indexes = [
        "CREATE INDEX hotel_name_idx IF NOT EXISTS FOR (h:Hotel) ON (h.name)",
        "CREATE INDEX hotel_location_idx IF NOT EXISTS FOR (h:Hotel) ON (h.location)",
        "CREATE INDEX room_status_idx IF NOT EXISTS FOR (r:Room) ON (r.status)",
        "CREATE INDEX guest_name_idx IF NOT EXISTS FOR (g:Guest) ON (g.name)",
        "CREATE INDEX guest_nationality_idx IF NOT EXISTS FOR (g:Guest) ON (g.nationality)",
        "CREATE INDEX res_status_idx IF NOT EXISTS FOR (r:Reservation) ON (r.status)",
    ]

    with driver.session() as session:
        for stmt in constraints + indexes:
            session.run(stmt)
    print("[OK] Constraints and indexes created.")


def seed_data(driver):
    """Seed all sample data using MERGE (idempotent)."""

    # --- Hotels ---
    hotels = [
        {"hotel_id": "H001", "name": "Grand Palace Hotel", "location": "Mumbai", "rating": 4.5},
        {"hotel_id": "H002", "name": "Royal Orchid Resort", "location": "Delhi", "rating": 4.2},
        {"hotel_id": "H003", "name": "Seaside Inn", "location": "Goa", "rating": 3.8},
    ]

    # --- Room Categories ---
    categories = [
        {"category_name": "Standard", "rent": 2500},
        {"category_name": "Deluxe", "rent": 5000},
        {"category_name": "Suite", "rent": 10000},
        {"category_name": "Executive", "rent": 7500},
    ]

    # --- Rooms: (room_no, status, hotel_id, category_name) ---
    rooms = [
        (101, "Available", "H001", "Standard"),
        (102, "Available", "H001", "Deluxe"),
        (103, "Occupied", "H001", "Suite"),
        (104, "Available", "H001", "Executive"),
        (105, "Maintenance", "H001", "Standard"),
        (201, "Available", "H002", "Standard"),
        (202, "Occupied", "H002", "Deluxe"),
        (203, "Available", "H002", "Suite"),
        (204, "Available", "H002", "Executive"),
        (301, "Available", "H003", "Standard"),
        (302, "Occupied", "H003", "Deluxe"),
        (303, "Available", "H003", "Suite"),
    ]

    # --- Departments ---
    departments = [
        {"dept_id": "D001", "d_head": "Rajesh Kumar", "d_role": "Front Desk", "contact_info": "9876543210", "hotel_id": "H001"},
        {"dept_id": "D002", "d_head": "Priya Sharma", "d_role": "Housekeeping", "contact_info": "9876543211", "hotel_id": "H001"},
        {"dept_id": "D003", "d_head": "Amit Patel", "d_role": "Front Desk", "contact_info": "9876543212", "hotel_id": "H002"},
        {"dept_id": "D004", "d_head": "Sneha Reddy", "d_role": "Restaurant", "contact_info": "9876543213", "hotel_id": "H002"},
        {"dept_id": "D005", "d_head": "Vikram Singh", "d_role": "Front Desk", "contact_info": "9876543214", "hotel_id": "H003"},
    ]

    # --- Staff ---
    staff_members = [
        {"staff_id": "S001", "name": "Arjun Mehta", "age": 28, "salary": 35000, "contact_info": "9111111111", "dept_id": "D001"},
        {"staff_id": "S002", "name": "Meera Joshi", "age": 32, "salary": 30000, "contact_info": "9222222222", "dept_id": "D001"},
        {"staff_id": "S003", "name": "Rahul Verma", "age": 25, "salary": 32000, "contact_info": "9333333333", "dept_id": "D002"},
        {"staff_id": "S004", "name": "Kavitha Nair", "age": 30, "salary": 28000, "contact_info": "9444444444", "dept_id": "D003"},
        {"staff_id": "S005", "name": "Deepak Rao", "age": 35, "salary": 40000, "contact_info": "9555555555", "dept_id": "D004"},
        {"staff_id": "S006", "name": "Anita Kulkarni", "age": 27, "salary": 33000, "contact_info": "9666666666", "dept_id": "D005"},
    ]

    # --- Guests ---
    guests = [
        {"guest_id": "G001", "name": "John Smith", "contact_info": "1234567890", "nationality": "American", "gender": "Male"},
        {"guest_id": "G002", "name": "Aisha Khan", "contact_info": "2345678901", "nationality": "Indian", "gender": "Female"},
        {"guest_id": "G003", "name": "Carlos Rivera", "contact_info": "3456789012", "nationality": "Mexican", "gender": "Male"},
        {"guest_id": "G004", "name": "Emily Chen", "contact_info": "4567890123", "nationality": "Chinese", "gender": "Female"},
        {"guest_id": "G005", "name": "Ravi Iyer", "contact_info": "5678901234", "nationality": "Indian", "gender": "Male"},
        {"guest_id": "G006", "name": "Sophie Martin", "contact_info": "6789012345", "nationality": "French", "gender": "Female"},
        {"guest_id": "G007", "name": "David Brown", "contact_info": "7890123456", "nationality": "American", "gender": "Male"},
        {"guest_id": "G008", "name": "Nisha Gupta", "contact_info": "8901234567", "nationality": "Indian", "gender": "Female"},
    ]

    # --- Reservations: (res_id, check_in, check_out, status, guest_id, room_no, staff_id) ---
    reservations = [
        ("R001", "2026-10-10", "2026-10-15", "Active", "G001", 103, "S001"),
        ("R002", "2026-10-09", "2026-10-13", "Active", "G002", 202, "S004"),
        ("R003", "2026-10-11", "2026-10-14", "Active", "G003", 302, "S006"),
        ("R004", "2026-09-01", "2026-09-05", "Completed", "G001", 101, "S001"),
        ("R005", "2026-09-10", "2026-09-14", "Completed", "G004", 201, "S004"),
        ("R006", "2026-09-15", "2026-09-20", "Completed", "G002", 102, "S002"),
        ("R007", "2026-08-20", "2026-08-25", "Completed", "G005", 301, "S006"),
        ("R008", "2026-10-20", "2026-10-25", "Cancelled", "G006", 104, "S001"),
        ("R009", "2026-11-01", "2026-11-05", "Confirmed", "G007", 203, "S004"),
    ]

    with driver.session() as session:
        # Hotels
        for h in hotels:
            session.run(
                "MERGE (h:Hotel {hotel_id: $hotel_id}) SET h.name=$name, h.location=$location, h.rating=$rating",
                h,
            )
        print("[OK] Hotels seeded.")

        # Categories
        for c in categories:
            session.run(
                "MERGE (c:RoomCategory {category_name: $category_name}) SET c.rent=$rent",
                c,
            )
        print("[OK] Room categories seeded.")

        # Rooms + relationships
        for room_no, status, hotel_id, cat in rooms:
            session.run(
                """
                MATCH (h:Hotel {hotel_id: $hotel_id})
                MATCH (c:RoomCategory {category_name: $cat})
                MERGE (r:Room {room_no: $room_no})
                SET r.status = $status
                MERGE (h)-[:HAS_ROOM]->(r)
                MERGE (r)-[:BELONGS_TO]->(c)
                """,
                {"room_no": room_no, "status": status, "hotel_id": hotel_id, "cat": cat},
            )
        print("[OK] Rooms seeded.")

        # Departments + relationships
        for d in departments:
            session.run(
                """
                MATCH (h:Hotel {hotel_id: $hotel_id})
                MERGE (d:Department {dept_id: $dept_id})
                SET d.d_head=$d_head, d.d_role=$d_role, d.contact_info=$contact_info
                MERGE (h)-[:HAS_DEPARTMENT]->(d)
                """,
                d,
            )
        print("[OK] Departments seeded.")

        # Staff + relationships
        for s in staff_members:
            session.run(
                """
                MATCH (d:Department {dept_id: $dept_id})
                MERGE (s:Staff {staff_id: $staff_id})
                SET s.name=$name, s.age=$age, s.salary=$salary, s.contact_info=$contact_info
                MERGE (d)-[:EMPLOYS]->(s)
                """,
                s,
            )
        print("[OK] Staff seeded.")

        # Guests
        for g in guests:
            session.run(
                """
                MERGE (g:Guest {guest_id: $guest_id})
                SET g.name=$name, g.contact_info=$contact_info,
                    g.nationality=$nationality, g.gender=$gender
                """,
                g,
            )
        print("[OK] Guests seeded.")

        # Reservations + relationships
        for res_id, ci, co, status, gid, rno, sid in reservations:
            session.run(
                """
                MATCH (g:Guest {guest_id: $guest_id})
                MATCH (r:Room {room_no: $room_no})
                MATCH (s:Staff {staff_id: $staff_id})
                MERGE (res:Reservation {res_id: $res_id})
                SET res.check_in_date = date($check_in),
                    res.check_out_date = date($check_out),
                    res.status = $status
                MERGE (g)-[:MADE]->(res)
                MERGE (res)-[:BOOKS]->(r)
                MERGE (s)-[:PROCESSES]->(res)
                """,
                {
                    "res_id": res_id, "check_in": ci, "check_out": co,
                    "status": status, "guest_id": gid, "room_no": rno, "staff_id": sid,
                },
            )
        print("[OK] Reservations seeded.")


def verify_seed(driver):
    """Print entity counts to verify seeding."""
    with driver.session() as session:
        result = session.run("""
            MATCH (h:Hotel) WITH COUNT(h) AS hotels
            MATCH (r:Room) WITH hotels, COUNT(r) AS rooms
            MATCH (c:RoomCategory) WITH hotels, rooms, COUNT(c) AS categories
            MATCH (d:Department) WITH hotels, rooms, categories, COUNT(d) AS departments
            MATCH (s:Staff) WITH hotels, rooms, categories, departments, COUNT(s) AS staff
            MATCH (g:Guest) WITH hotels, rooms, categories, departments, staff, COUNT(g) AS guests
            MATCH (res:Reservation) WITH hotels, rooms, categories, departments, staff, guests, COUNT(res) AS reservations
            RETURN hotels, rooms, categories, departments, staff, guests, reservations
        """)
        record = result.single()
        print("\n--- Seed Verification ---")
        for key in record.keys():
            print(f"  {key}: {record[key]}")
        print("-------------------------\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Hotel Management System — Database Seeder")
    print("=" * 50)

    driver = get_driver()
    try:
        driver.verify_connectivity()
        print(f"[OK] Connected to Neo4j.\n")

        print("Step 1: Creating constraints and indexes...")
        run_constraints(driver)

        print("\nStep 2: Seeding sample data (idempotent)...")
        seed_data(driver)

        print("\nStep 3: Verifying seed data...")
        verify_seed(driver)

        print("[DONE] Database seeding complete!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nMake sure:")
        print("  1. Neo4j is running")
        print("  2. .env file has correct NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        sys.exit(1)
    finally:
        driver.close()
