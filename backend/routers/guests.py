"""
Guests API — CRUD operations for Guest entities.
"""
from fastapi import APIRouter, HTTPException, Query
from backend.database import db
from backend.models.schemas import GuestCreate
from typing import Optional

router = APIRouter(prefix="/api/guests", tags=["Guests"])


@router.get("/")
def list_guests():
    """List all guests with reservation count."""
    query = """
    MATCH (g:Guest)
    OPTIONAL MATCH (g)-[:MADE]->(res:Reservation)
    RETURN g.guest_id AS guest_id, g.name AS name,
           g.contact_info AS contact_info, g.nationality AS nationality,
           g.gender AS gender, COUNT(res) AS reservation_count
    ORDER BY g.guest_id
    """
    return db.execute_read(query)


@router.get("/search")
def search_guests(
    name: Optional[str] = Query(None),
    nationality: Optional[str] = Query(None),
):
    """Search guests by name or nationality."""
    conditions = []
    params = {}

    if name:
        conditions.append("toLower(g.name) CONTAINS toLower($name)")
        params["name"] = name
    if nationality:
        conditions.append("toLower(g.nationality) CONTAINS toLower($nationality)")
        params["nationality"] = nationality

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
    MATCH (g:Guest)
    {where_clause}
    OPTIONAL MATCH (g)-[:MADE]->(res:Reservation)
    RETURN g.guest_id AS guest_id, g.name AS name,
           g.contact_info AS contact_info, g.nationality AS nationality,
           g.gender AS gender, COUNT(res) AS reservation_count
    ORDER BY g.name
    """
    return db.execute_read(query, params)


@router.get("/{guest_id}")
def get_guest(guest_id: str):
    """Get a guest's details and reservation history."""
    query = """
    MATCH (g:Guest {guest_id: $guest_id})
    OPTIONAL MATCH (g)-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    OPTIONAL MATCH (r)-[:BELONGS_TO]->(c:RoomCategory)
    OPTIONAL MATCH (s:Staff)-[:PROCESSES]->(res)
    RETURN g.guest_id AS guest_id, g.name AS name,
           g.contact_info AS contact_info, g.nationality AS nationality,
           g.gender AS gender,
           COLLECT(DISTINCT {
               res_id: res.res_id, check_in_date: toString(res.check_in_date),
               check_out_date: toString(res.check_out_date), status: res.status,
               room_no: r.room_no, hotel_name: h.name, category: c.category_name,
               rent: c.rent, processed_by: s.name
           }) AS reservations
    """
    result = db.execute_read(query, {"guest_id": guest_id})
    if not result:
        raise HTTPException(status_code=404, detail=f"Guest {guest_id} not found")
    data = result[0]
    # Filter out null reservation entries from OPTIONAL MATCH
    data["reservations"] = [r for r in data["reservations"] if r.get("res_id") is not None]
    return data


@router.post("/")
def create_guest(guest: GuestCreate):
    """Add a new guest."""
    # Check for duplicate
    dup_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g",
        {"guest_id": guest.guest_id}
    )
    if dup_check:
        raise HTTPException(status_code=409, detail=f"Guest {guest.guest_id} already exists")

    query = """
    CREATE (g:Guest {
        guest_id: $guest_id, name: $name, contact_info: $contact_info,
        nationality: $nationality, gender: $gender
    })
    RETURN g.guest_id AS guest_id, g.name AS name
    """
    result = db.execute_write(query, guest.model_dump())
    return result[0] if result else {"message": "Guest created"}
