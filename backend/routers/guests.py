"""
Guests API — CRUD operations for Guest entities.
"""
from fastapi import APIRouter, HTTPException, Query
from backend.database import db
from backend.models.schemas import GuestCreate
from typing import Optional
import re

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


def _generate_next_guest_id() -> str:
    """Find the next sequential Guest ID (e.g. G009, G010)."""
    query = "MATCH (g:Guest) RETURN g.guest_id AS guest_id"
    results = db.execute_read(query)
    max_num = 0
    for r in results:
        gid = r.get("guest_id") or ""
        if gid.startswith("G") and gid[1:].isdigit():
            try:
                max_num = max(max_num, int(gid[1:]))
            except ValueError:
                pass
    return f"G{max_num + 1:03d}"


@router.get("/next-id")
def get_next_guest_id():
    """Get the next sequential Guest ID (e.g. G009, G010)."""
    return {"next_id": _generate_next_guest_id()}


@router.post("/login")
def guest_login(payload: dict):
    """
    Authenticate or register a guest user:
    1. Read and normalize login identifier (email, phone, or guest ID) and password.
    2. Enforce authentication: do NOT authenticate users merely because they enter an email,
       phone number, or guest ID without providing credentials/password.
    3. Validate input format (email regex, phone digits).
    4. Query Neo4j using parameterized Cypher to check if the guest already exists.
    5. If found, verify password and return authenticated guest record.
    6. If registering, validate required fields including password and create atomically.
    7. Return proper HTTP errors on validation, authentication, or DB failure.
    """
    guest_id = (payload.get("guest_id") or "").strip().upper() or None
    raw_email = (payload.get("email") or "").strip() or None
    raw_phone = (payload.get("phone") or "").strip() or None
    raw_contact = (payload.get("contact_info") or "").strip() or None
    name = (payload.get("name") or "").strip()
    nationality = (payload.get("nationality") or "Indian").strip()
    gender = payload.get("gender") or "Other"
    if gender not in ["Male", "Female", "Other"]:
        gender = "Other"

    password = (payload.get("password") or "").strip() or None
    action = payload.get("action")  # "register", "login", or None (auto)

    # Validate and normalize email
    email = None
    if raw_email:
        email = raw_email.lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise HTTPException(status_code=400, detail="Invalid email address format")

    # Validate and normalize phone
    phone = None
    if raw_phone:
        digits = re.sub(r"\D", "", raw_phone)
        if len(digits) < 5:
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        phone = raw_phone

    # If raw_contact was provided directly
    if raw_contact and not email and not phone:
        if "@" in raw_contact:
            c_email = raw_contact.split("|")[0].strip().lower()
            if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", c_email):
                email = c_email
            else:
                contact_info = raw_contact
        else:
            digits = re.sub(r"\D", "", raw_contact)
            if len(digits) >= 5:
                phone = raw_contact

    # Unified contact_info string
    if email and phone:
        contact_info = f"{email} | {phone}"
    elif email:
        contact_info = email
    elif phone:
        contact_info = phone
    elif raw_contact:
        contact_info = raw_contact
    else:
        contact_info = None

    # Check for empty input
    if not guest_id and not email and not phone and not contact_info and not name:
        raise HTTPException(
            status_code=400,
            detail="A valid login identifier (Guest ID, email, or phone) is required"
        )

    # Security check: Password is strictly required for authentication.
    # Users must NOT be authenticated merely by entering an email, phone, or guest ID alone.
    if not password:
        raise HTTPException(
            status_code=401,
            detail="Password is required. Users cannot be authenticated merely by entering an email, phone, or guest ID"
        )

    existing_guest = None

    # Step 1: Lookup by guest_id if provided
    if guest_id:
        try:
            lookup = db.execute_read(
                "MATCH (g:Guest {guest_id: $guest_id}) "
                "RETURN g.guest_id AS guest_id, g.name AS name, g.contact_info AS contact_info, "
                "       g.nationality AS nationality, g.gender AS gender, g.password AS password",
                {"guest_id": guest_id}
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Database connection error: {str(e)}")

        if lookup:
            existing_guest = lookup[0]
            if name and existing_guest.get("name") and name.lower() != existing_guest["name"].lower():
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials: name does not match guest ID"
                )
        else:
            if action == "login" or not name:
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid credentials: Guest '{guest_id}' not found"
                )

    # Step 2: Lookup by email / phone / contact_info if not yet found
    if not existing_guest and (email or phone or contact_info):
        try:
            lookup = db.execute_read(
                "MATCH (g:Guest) "
                "WHERE ($email IS NOT NULL AND $email <> '' AND toLower(g.contact_info) CONTAINS toLower($email)) "
                "   OR ($phone IS NOT NULL AND $phone <> '' AND g.contact_info CONTAINS $phone) "
                "   OR ($contact_info IS NOT NULL AND $contact_info <> '' AND toLower(g.contact_info) CONTAINS toLower($contact_info)) "
                "RETURN g.guest_id AS guest_id, g.name AS name, g.contact_info AS contact_info, "
                "       g.nationality AS nationality, g.gender AS gender, g.password AS password "
                "LIMIT 1",
                {"email": email or "", "phone": phone or "", "contact_info": contact_info or ""}
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Database connection error: {str(e)}")

        if lookup:
            existing_guest = lookup[0]

    # Step 3: Fallback lookup by exact name if provided and not yet found
    if not existing_guest and name:
        try:
            lookup = db.execute_read(
                "MATCH (g:Guest) WHERE toLower(g.name) = toLower($name) "
                "RETURN g.guest_id AS guest_id, g.name AS name, g.contact_info AS contact_info, "
                "       g.nationality AS nationality, g.gender AS gender, g.password AS password "
                "LIMIT 1",
                {"name": name}
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Database connection error: {str(e)}")

        if lookup:
            existing_guest = lookup[0]

    # If guest exists: Authenticate with password!
    if existing_guest:
        stored_pw = existing_guest.get("password")
        if stored_pw and stored_pw != password:
            raise HTTPException(status_code=401, detail="Invalid credentials: Incorrect password")
        elif not stored_pw:
            # Set initial password on first login for legacy/unseeded record
            db.execute_write(
                "MATCH (g:Guest {guest_id: $guest_id}) SET g.password = $password",
                {"guest_id": existing_guest["guest_id"], "password": password}
            )

        # Do not expose password to client
        guest_response = {k: v for k, v in existing_guest.items() if k != "password"}
        return {
            "success": True,
            "guest": guest_response,
            "role": "guest",
            "is_new": False
        }

    # If action was specifically 'login' and no guest was found
    if action == "login":
        raise HTTPException(status_code=401, detail="Invalid credentials: Guest not found")

    # If guest does not exist: Validate registration fields
    if not name or len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Guest full name is required to create a new guest account"
        )
    if len(password) < 4:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 4 characters long"
        )

    final_contact = contact_info or "Not provided"

    # Transactional guest creation using MERGE to prevent duplicate nodes
    def _create_guest_atomic_tx(tx):
        # Concurrency check inside transaction
        check = tx.run(
            "MATCH (g:Guest) "
            "WHERE ($email IS NOT NULL AND $email <> '' AND toLower(g.contact_info) CONTAINS toLower($email)) "
            "   OR ($phone IS NOT NULL AND $phone <> '' AND g.contact_info CONTAINS $phone) "
            "RETURN g.guest_id AS guest_id, g.name AS name, g.contact_info AS contact_info, "
            "       g.nationality AS nationality, g.gender AS gender "
            "LIMIT 1",
            {"email": email or "", "phone": phone or ""}
        ).single()
        if check:
            return {
                "success": True,
                "guest": dict(check),
                "role": "guest",
                "is_new": False
            }

        # Sequence next Guest ID inside write transaction
        id_records = tx.run("MATCH (g:Guest) RETURN g.guest_id AS guest_id").data()
        max_num = 0
        for r in id_records:
            gid = r.get("guest_id") or ""
            if gid.startswith("G") and gid[1:].isdigit():
                try:
                    max_num = max(max_num, int(gid[1:]))
                except ValueError:
                    pass
        assigned_id = guest_id if (guest_id and guest_id.startswith("G")) else f"G{max_num + 1:03d}"

        # Parameterized MERGE query
        create_query = """
        MERGE (g:Guest {guest_id: $guest_id})
        ON CREATE SET g.name = $name,
                      g.contact_info = $contact_info,
                      g.nationality = $nationality,
                      g.gender = $gender,
                      g.password = $password
        RETURN g.guest_id AS guest_id, g.name AS name,
               g.contact_info AS contact_info, g.nationality AS nationality,
               g.gender AS gender
        """
        record = tx.run(create_query, {
            "guest_id": assigned_id,
            "name": name,
            "contact_info": final_contact,
            "nationality": nationality,
            "gender": gender,
            "password": password,
        }).single()

        if not record:
            raise HTTPException(status_code=500, detail="Database operation failed to create guest")

        return {
            "success": True,
            "guest": dict(record),
            "role": "guest",
            "is_new": True
        }

    try:
        result = db.run_write_transaction(_create_guest_atomic_tx)
        if not result or not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to create guest record in database")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error during guest registration: {str(e)}")


