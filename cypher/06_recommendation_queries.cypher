// ============================================================
// 06_recommendation_queries.cypher
// Hotel Management System — Graph-Based Recommendations
// ============================================================
// These queries leverage Neo4j's graph traversal capabilities
// to provide recommendations that would be complex in SQL
// (requiring multiple self-joins and subqueries).
// ============================================================

// --- 1. Guest-to-Guest Recommendation ---
// "Recommend hotels to a guest based on where similar guests have stayed"
//
// How it works:
//   (Guest A) → Reservation → Room → Hotel ← Room ← Reservation ← (Guest B)
//   Find other guests who stayed at the SAME hotel as Guest G001,
//   then find OTHER hotels those guests have also visited.
//
// Why graph: This multi-hop traversal is natural in Cypher but requires
//   multiple self-joins on Reservation, Room, and Hotel tables in SQL.
//
// Expected: Hotels visited by guests who also stayed at hotels G001 visited,
//   excluding hotels G001 has already visited.
MATCH (target:Guest {guest_id: 'G001'})-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(commonHotel:Hotel)
MATCH (commonHotel)-[:HAS_ROOM]->(:Room)<-[:BOOKS]-(:Reservation)<-[:MADE]-(otherGuest:Guest)
WHERE otherGuest <> target
MATCH (otherGuest)-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(recommended:Hotel)
WHERE NOT (target)-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(recommended)
RETURN DISTINCT recommended.name AS RecommendedHotel,
       recommended.location AS Location,
       recommended.rating AS Rating,
       COUNT(DISTINCT otherGuest) AS SharedGuestCount
ORDER BY SharedGuestCount DESC, Rating DESC;

// --- 2. Room Category Recommendation ---
// "Recommend room categories to a guest based on their past preferences"
//
// How it works:
//   (Guest) → Reservation → Room → RoomCategory
//   Find categories the guest has booked, then find similar categories
//   (same price range) they haven't tried.
//
// Expected: Room categories the guest hasn't booked, sorted by similarity.
MATCH (g:Guest {guest_id: 'G001'})-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)-[:BELONGS_TO]->(booked:RoomCategory)
WITH g, COLLECT(DISTINCT booked.category_name) AS bookedCategories, AVG(booked.rent) AS avgRent
MATCH (c:RoomCategory)
WHERE NOT c.category_name IN bookedCategories
RETURN c.category_name AS RecommendedCategory,
       c.rent AS Rent,
       ABS(c.rent - avgRent) AS PriceDifference
ORDER BY PriceDifference ASC;

// --- 3. Nationality-Based Hotel Recommendation ---
// "Recommend hotels popular among guests of the same nationality"
//
// How it works:
//   Find all guests of the same nationality → their reservations → hotels
//   Rank hotels by how many compatriots have stayed there.
//
// Expected: Hotels sorted by popularity among Indian guests.
MATCH (g:Guest {guest_id: 'G002'})
WITH g.nationality AS targetNationality
MATCH (peer:Guest {nationality: targetNationality})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
WHERE res.status IN ['Active', 'Completed', 'Confirmed']
RETURN h.name AS Hotel, h.location AS Location, h.rating AS Rating,
       COUNT(DISTINCT peer) AS GuestFromSameCountry,
       COUNT(DISTINCT res) AS TotalBookings
ORDER BY GuestFromSameCountry DESC, TotalBookings DESC;

// --- 4. Staff Workload Analysis (Graph Aggregation) ---
// "Analyze staff workload by traversing through departments and reservations"
//
// How it works:
//   (Hotel) → Department → Staff → Reservation → Room
//   Multi-hop traversal to understand staff utilization across hotels.
//
// Expected: Staff with their hotel, department, and reservation count.
MATCH (h:Hotel)-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s:Staff)
OPTIONAL MATCH (s)-[:PROCESSES]->(res:Reservation)
RETURN h.name AS Hotel, d.d_role AS Department, s.name AS Staff,
       COUNT(res) AS ReservationsProcessed,
       COLLECT(DISTINCT res.status) AS ReservationStatuses
ORDER BY ReservationsProcessed DESC;

// --- 5. Guest Journey Map ---
// "Trace a guest's complete journey through the hotel system"
//
// How it works:
//   (Guest) → Reservation → Room → Hotel
//   (Guest) → Reservation ← Staff → Department → Hotel
//   Combines forward and backward traversals.
//
// Expected: Complete timeline of guest G001's interactions.
MATCH (g:Guest {guest_id: 'G001'})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
MATCH (r)-[:BELONGS_TO]->(c:RoomCategory)
OPTIONAL MATCH (s:Staff)-[:PROCESSES]->(res)
RETURN res.res_id AS Reservation, res.status AS Status,
       res.check_in_date AS CheckIn, res.check_out_date AS CheckOut,
       h.name AS Hotel, r.room_no AS Room, c.category_name AS Category,
       c.rent AS Rent, s.name AS ProcessedBy
ORDER BY res.check_in_date;

// --- 6. Find Connected Components ---
// "Find how entities are interconnected (graph-unique operation)"
//
// How it works:
//   Uses variable-length paths to discover connectivity.
//   This type of query has no direct SQL equivalent.
//
// Expected: Shows how many entities each hotel is connected to.
MATCH (h:Hotel)
OPTIONAL MATCH path = (h)-[*1..4]-(connected)
RETURN h.name AS Hotel,
       COUNT(DISTINCT connected) AS ConnectedEntities,
       COLLECT(DISTINCT labels(connected)[0]) AS ConnectedTypes
ORDER BY ConnectedEntities DESC;
