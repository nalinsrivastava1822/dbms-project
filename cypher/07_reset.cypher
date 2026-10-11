// ============================================================
// 07_reset.cypher
// Hotel Management System — Database Reset
// ============================================================
// WARNING: This script DELETES ALL DATA in the database.
// Only run this if you want to start fresh.
// The Python reset script (scripts/reset.py) will ask for
// confirmation before executing these commands.
// ============================================================

// --- Step 1: Delete all relationships and nodes ---
// DETACH DELETE removes all relationships before deleting nodes.
MATCH (n)
DETACH DELETE n;

// --- Step 2: Drop constraints (optional, for complete reset) ---
// Uncomment these if you also want to remove constraints.
// DROP CONSTRAINT hotel_id_unique IF EXISTS;
// DROP CONSTRAINT room_no_unique IF EXISTS;
// DROP CONSTRAINT category_name_unique IF EXISTS;
// DROP CONSTRAINT dept_id_unique IF EXISTS;
// DROP CONSTRAINT staff_id_unique IF EXISTS;
// DROP CONSTRAINT guest_id_unique IF EXISTS;
// DROP CONSTRAINT res_id_unique IF EXISTS;

// --- Verify empty database ---
MATCH (n)
RETURN COUNT(n) AS RemainingNodes;
// Expected: 0
