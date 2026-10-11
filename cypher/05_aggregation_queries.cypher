// ============================================================
// 05_aggregation_queries.cypher
// Hotel Management System — Filtering, Sorting & Aggregation
// ============================================================
// Demonstrates: WHERE, ORDER BY, LIMIT, COUNT, SUM, AVG,
//               COLLECT, WITH, and date-based filtering.
// ============================================================

// --- 1. Filter: Available rooms with rent under 6000 ---
// Expected: Standard (2500) and Deluxe (5000) rooms with 'Available' status.
MATCH (r:Room)-[:BELONGS_TO]->(c:RoomCategory)
WHERE r.status = 'Available' AND c.rent < 6000
RETURN r.room_no AS Room, c.category_name AS Category, c.rent AS Rent
ORDER BY c.rent;

// --- 2. Filter: Rooms in a specific hotel by category ---
// Expected: Rooms in H001 that belong to 'Standard' category.
MATCH (h:Hotel {hotel_id: 'H001'})-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory {category_name: 'Standard'})
RETURN r.room_no AS Room, r.status AS Status, c.rent AS Rent;

// --- 3. Count: Total rooms per hotel ---
// Expected: H001=5, H002=4, H003=3.
MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)
RETURN h.name AS Hotel, COUNT(r) AS TotalRooms
ORDER BY TotalRooms DESC;

// --- 4. Count: Available vs occupied rooms per hotel ---
// Expected: Breakdown of room status by hotel.
MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)
RETURN h.name AS Hotel, r.status AS Status, COUNT(r) AS Count
ORDER BY h.name, r.status;

// --- 5. Aggregation: Average room rent per hotel ---
// Expected: Average rent based on room categories in each hotel.
MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
RETURN h.name AS Hotel, ROUND(AVG(c.rent)) AS AvgRent
ORDER BY AvgRent DESC;

// --- 6. Aggregation: Total potential revenue per hotel (all rooms) ---
// Expected: Sum of rents for all rooms in each hotel.
MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
RETURN h.name AS Hotel, SUM(c.rent) AS TotalDailyRevenue
ORDER BY TotalDailyRevenue DESC;

// --- 7. Aggregation: Staff count per department ---
// Expected: Count of staff in each department.
MATCH (h:Hotel)-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s:Staff)
RETURN h.name AS Hotel, d.d_role AS Department, COUNT(s) AS StaffCount
ORDER BY h.name, d.d_role;

// --- 8. Aggregation: Reservations per guest with COLLECT ---
// Expected: Each guest with a list of their reservation IDs.
MATCH (g:Guest)-[:MADE]->(res:Reservation)
RETURN g.name AS Guest, COLLECT(res.res_id) AS Reservations, COUNT(res) AS Total
ORDER BY Total DESC;

// --- 9. Filter: Active reservations with date range ---
// Expected: Reservations with check-in on or after Oct 10, 2026.
MATCH (g:Guest)-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)
WHERE res.status = 'Active' AND res.check_in_date >= date('2026-10-10')
RETURN g.name AS Guest, res.res_id AS Reservation, r.room_no AS Room,
       res.check_in_date AS CheckIn, res.check_out_date AS CheckOut
ORDER BY res.check_in_date;

// --- 10. Sort and Limit: Top 3 highest-paid staff ---
// Expected: Top 3 staff sorted by salary descending.
MATCH (s:Staff)
RETURN s.name AS Staff, s.salary AS Salary
ORDER BY s.salary DESC
LIMIT 3;

// --- 11. WITH clause: Hotels with more than 3 rooms ---
// Expected: Only Grand Palace Hotel (5 rooms) and Royal Orchid (4 rooms).
MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)
WITH h, COUNT(r) AS roomCount
WHERE roomCount > 3
RETURN h.name AS Hotel, h.location AS Location, roomCount AS RoomCount
ORDER BY roomCount DESC;

// --- 12. Aggregation: Guest nationality distribution ---
// Expected: Count of guests by nationality.
MATCH (g:Guest)
RETURN g.nationality AS Nationality, COUNT(g) AS GuestCount
ORDER BY GuestCount DESC;

// --- 13. Dashboard counts: Total entities ---
// Expected: Summary counts for all entity types.
MATCH (h:Hotel) WITH COUNT(h) AS hotels
MATCH (r:Room) WITH hotels, COUNT(r) AS rooms
MATCH (g:Guest) WITH hotels, rooms, COUNT(g) AS guests
MATCH (s:Staff) WITH hotels, rooms, guests, COUNT(s) AS staff
MATCH (res:Reservation) WITH hotels, rooms, guests, staff, COUNT(res) AS reservations
RETURN hotels AS Hotels, rooms AS Rooms, guests AS Guests,
       staff AS Staff, reservations AS Reservations;
