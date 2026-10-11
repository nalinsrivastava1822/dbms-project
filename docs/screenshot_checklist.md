# Screenshot Capture Checklist — Hotel Management System (Neo4j)
## DBMS Digital Assignment 3 (DA3) — Academic Submission Artifacts

Capture the following screenshots from your actual running application and paste or attach them to your handwritten report, lab record, or viva presentation slide deck.

---

## 📸 Checklist Summary

| # | Item Description | Source View / URL | What to Highlight in Screenshot | Report Section |
|---|---|---|---|---|
| **SS-01** | Backend Startup & Neo4j Connection | PowerShell / VS Code Terminal | Server running on `http://127.0.0.1:8000`, successful driver connection | Section 4: Implementation |
| **SS-02** | Main Dashboard & Key Metrics | Browser: `http://localhost:8000` | Metric cards: 3 Hotels, 15 Rooms, 10 Guests, 6 Staff, 12 Reservations | Section 4 & 8: Results |
| **SS-03** | Room Availability Breakdown | Browser: Dashboard tab | Bar visualization showing available vs occupied rooms per hotel | Section 5: Query Aggregations |
| **SS-04** | Room Directory & Filter in Action | Browser: `Rooms` tab | Filter controls (Hotel dropdown, Max rent slider, Status radio buttons) | Section 5: CRUD & Search |
| **SS-05** | Guest Directory & Booking History | Browser: `Guests` tab | Guest G001 profile showing full traversed reservation history table | Section 5: Multi-hop Traversal |
| **SS-06** | Creating a New Reservation | Browser: `Reservations` tab | Form fields populated (Guest ID, Room, Check-in, Check-out, Staff) | Section 5: Core Transactions |
| **SS-07** | Booking Collision Prevention | Browser: `Reservations` tab | Red error modal/banner: *"Room has an overlapping reservation during this period"* | Section 5 & 8: ACID Integrity |
| **SS-08** | Collaborative Recommendation Engine | Browser: `Recommendations` tab | Recommendations card for Guest G001 showing peer endorsements & hotels | Section 5: Graph Feature |
| **SS-09** | Interactive Graph Network Visualizer | Browser: `Graph Visualizer` tab (`http://localhost:8000`) or Neo4j Browser (`http://localhost:7474`) | Visual force-directed nodes (Hotels, Rooms, Guests, Staff, Reservations) with physics and labeled directed relationship edges | Section 3: Graph Model |
| **SS-10** | Automated Test Suite Execution | PowerShell / VS Code Terminal | Output of `pytest -v` showing green passed unit tests (52 passed) and summary | Section 8: Verification |
| **SS-11** | Staff Directory & Data Input Modal | Browser: `Staff` tab (`http://localhost:8000`) | Staff directory table and interactive "➕ Add Staff" modal form | Section 4: CRUD & Modules |
| **SS-12** | Empirical Benchmark Execution | PowerShell / VS Code Terminal | Output of `python scripts/benchmark.py` showing 50-iteration SQL vs Graph timings | Section 6: Comparative Analysis |

---

## 🔍 Detailed Instructions for Each Screenshot

### SS-01: Terminal Backend Launch
- **Command to Run**:
  ```powershell
  uvicorn backend.main:app --reload --port 8000
  ```
- **What to Capture**:
  - The Uvicorn log showing `Application startup complete.`
  - The local listening address `http://127.0.0.1:8000`.

---

### SS-02: Dashboard Overview
- **Action**: Open `http://localhost:8000` in full screen.
- **What to Capture**:
  - The header banner with title: *"Hotel Management System — Graph Database (Neo4j)"*.
  - The green status badge: **"Neo4j Connected"** (or simulation mode).
  - The 5 metric counters (**Hotels: 3**, **Rooms: 15**, **Guests: 10**, **Staff: 6**, **Reservations: 12**).

---

### SS-03: Room Availability Chart / Cards
- **Action**: Scroll to the *"Room Availability by Hotel"* section on the Dashboard.
- **What to Capture**:
  - Breakdown bars for Grand Palace Hotel (Mumbai), Royal Heritage Hotel (Jaipur), and Seaside Palms Resort (Goa).
  - Legend indicating Available vs. Occupied rooms.

---

