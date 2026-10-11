"""
Hotels API — CRUD operations for Hotel entities.
"""
from fastapi import APIRouter, HTTPException
from backend.database import db
from backend.models.schemas import HotelCreate

router = APIRouter(prefix="/api/hotels", tags=["Hotels"])


@router.get("/")
def list_hotels():
    """List all hotels with room and department counts."""
    query = """
    MATCH (h:Hotel)
    OPTIONAL MATCH (h)-[:HAS_ROOM]->(r:Room)
    OPTIONAL MATCH (h)-[:HAS_DEPARTMENT]->(d:Department)
    RETURN h.hotel_id AS hotel_id, h.name AS name, h.location AS location,
           h.rating AS rating, COUNT(DISTINCT r) AS room_count,
           COUNT(DISTINCT d) AS dept_count
    ORDER BY h.hotel_id
    """
    return db.execute_read(query)


@router.get("/{hotel_id}")
def get_hotel(hotel_id: str):
    """Get a specific hotel with its rooms and departments."""
    query = """
    MATCH (h:Hotel {hotel_id: $hotel_id})
    OPTIONAL MATCH (h)-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
    OPTIONAL MATCH (h)-[:HAS_DEPARTMENT]->(d:Department)
    WITH h,
         COLLECT(DISTINCT {room_no: r.room_no, status: r.status,
                 category: c.category_name, rent: c.rent}) AS rooms,
         COLLECT(DISTINCT {dept_id: d.dept_id, d_head: d.d_head,
                 d_role: d.d_role, contact_info: d.contact_info}) AS departments
    RETURN h.hotel_id AS hotel_id, h.name AS name, h.location AS location,
           h.rating AS rating, rooms, departments
    """
    result = db.execute_read(query, {"hotel_id": hotel_id})
    if not result:
        raise HTTPException(status_code=404, detail=f"Hotel {hotel_id} not found")
    data = result[0]
    # Filter out null entries from OPTIONAL MATCH
    data["rooms"] = [r for r in data["rooms"] if r.get("room_no") is not None]
    data["departments"] = [d for d in data["departments"] if d.get("dept_id") is not None]
    return data


@router.get("/{hotel_id}/rooms")
def get_hotel_rooms(hotel_id: str):
    """List rooms for a specific hotel."""
    query = """
    MATCH (h:Hotel {hotel_id: $hotel_id})-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
    RETURN r.room_no AS room_no, r.status AS status,
           c.category_name AS category, c.rent AS rent
    ORDER BY r.room_no
    """
    return db.execute_read(query, {"hotel_id": hotel_id})


@router.get("/{hotel_id}/departments")
def get_hotel_departments(hotel_id: str):
    """List departments for a specific hotel with staff."""
    query = """
    MATCH (h:Hotel {hotel_id: $hotel_id})-[:HAS_DEPARTMENT]->(d:Department)
    OPTIONAL MATCH (d)-[:EMPLOYS]->(s:Staff)
    RETURN d.dept_id AS dept_id, d.d_head AS d_head, d.d_role AS d_role,
           d.contact_info AS contact_info,
           COLLECT({staff_id: s.staff_id, name: s.name, age: s.age,
                    salary: s.salary}) AS staff
    ORDER BY d.dept_id
    """
    results = db.execute_read(query, {"hotel_id": hotel_id})
    for r in results:
        r["staff"] = [s for s in r["staff"] if s.get("staff_id") is not None]
    return results
