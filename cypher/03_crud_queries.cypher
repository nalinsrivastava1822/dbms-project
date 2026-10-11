// ============================================================
// 03_crud_queries.cypher
// Hotel Management System — CRUD Operations
// ============================================================
// Demonstrates: CREATE, MATCH, RETURN, SET, DELETE
// ============================================================

// --- CREATE: Add a new guest ---
// Expected: Creates guest G009 with specified properties.
CREATE (g:Guest {
  guest_id: 'G009',
  name: 'Takeshi Yamamoto',
  contact_info: '9012345678',
  nationality: 'Japanese',
  gender: 'Male'
})
RETURN g;

// --- MATCH + RETURN: Retrieve all hotels ---
// Expected: Returns 3 hotels (H001, H002, H003) with all properties.
MATCH (h:Hotel)
RETURN h.hotel_id AS ID, h.name AS Name, h.location AS Location, h.rating AS Rating
ORDER BY h.hotel_id;

// --- MATCH + RETURN: Get a specific guest by ID ---
// Expected: Returns guest G001 (John Smith).
MATCH (g:Guest {guest_id: 'G001'})
RETURN g.name AS Name, g.contact_info AS Contact, g.nationality AS Nationality;

// --- SET: Update hotel rating ---
// Expected: Grand Palace Hotel rating changes to 4.7.
MATCH (h:Hotel {hotel_id: 'H001'})
SET h.rating = 4.7
RETURN h.name AS Hotel, h.rating AS NewRating;

// --- SET: Update room status ---
// Expected: Room 101 status changes to 'Maintenance'.
MATCH (r:Room {room_no: 101})
SET r.status = 'Maintenance'
RETURN r.room_no AS Room, r.status AS Status;

// --- DELETE: Remove a cancelled reservation ---
// First, detach delete removes the node AND all its relationships.
// Expected: Reservation R008 (Cancelled) is removed.
MATCH (r:Reservation {res_id: 'R008'})
DETACH DELETE r;

// --- DELETE: Remove a guest with no reservations ---
// Safe deletion: only deletes if guest has no relationships.
// Expected: If G009 has no relationships, it is deleted.
MATCH (g:Guest {guest_id: 'G009'})
WHERE NOT (g)-[:MADE]->()
DELETE g;

// --- Verify deletion ---
// Expected: G009 should not appear; R008 should not appear.
MATCH (g:Guest {guest_id: 'G009'}) RETURN g;
MATCH (r:Reservation {res_id: 'R008'}) RETURN r;