### SS-04: Filtered Room Inventory
- **Action**: Go to the **Rooms** tab.
  - Select Hotel: **"Grand Palace Hotel"**.
  - Status: **"Available"**.
  - Set Max Rent slider to: **₹6,000**.
- **What to Capture**:
  - The filter toolbar at the top.
  - The filtered table below showing matching room numbers, category, rent, and status.

---

### SS-05: Guest Profile with Multi-Hop Booking History
- **Action**: Go to the **Guests** tab and click on **Guest G001 (Aditi Rao)**.
- **What to Capture**:
  - Guest demographic details (Nationality: Indian, Gender: Female, Contact).
  - The **Reservation History** table showing:
    - Reservation ID (e.g., `R001`)
    - Hotel Name (e.g., `Grand Palace Hotel`)
    - Room No & Category (e.g., `101 Deluxe Suite`)
    - Nightly Rent (e.g., `₹5,500`)
    - Booking Dates & Staff Handler

---

### SS-06: New Reservation Modal / Form
- **Action**: Go to the **Reservations** tab and click **"+ New Reservation"**.
- **What to Capture**:
  - The modal populated with valid data:
    - Guest ID: `G003`
    - Room No: `102`
    - Staff ID: `S001`
    - Check-in: `2026-12-01`
    - Check-out: `2026-12-05`
  - The "Confirm Booking" button.

---

### SS-07: Overlapping Booking Conflict Alert
- **Action**:
  - Attempt to book Room `102` again with overlapping dates (e.g., `2026-12-03` to `2026-12-08`).
  - Submit the form.
- **What to Capture**:
  - The red error notification banner showing:
    `"Error: Room 102 is already booked for the selected date interval."`
  - This proves strict ACID concurrency validation.

---

### SS-08: Guest Collaborative Recommendations
- **Action**: Go to the **Recommendations** tab.
  - Select Guest: **Aditi Rao (G001)**.
  - Click **"Generate Recommendations"**.
- **What to Capture**:
  - The recommendation cards displaying suggested hotels (e.g., Royal Heritage Hotel, Seaside Palms Resort).
  - Peer endorsement counts and suggested room categories.
  - The explanation box describing the multi-hop collaborative filtering path.

---

### SS-09: Interactive Graph Visualizer & Topology
- **Action Option A (Built-in Web Dashboard)**:
  - Open `http://localhost:8000` and click the **Graph Visualizer** tab in the sidebar.
  - Explore the interactive force-directed graph with physics, showing circular nodes (Hotels in Red, Rooms in Blue, Guests in Green, Staff in Amber, Reservations in Pink, Departments in Teal).
  - Click on a node (e.g., Grand Palace Hotel or a Guest) to open the Node Inspector card.
  - Click **"📸 Export PNG"** in the top right to download a high-resolution screenshot directly!
- **Action Option B (Neo4j Browser)**:
  - Open `http://localhost:7474`.
  - Run the Cypher query:
    ```cypher
    MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50;
    ```
- **What to Capture**:
  - The circular network nodes, directed relationship arrows (`HAS_ROOM`, `BELONGS_TO`, `MADE`, `BOOKS`, `PROCESSES`, `EMPLOYS`), and legend.

---

### SS-10: Automated Test Results
- **Action**: In your PowerShell terminal, run:
  ```powershell
  pytest -v
  ```
- **What to Capture**:
  - The green test execution summary:
    `52 passed, 2 skipped in 9.48s`
  - Showing unit schema tests, route tests, concurrency isolation tests, and Cypher integrity checks passing.

---

### SS-11: Staff Directory & Live Input Modal
- **Action**: Open `http://localhost:8000` and click the **Staff** tab.
  - Click the **"➕ Add Staff"** button to open the modal dialog.
  - Fill out sample fields (Staff ID: `S007`, Name: `Meera Nair`, Department: `Front Desk`).
- **What to Capture**:
  - The glassmorphism modal popup overlaid on the staff directory table showing department assignments.

---

### SS-12: Empirical Benchmark Comparison Output
- **Action**: In your PowerShell terminal, run:
  ```powershell
  python scripts/benchmark.py
  ```
- **What to Capture**:
  - The printed terminal benchmark table showing 50-run median latency:
    `Relational SQL: 0.007 ms` vs `Neo4j/Graph: 0.004 ms` for the 5-hop path traversal.