@router.get("/{guest_id}")
def get_guest(guest_id: str, caller_guest_id: Optional[str] = Query(None)):
    """
    Get a guest's details and reservation history.
    Enforces authorization if caller_guest_id is provided to prevent viewing other guests' data.
    """
    if caller_guest_id and caller_guest_id != guest_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot view another guest's profile or reservations"
        )

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
    data["reservations"] = [r for r in data["reservations"] if r.get("res_id") is not None]
    return data


@router.get("/{guest_id}/reservations")
def get_guest_reservations(guest_id: str, caller_guest_id: Optional[str] = Query(None)):
    """
    Dedicated endpoint for Guest Self-Service: My Reservations.
    Categorizes reservations into upcoming, completed, and cancelled.
    Enforces caller_guest_id ownership check.
    """
    if caller_guest_id and caller_guest_id != guest_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot view another guest's reservations"
        )

    # Verify guest exists
    guest_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g.guest_id AS guest_id, g.name AS name",
        {"guest_id": guest_id}
    )
    if not guest_check:
        raise HTTPException(status_code=404, detail=f"Guest {guest_id} not found")

    query = """
    MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    OPTIONAL MATCH (r)-[:BELONGS_TO]->(c:RoomCategory)
    OPTIONAL MATCH (s:Staff)-[:PROCESSES]->(res)
    RETURN res.res_id AS res_id,
           toString(res.check_in_date) AS check_in_date,
           toString(res.check_out_date) AS check_out_date,
           res.status AS status,
           r.room_no AS room_no,
           coalesce(r.room_id, 'RM' + toString(r.room_no)) AS room_id,
           h.hotel_id AS hotel_id,
           h.name AS hotel_name,
           h.location AS location,
           c.category_name AS category,
           c.rent AS rent,
           s.name AS staff_name
    ORDER BY res.check_in_date DESC
    """
    records = db.execute_read(query, {"guest_id": guest_id})

    upcoming = []
    completed = []
    cancelled = []

    for r in records:
        try:
            d_in = date.fromisoformat(r["check_in_date"])
            d_out = date.fromisoformat(r["check_out_date"])
            nights = max(1, (d_out - d_in).days)
        except Exception:
            nights = 1

        r["nights"] = nights
        r["estimated_total_price"] = round(float(r.get("rent", 0.0)) * nights, 2)
        r["can_cancel"] = r["status"] in ["Active", "Confirmed"]

        status = r.get("status")
        if status in ["Active", "Confirmed"]:
            upcoming.append(r)
        elif status == "Completed":
            completed.append(r)
        elif status == "Cancelled":
            cancelled.append(r)
        else:
            upcoming.append(r)

    return {
        "guest_id": guest_id,
        "guest_name": guest_check[0]["name"],
        "total_count": len(records),
        "upcoming": upcoming,
        "completed": completed,
        "cancelled": cancelled,
        "all": records,
    }


@router.post("/")
def create_guest(guest: GuestCreate):
    """Add a new guest."""
    gid = guest.guest_id or _generate_next_guest_id()

    # Check for duplicate
    dup_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g.guest_id AS guest_id",
        {"guest_id": gid}
    )
    if dup_check:
        raise HTTPException(status_code=409, detail=f"Guest {gid} already exists")

    query = """
    CREATE (g:Guest {
        guest_id: $guest_id, name: $name, contact_info: $contact_info,
        nationality: $nationality, gender: $gender, password: $password
    })
    RETURN g.guest_id AS guest_id, g.name AS name,
           g.contact_info AS contact_info, g.nationality AS nationality,
           g.gender AS gender
    """
    params = guest.model_dump()
    params["guest_id"] = gid
    result = db.execute_write(query, params)
    return result[0] if result else {"guest_id": gid, "name": guest.name}
