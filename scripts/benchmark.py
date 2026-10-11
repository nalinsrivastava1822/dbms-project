"""
Reproducible Benchmark Experiment: Relational SQL (SQLite) vs. Neo4j Graph Traversal.
Compares multi-hop traversal query performance across identical datasets.
Outputs statistics (min, median, max latencies) and markdown table for academic reporting.
"""
import sqlite3
import time
import statistics
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import db
from backend.mock_store import mock_store


def setup_relational_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE hotels (
        hotel_id TEXT PRIMARY KEY,
        name TEXT,
        location TEXT,
        rating REAL
    );

    CREATE TABLE room_categories (
        category_name TEXT PRIMARY KEY,
        rent REAL
    );

    CREATE TABLE rooms (
        room_id TEXT PRIMARY KEY,
        room_no INTEGER,
        status TEXT,
        hotel_id TEXT,
        category_name TEXT,
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id),
        FOREIGN KEY (category_name) REFERENCES room_categories(category_name)
    );

    CREATE TABLE departments (
        dept_id TEXT PRIMARY KEY,
        d_head TEXT,
        d_role TEXT,
        contact_info TEXT,
        hotel_id TEXT,
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
    );

    CREATE TABLE staff (
        staff_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        salary REAL,
        contact_info TEXT,
        dept_id TEXT,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );

    CREATE TABLE guests (
        guest_id TEXT PRIMARY KEY,
        name TEXT,
        contact_info TEXT,
        nationality TEXT,
        gender TEXT
    );

    CREATE TABLE reservations (
        res_id TEXT PRIMARY KEY,
        check_in_date TEXT,
        check_out_date TEXT,
        status TEXT,
        guest_id TEXT,
        room_id TEXT,
        room_no INTEGER,
        staff_id TEXT,
        FOREIGN KEY (guest_id) REFERENCES guests(guest_id),
        FOREIGN KEY (room_id) REFERENCES rooms(room_id),
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
    );

    CREATE INDEX idx_rooms_hotel ON rooms(hotel_id);
    CREATE INDEX idx_reservations_guest ON reservations(guest_id);
    CREATE INDEX idx_reservations_room ON reservations(room_no);
    CREATE INDEX idx_reservations_staff ON reservations(staff_id);
    """)

    # Populate from mock_store to ensure identical datasets
    for h in mock_store.hotels.values():
        cursor.execute("INSERT INTO hotels VALUES (?, ?, ?, ?)", (h["hotel_id"], h["name"], h["location"], h["rating"]))
    for c in mock_store.categories.values():
        cursor.execute("INSERT INTO room_categories VALUES (?, ?)", (c["category_name"], c["rent"]))
    for r in mock_store.rooms.values():
        cursor.execute("INSERT INTO rooms VALUES (?, ?, ?, ?, ?)", (r.get("room_id", f"RM{r['room_no']}"), r["room_no"], r["status"], r["hotel_id"], r["category_name"]))
    for d in mock_store.departments.values():
        cursor.execute("INSERT INTO departments VALUES (?, ?, ?, ?, ?)", (d["dept_id"], d["d_head"], d["d_role"], d["contact_info"], d["hotel_id"]))
    for s in mock_store.staff.values():
        cursor.execute("INSERT INTO staff VALUES (?, ?, ?, ?, ?, ?)", (s["staff_id"], s["name"], s["age"], s["salary"], s["contact_info"], s["dept_id"]))
    for g in mock_store.guests.values():
        cursor.execute("INSERT INTO guests VALUES (?, ?, ?, ?, ?)", (g["guest_id"], g["name"], g["contact_info"], g["nationality"], g["gender"]))
    for res in mock_store.reservations.values():
        cursor.execute("INSERT INTO reservations VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
            res["res_id"], res["check_in_date"], res["check_out_date"], res["status"],
            res["guest_id"], res.get("room_id", f"RM{res['room_no']}"), res["room_no"], res["staff_id"]
        ))
    conn.commit()
    return conn


def run_benchmark():
    print("=" * 70)
    print("DBMS DA3 BENCHMARK: Relational SQL (5-Table Join) vs. Graph Traversal")
    print("=" * 70)

    sql_conn = setup_relational_db()
    cursor = sql_conn.cursor()

    sql_query = """
    SELECT g.guest_id, g.name, res.res_id, r.room_no, rc.category_name, rc.rent, h.name, s.name
    FROM guests g
    JOIN reservations res ON g.guest_id = res.guest_id
    JOIN rooms r ON res.room_no = r.room_no
    JOIN room_categories rc ON r.category_name = rc.category_name
    JOIN hotels h ON r.hotel_id = h.hotel_id
    JOIN staff s ON res.staff_id = s.staff_id
    WHERE g.guest_id = ?;
    """

    cypher_query = """
    MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    MATCH (r)-[:BELONGS_TO]->(rc:RoomCategory)
    MATCH (s:Staff)-[:PROCESSES]->(res)
    RETURN g.guest_id AS guest_id, g.name AS guest_name, res.res_id AS res_id,
           r.room_no AS room_no, rc.category_name AS category, rc.rent AS rent,
           h.name AS hotel_name, s.name AS staff_name
    """

    test_guest_id = "G001"

    # Warm-up phase (5 iterations)
    print("\nExecuting warm-up phase (5 iterations)...")
    for _ in range(5):
        cursor.execute(sql_query, (test_guest_id,))
        _ = cursor.fetchall()
        _ = db.execute_read(cypher_query, {"guest_id": test_guest_id})

    # Benchmark phase (50 iterations)
    iterations = 50
    sql_timings = []
    cypher_timings = []

    print(f"Running {iterations} benchmark iterations per engine...")
    for _ in range(iterations):
        t0 = time.perf_counter()
        cursor.execute(sql_query, (test_guest_id,))
        _ = cursor.fetchall()
        t1 = time.perf_counter()
        sql_timings.append((t1 - t0) * 1000.0)

        t2 = time.perf_counter()
        _ = db.execute_read(cypher_query, {"guest_id": test_guest_id})
        t3 = time.perf_counter()
        cypher_timings.append((t3 - t2) * 1000.0)

    # Compute statistics
    sql_min, sql_med, sql_max = min(sql_timings), statistics.median(sql_timings), max(sql_timings)
    cyp_min, cyp_med, cyp_max = min(cypher_timings), statistics.median(cypher_timings), max(cypher_timings)

    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS SUMMARY (in milliseconds)")
    print("=" * 70)
    print(f"Relational SQL  : Min={sql_min:.3f} ms | Median={sql_med:.3f} ms | Max={sql_max:.3f} ms")
    print(f"Graph (Cypher)  : Min={cyp_min:.3f} ms | Median={cyp_med:.3f} ms | Max={cyp_max:.3f} ms")
    print("=" * 70)

    markdown_table = f"""
### Empirical Benchmark Results: Multi-Hop Traversal (5-Hop Path)

| Database Engine | Query Type | Dataset Size | Min Latency | Median Latency | Max Latency | Traversal Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Relational SQL** | 5-Table Join (`JOIN` x 5) | 47 Rows, 7 Tables | `{sql_min:.3f} ms` | `{sql_med:.3f} ms` | `{sql_max:.3f} ms` | B-Tree Index Scans + Nested Loop Joins |
| **Neo4j / Graph** | Multi-Hop Pattern (`MATCH` 5 edges) | 47 Nodes, 62 Edges | `{cyp_min:.3f} ms` | `{cyp_med:.3f} ms` | `{cyp_max:.3f} ms` | Index-Free Adjacency (Direct Pointer Dereference) |
"""
    print("\nMarkdown Table for DA3 Report:")
    print(markdown_table)
    return {
        "sql_median": sql_med,
        "cypher_median": cyp_med,
        "iterations": iterations,
    }


if __name__ == "__main__":
    run_benchmark()
