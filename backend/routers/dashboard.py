"""
Dashboard API — Aggregate statistics for the hotel management system.
"""
from fastapi import APIRouter, HTTPException
from backend.database import db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats():
    """Return aggregate counts for all entity types."""
    try:
        query = """
        MATCH (h:Hotel) WITH COUNT(h) AS hotels
        MATCH (r:Room) WITH hotels, COUNT(r) AS rooms
        MATCH (g:Guest) WITH hotels, rooms, COUNT(g) AS guests
        MATCH (s:Staff) WITH hotels, rooms, guests, COUNT(s) AS staff
        MATCH (res:Reservation) WITH hotels, rooms, guests, staff, COUNT(res) AS reservations
        RETURN hotels, rooms, guests, staff, reservations
        """
        result = db.execute_read(query)
        return result[0] if result else {
            "hotels": 0, "rooms": 0, "guests": 0, "staff": 0, "reservations": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/room-availability")
def get_room_availability():
    """Return available vs unavailable room counts per hotel."""
    try:
        query = """
        MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)
        RETURN h.hotel_id AS hotel_id, h.name AS hotel_name,
               SUM(CASE WHEN r.status = 'Available' THEN 1 ELSE 0 END) AS available,
               SUM(CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END) AS occupied,
               SUM(CASE WHEN r.status = 'Maintenance' THEN 1 ELSE 0 END) AS maintenance,
               COUNT(r) AS total
        ORDER BY h.name
        """
        return db.execute_read(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-reservations")
def get_recent_reservations():
    """Return the 10 most recent reservations with guest and room details."""
    try:
        query = """
        MATCH (g:Guest)-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
        OPTIONAL MATCH (s:Staff)-[:PROCESSES]->(res)
        RETURN res.res_id AS res_id, g.name AS guest_name, r.room_no AS room_no,
               h.name AS hotel_name, res.check_in_date AS check_in_date,
               res.check_out_date AS check_out_date, res.status AS status,
               s.name AS processed_by
        ORDER BY res.check_in_date DESC
        LIMIT 10
        """
        results = db.execute_read(query)
        # Convert Neo4j date objects to strings
        for r in results:
            if r.get("check_in_date"):
                r["check_in_date"] = str(r["check_in_date"])
            if r.get("check_out_date"):
                r["check_out_date"] = str(r["check_out_date"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
