// ============================================================
// 01_constraints.cypher
// Hotel Management System — Neo4j Constraints & Indexes
// ============================================================
// Run these BEFORE seeding data to enforce uniqueness.
// These use CREATE CONSTRAINT ... IF NOT EXISTS (Neo4j 4.4+).
// ============================================================

// --- Uniqueness Constraints ---
// Each constraint also creates an implicit index on the property.

CREATE CONSTRAINT hotel_id_unique IF NOT EXISTS
FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE;

CREATE CONSTRAINT room_no_unique IF NOT EXISTS
FOR (r:Room) REQUIRE r.room_no IS UNIQUE;

CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:RoomCategory) REQUIRE c.category_name IS UNIQUE;

CREATE CONSTRAINT dept_id_unique IF NOT EXISTS
FOR (d:Department) REQUIRE d.dept_id IS UNIQUE;

CREATE CONSTRAINT staff_id_unique IF NOT EXISTS
FOR (s:Staff) REQUIRE s.staff_id IS UNIQUE;

CREATE CONSTRAINT guest_id_unique IF NOT EXISTS
FOR (g:Guest) REQUIRE g.guest_id IS UNIQUE;

CREATE CONSTRAINT res_id_unique IF NOT EXISTS
FOR (r:Reservation) REQUIRE r.res_id IS UNIQUE;

// --- Additional Indexes for Query Performance ---

CREATE INDEX hotel_name_idx IF NOT EXISTS
FOR (h:Hotel) ON (h.name);

CREATE INDEX hotel_location_idx IF NOT EXISTS
FOR (h:Hotel) ON (h.location);

CREATE INDEX room_status_idx IF NOT EXISTS
FOR (r:Room) ON (r.status);

CREATE INDEX guest_name_idx IF NOT EXISTS
FOR (g:Guest) ON (g.name);

CREATE INDEX guest_nationality_idx IF NOT EXISTS
FOR (g:Guest) ON (g.nationality);

CREATE INDEX res_status_idx IF NOT EXISTS
FOR (r:Reservation) ON (r.status);

CREATE INDEX res_checkin_idx IF NOT EXISTS
FOR (r:Reservation) ON (r.check_in_date);

CREATE INDEX res_checkout_idx IF NOT EXISTS
FOR (r:Reservation) ON (r.check_out_date);
