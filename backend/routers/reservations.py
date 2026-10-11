"""
Reservations API — Create, list, cancel reservations with validation.
Uses transactions for consistent booking updates.
"""
from fastapi import APIRouter, HTTPException
from backend.database import db
from backend.models.schemas import ReservationCreate

router = APIRouter(prefix="/api/reservations", tags=["Reservations"])


@router.get("/")
def list_reservations():
    """List all reservations with guest, room, hotel, and staff details."""
    query = """
    MATCH (g:Guest)-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    OPTIONAL MATCH (s:Staff)-[:PROCESSES]->(res)
    OPTIONAL MATCH (r)-[:BELONGS_TO]->(c:RoomCategory)
    RETURN res.res_id AS res_id, res.check_in_date AS check_in_date,
           res.check_out_date AS check_out_date, res.status AS status,
           g.guest_id AS guest_id, g.name AS guest_name,
           r.room_no AS room_no, c.category_name AS category, c.rent AS rent,
           h.hotel_id AS hotel_id, h.name AS hotel_name,
           s.staff_id AS staff_id, s.name AS staff_name
    ORDER BY res.check_in_date DESC
    """
    results = db.execute_read(query)
    for r in results:
        if r.get("check_in_date"):
            r["check_in_date"] = str(r["check_in_date"])
        if r.get("check_out_date"):
            r["check_out_date"] = str(r["check_out_date"])
    return results


@router.post("/")
def create_reservation(reservation: ReservationCreate):
    """
    Create a new reservation with full validation:
    - Check-out date must be after check-in date.
    - Guest, room, and staff must exist.
    - No overlapping active reservations for the same room.
    - Uses a transaction for atomicity.
    """
    # 1. Validate dates
    if reservation.check_out_date <= reservation.check_in_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    # 2. Check duplicate reservation ID
    dup_check = db.execute_read(
        "MATCH (r:Reservation {res_id: $res_id}) RETURN r",
        {"res_id": reservation.res_id}
    )
    if dup_check:
        raise HTTPException(status_code=409, detail=f"Reservation {reservation.res_id} already exists")

    # 3. Verify guest exists
    guest_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g",
        {"guest_id": reservation.guest_id}
    )
    if not guest_check:
        raise HTTPException(status_code=404, detail=f"Guest {reservation.guest_id} not found")

    # 4. Verify room exists
    room_check = db.execute_read(
        "MATCH (r:Room {room_no: $room_no}) RETURN r",
        {"room_no": reservation.room_no}
    )
    if not room_check:
        raise HTTPException(status_code=404, detail=f"Room {reservation.room_no} not found")

    # 5. Verify staff exists
    staff_check = db.execute_read(
        "MATCH (s:Staff {staff_id: $staff_id}) RETURN s",
        {"staff_id": reservation.staff_id}
    )
    if not staff_check:
        raise HTTPException(status_code=404, detail=f"Staff {reservation.staff_id} not found")

    # 6. Check for overlapping active reservations on the same room
    overlap_check = db.execute_read(
        """
        MATCH (res:Reservation)-[:BOOKS]->(r:Room {room_no: $room_no})
        WHERE res.status IN ['Active', 'Confirmed']
          AND res.check_in_date < date($check_out)
          AND res.check_out_date > date($check_in)
        RETURN res.res_id AS conflicting_reservation
        """,
        {
            "room_no": reservation.room_no,
            "check_in": str(reservation.check_in_date),
            "check_out": str(reservation.check_out_date),
        }
    )
    if overlap_check:
        conflicting = overlap_check[0]["conflicting_reservation"]
        raise HTTPException(
            status_code=409,
            detail=f"Room {reservation.room_no} has an overlapping reservation ({conflicting}) "
                   f"during the requested dates"
        )

    # 7. Create reservation in a transaction
    query = """
    MATCH (g:Guest {guest_id: $guest_id})
    MATCH (r:Room {room_no: $room_no})
    MATCH (s:Staff {staff_id: $staff_id})
    CREATE (res:Reservation {
        res_id: $res_id,
        check_in_date: date($check_in),
        check_out_date: date($check_out),
        status: 'Confirmed'
    })
    MERGE (g)-[:MADE]->(res)
    MERGE (res)-[:BOOKS]->(r)
    MERGE (s)-[:PROCESSES]->(res)
    SET r.status = CASE
        WHEN date($check_in) <= date() AND date($check_out) >= date() THEN 'Occupied'
        ELSE r.status
    END
    RETURN res.res_id AS res_id, res.status AS status,
           g.name AS guest_name, r.room_no AS room_no, s.name AS staff_name
    """
    result = db.execute_write(query, {
        "res_id": reservation.res_id,
        "guest_id": reservation.guest_id,
        "room_no": reservation.room_no,
        "staff_id": reservation.staff_id,
        "check_in": str(reservation.check_in_date),
        "check_out": str(reservation.check_out_date),
    })
    return result[0] if result else {"message": "Reservation created"}


@router.post("/{res_id}/cancel")
def cancel_reservation(res_id: str):
    """
    Cancel a reservation and update room availability.
    Uses a transaction for consistency.
    """
    # Check reservation exists and is cancellable
    res_check = db.execute_read(
        "MATCH (res:Reservation {res_id: $res_id}) RETURN res.status AS status",
        {"res_id": res_id}
    )
    if not res_check:
        raise HTTPException(status_code=404, detail=f"Reservation {res_id} not found")

    current_status = res_check[0]["status"]
    if current_status == "Cancelled":
        raise HTTPException(status_code=400, detail="Reservation is already cancelled")
    if current_status == "Completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed reservation")

    # Cancel reservation and update room status in one transaction
    query = """
    MATCH (res:Reservation {res_id: $res_id})-[:BOOKS]->(r:Room)
    SET res.status = 'Cancelled'
    WITH r
    OPTIONAL MATCH (other:Reservation)-[:BOOKS]->(r)
    WHERE other.status IN ['Active', 'Confirmed']
      AND other.check_in_date <= date() AND other.check_out_date >= date()
    WITH r, COUNT(other) AS activeBookings
    SET r.status = CASE WHEN activeBookings = 0 THEN 'Available' ELSE r.status END
    RETURN r.room_no AS room_no, r.status AS room_status
    """
    result = db.execute_write(query, {"res_id": res_id})
    return {
        "message": f"Reservation {res_id} cancelled",
        "room_update": result[0] if result else None
    }
