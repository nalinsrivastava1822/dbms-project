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
@router.post("/", status_code=201)
def create_reservation(reservation: ReservationCreate):
    """
    Create a new reservation atomically within a transaction:
    - Check-out date must be strictly after check-in date.
    - Resolves room by room_id or hotel room_no.
    - Rejects room if currently under Maintenance.
    - Rejects if Guest or Staff does not exist.
    - Rejects if an active/confirmed booking overlaps the requested dates.
    - Atomically creates reservation node and relationships in one transaction callback.
    """
    # 1. Validate dates
    if reservation.check_out_date <= reservation.check_in_date:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date"
        )

    if not reservation.room_id and not reservation.room_no:
        raise HTTPException(
            status_code=400,
            detail="Either room_id or room_no must be provided"
        )

    payload = {
        "res_id": reservation.res_id,
        "guest_id": reservation.guest_id,
        "room_id": reservation.room_id,
        "room_no": reservation.room_no,
        "staff_id": reservation.staff_id,
        "check_in": str(reservation.check_in_date),
        "check_out": str(reservation.check_out_date),
    }

    def _atomic_booking_tx(tx):
        # A. Check duplicate reservation ID
        dup = tx.run(
            "MATCH (r:Reservation {res_id: $res_id}) RETURN r.res_id AS res_id",
            {"res_id": payload["res_id"]}
        ).single()
        if dup:
            raise HTTPException(status_code=409, detail=f"Reservation {payload['res_id']} already exists")

        # B. Verify guest exists
        guest = tx.run(
            "MATCH (g:Guest {guest_id: $guest_id}) RETURN g.name AS name",
            {"guest_id": payload["guest_id"]}
        ).single()
        if not guest:
            raise HTTPException(status_code=404, detail=f"Guest {payload['guest_id']} not found")

        # C. Verify room exists and check maintenance status
        room_query = """
        MATCH (r:Room)
        WHERE ($room_id IS NOT NULL AND r.room_id = $room_id)
           OR ($room_id IS NULL AND r.room_no = $room_no)
        RETURN r.room_id AS room_id, r.room_no AS room_no, r.status AS status
        """
        room = tx.run(room_query, {"room_id": payload["room_id"], "room_no": payload["room_no"]}).single()
        if not room:
            id_val = payload["room_id"] or payload["room_no"]
            raise HTTPException(status_code=404, detail=f"Room {id_val} not found")

        if room.get("status") == "Maintenance":
            raise HTTPException(
                status_code=400,
                detail=f"Room {room['room_no']} is currently under maintenance and cannot be booked"
            )

        # D. Verify staff exists
        staff = tx.run(
            "MATCH (s:Staff {staff_id: $staff_id}) RETURN s.name AS name",
            {"staff_id": payload["staff_id"]}
        ).single()
        if not staff:
            raise HTTPException(status_code=404, detail=f"Staff {payload['staff_id']} not found")

        # E. Check for overlapping active reservations on the same room
        overlap_query = """
        MATCH (res:Reservation)-[:BOOKS]->(r:Room)
        WHERE (($room_id IS NOT NULL AND r.room_id = $room_id) OR ($room_id IS NULL AND r.room_no = $room_no))
          AND res.status IN ['Active', 'Confirmed']
          AND res.check_in_date < date($check_out)
          AND res.check_out_date > date($check_in)
        RETURN res.res_id AS conflicting_reservation
        """
        overlap = tx.run(overlap_query, {
            "room_id": payload["room_id"],
            "room_no": payload["room_no"],
            "check_in": payload["check_in"],
            "check_out": payload["check_out"],
        }).single()
        if overlap:
            raise HTTPException(
                status_code=409,
                detail=f"Room {room['room_no']} has an overlapping reservation ({overlap['conflicting_reservation']}) during requested dates"
            )

        # F. Create reservation and relationships atomically
        create_query = """
        MATCH (g:Guest {guest_id: $guest_id})
        MATCH (r:Room) WHERE ($room_id IS NOT NULL AND r.room_id = $room_id) OR ($room_id IS NULL AND r.room_no = $room_no)
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
        RETURN res.res_id AS res_id, res.status AS status,
               g.name AS guest_name, coalesce(r.room_id, 'RM' + toString(r.room_no)) AS room_id,
               r.room_no AS room_no, s.name AS staff_name
        """
        record = tx.run(create_query, payload).single()
        return dict(record) if record else {"res_id": payload["res_id"], "status": "Confirmed"}

    return db.run_write_transaction(_atomic_booking_tx)


@router.post("/{res_id}/cancel")
def cancel_reservation(res_id: str):
    """
    Cancel a reservation atomically.
    Cancelled reservations no longer block future date availability.
    Physical maintenance status of the room is preserved.
    """
    def _cancel_tx(tx):
        res = tx.run(
            "MATCH (res:Reservation {res_id: $res_id}) RETURN res.status AS status",
            {"res_id": res_id}
        ).single()
        if not res:
            raise HTTPException(status_code=404, detail=f"Reservation {res_id} not found")

        current_status = res["status"]
        if current_status == "Cancelled":
            raise HTTPException(status_code=400, detail="Reservation is already cancelled")
        if current_status == "Completed":
            raise HTTPException(status_code=400, detail="Cannot cancel a completed reservation")

        query = """
        MATCH (res:Reservation {res_id: $res_id})-[:BOOKS]->(r:Room)
        SET res.status = 'Cancelled'
        RETURN res.res_id AS res_id, res.status AS status, r.room_no AS room_no, r.status AS room_status
        """
        result = tx.run(query, {"res_id": res_id}).single()
        return {
            "message": f"Reservation {res_id} cancelled",
            "reservation": dict(result) if result else {"res_id": res_id, "status": "Cancelled"}
        }

    return db.run_write_transaction(_cancel_tx)

