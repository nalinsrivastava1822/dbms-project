// ============================================================
// 04_traversal_queries.cypher
// Hotel Management System — Relationship Traversal
// ============================================================
// Demonstrates multi-hop traversal across 4+ node types,
// OPTIONAL MATCH, and path queries.
// ============================================================

// --- 1. Two-hop: Hotel → Room → RoomCategory ---
// "List all rooms in Grand Palace Hotel with their category and rent"
// Expected: 5 rooms with their category names and rents.
MATCH (h:Hotel {hotel_id: 'H001'})-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
RETURN r.room_no AS Room, r.status AS Status, c.category_name AS Category, c.rent AS Rent
ORDER BY r.room_no;

// --- 2. Three-hop: Hotel → Department → Staff ---
// "List all staff working at Royal Orchid Resort with their department"
// Expected: Staff S004 (Kavitha, Front Desk) and S005 (Deepak, Restaurant).
MATCH (h:Hotel {hotel_id: 'H002'})-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s:Staff)
RETURN s.staff_id AS StaffID, s.name AS Staff, d.d_role AS Department, d.d_head AS DeptHead
ORDER BY s.staff_id;

// --- 3. Three-hop: Guest → Reservation → Room ---
// "Show all rooms that John Smith (G001) has ever booked"
// Expected: Rooms 103 (Active, R001) and 101 (Completed, R004).
MATCH (g:Guest {guest_id: 'G001'})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)
RETURN res.res_id AS ReservationID, r.room_no AS Room, res.status AS Status,
       res.check_in_date AS CheckIn, res.check_out_date AS CheckOut
ORDER BY res.check_in_date;

// --- 4. Four-hop: Guest → Reservation → Room → Hotel ---
// "Which hotels has each guest visited?"
// Traverses four node types in a single query.
// Expected: Shows guest-hotel pairs based on reservation history.
MATCH (g:Guest)-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
RETURN g.name AS Guest, COLLECT(DISTINCT h.name) AS HotelsVisited
ORDER BY g.name;

// --- 5. Four-hop: Hotel → Room → Reservation ← Staff ---
// "Which staff processed reservations for rooms in Grand Palace Hotel?"
// Expected: Links staff to specific rooms in H001 through reservations.
MATCH (h:Hotel {hotel_id: 'H001'})-[:HAS_ROOM]->(r:Room)<-[:BOOKS]-(res:Reservation)<-[:PROCESSES]-(s:Staff)
RETURN s.name AS Staff, r.room_no AS Room, res.res_id AS Reservation, res.status AS Status
ORDER BY r.room_no;

// --- 6. Five-hop: Hotel → Department → Staff → Reservation → Room → RoomCategory ---
// "Full chain: Hotels, their staff, the reservations they processed, rooms booked, and category"
// Expected: Complete operational view spanning all node types.
MATCH (h:Hotel)-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s:Staff)-[:PROCESSES]->(res:Reservation)-[:BOOKS]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
RETURN h.name AS Hotel, s.name AS Staff, res.res_id AS Reservation,
       r.room_no AS Room, c.category_name AS Category
ORDER BY h.name, s.name;

// --- 7. OPTIONAL MATCH: Guests with and without reservations ---
// "List all guests; show reservation count (including 0 for guests with none)"
// Expected: All 8 guests listed. Guests G003 has 1 reservation. G008 has 0.
MATCH (g:Guest)
OPTIONAL MATCH (g)-[:MADE]->(res:Reservation)
RETURN g.guest_id AS GuestID, g.name AS Guest,
       COUNT(res) AS TotalReservations
ORDER BY TotalReservations DESC, g.name;

// --- 8. OPTIONAL MATCH: Rooms without any reservation ---
// "Find rooms that have never been booked"
// Expected: May include rooms like 105 (Maintenance).
MATCH (r:Room)
OPTIONAL MATCH (r)<-[:BOOKS]-(res:Reservation)
WITH r, COUNT(res) AS bookings
WHERE bookings = 0
RETURN r.room_no AS UnbookedRoom, r.status AS Status;

// --- 9. OPTIONAL MATCH: Staff who have not processed any reservations ---
// Expected: Staff S003 and S005 have not processed any reservations.
MATCH (s:Staff)
OPTIONAL MATCH (s)-[:PROCESSES]->(res:Reservation)
WITH s, COUNT(res) AS processed
WHERE processed = 0
RETURN s.staff_id AS StaffID, s.name AS Staff;

// --- 10. Variable-length path: Connected components ---
// "Find all entities reachable from Grand Palace Hotel within 3 hops"
// Expected: Shows the subgraph around H001.
MATCH path = (h:Hotel {hotel_id: 'H001'})-[*1..3]-(connected)
RETURN DISTINCT labels(connected)[0] AS NodeType,
       COUNT(DISTINCT connected) AS Count
ORDER BY NodeType;
