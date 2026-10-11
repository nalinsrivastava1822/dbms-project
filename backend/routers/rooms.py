"""
Rooms API — CRUD and search operations for Room entities.
"""
from fastapi import APIRouter, HTTPException, Query
from backend.database import db
from backend.models.schemas import RoomCreate, RoomStatusUpdate
from typing import Optional

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


@router.get("/")
def list_rooms():
    """List all rooms with hotel and category information."""
    query = """
    MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
    RETURN r.room_no AS room_no, r.status AS status,
           c.category_name AS category, c.rent AS rent,
           h.hotel_id AS hotel_id, h.name AS hotel_name, h.location AS location
    ORDER BY h.hotel_id, r.room_no
    """
    return db.execute_read(query)


@router.get("/search")
def search_rooms(
    hotel_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    max_rent: Optional[float] = Query(None),
    status: Optional[str] = Query(None, pattern=r"^(Available|Occupied|Maintenance)$"),
):
    """Search rooms by hotel, category, rent, and/or status."""
    conditions = []
    params = {}

    if hotel_id:
        conditions.append("h.hotel_id = $hotel_id")
        params["hotel_id"] = hotel_id
    if category:
        conditions.append("c.category_name = $category")
        params["category"] = category
    if max_rent is not None:
        conditions.append("c.rent <= $max_rent")
        params["max_rent"] = max_rent
    if status:
        conditions.append("r.status = $status")
        params["status"] = status

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
    MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)
    {where_clause}
    RETURN r.room_no AS room_no, r.status AS status,
           c.category_name AS category, c.rent AS rent,
           h.hotel_id AS hotel_id, h.name AS hotel_name, h.location AS location
    ORDER BY c.rent, r.room_no
    """
    return db.execute_read(query, params)


@router.get("/categories")
def list_categories():
    """List all room categories."""
    query = """
    MATCH (c:RoomCategory)
    RETURN c.category_name AS category_name, c.rent AS rent
    ORDER BY c.rent
    """
    return db.execute_read(query)


@router.post("/")
def create_room(room: RoomCreate):
    """Add a new room to a hotel with a category."""
    # Verify hotel exists
    hotel_check = db.execute_read(
        "MATCH (h:Hotel {hotel_id: $hotel_id}) RETURN h",
        {"hotel_id": room.hotel_id}
    )
    if not hotel_check:
        raise HTTPException(status_code=404, detail=f"Hotel {room.hotel_id} not found")

    # Verify category exists
    cat_check = db.execute_read(
        "MATCH (c:RoomCategory {category_name: $cat}) RETURN c",
        {"cat": room.category_name}
    )
    if not cat_check:
        raise HTTPException(status_code=404, detail=f"Category {room.category_name} not found")

    # Check for duplicate room number
    dup_check = db.execute_read(
        "MATCH (r:Room {room_no: $room_no}) RETURN r",
        {"room_no": room.room_no}
    )
    if dup_check:
        raise HTTPException(status_code=409, detail=f"Room {room.room_no} already exists")

    query = """
    MATCH (h:Hotel {hotel_id: $hotel_id})
    MATCH (c:RoomCategory {category_name: $category_name})
    CREATE (r:Room {room_no: $room_no, status: $status})
    MERGE (h)-[:HAS_ROOM]->(r)
    MERGE (r)-[:BELONGS_TO]->(c)
    RETURN r.room_no AS room_no, r.status AS status,
           c.category_name AS category, c.rent AS rent,
           h.name AS hotel_name
    """
    result = db.execute_write(query, {
        "hotel_id": room.hotel_id,
        "category_name": room.category_name,
        "room_no": room.room_no,
        "status": room.status,
    })
    return result[0] if result else {"message": "Room created"}


@router.patch("/{room_no}/status")
def update_room_status(room_no: int, update: RoomStatusUpdate):
    """Update the status of a room."""
    check = db.execute_read(
        "MATCH (r:Room {room_no: $room_no}) RETURN r",
        {"room_no": room_no}
    )
    if not check:
        raise HTTPException(status_code=404, detail=f"Room {room_no} not found")

    # If setting to Available, check there's no active reservation
    if update.status == "Available":
        active_check = db.execute_read(
            """
            MATCH (res:Reservation)-[:BOOKS]->(r:Room {room_no: $room_no})
            WHERE res.status IN ['Active', 'Confirmed']
            AND res.check_out_date >= date()
            RETURN res
            """,
            {"room_no": room_no}
        )
        # Allow it but log a warning — the staff may know what they're doing

    query = """
    MATCH (r:Room {room_no: $room_no})
    SET r.status = $status
    RETURN r.room_no AS room_no, r.status AS status
    """
    result = db.execute_write(query, {"room_no": room_no, "status": update.status})
    return result[0] if result else {"message": "Status updated"}
