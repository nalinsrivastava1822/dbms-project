"""
Staff API — List staff and view reservation processing.
"""
from fastapi import APIRouter, HTTPException, Query
from backend.database import db
from typing import Optional

router = APIRouter(prefix="/api/staff", tags=["Staff"])


@router.get("/")
def list_staff():
    """List all staff with department and hotel information."""
    query = """
    MATCH (h:Hotel)-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s:Staff)
    OPTIONAL MATCH (s)-[:PROCESSES]->(res:Reservation)
    RETURN s.staff_id AS staff_id, s.name AS name, s.age AS age,
           s.salary AS salary, s.contact_info AS contact_info,
           d.dept_id AS dept_id, d.d_role AS department,
           h.hotel_id AS hotel_id, h.name AS hotel_name,
           COUNT(res) AS reservations_processed
    ORDER BY h.hotel_id, d.dept_id, s.staff_id
    """
    return db.execute_read(query)


@router.get("/by-department")
def staff_by_department(dept_id: Optional[str] = Query(None)):
    """List staff grouped by department, optionally filtered."""
    conditions = ""
    params = {}
    if dept_id:
        conditions = "WHERE d.dept_id = $dept_id"
        params["dept_id"] = dept_id

    query = f"""
    MATCH (h:Hotel)-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s:Staff)
    {conditions}
    RETURN d.dept_id AS dept_id, d.d_role AS department, d.d_head AS dept_head,
           h.name AS hotel_name,
           COLLECT({{staff_id: s.staff_id, name: s.name, age: s.age,
                    salary: s.salary, contact_info: s.contact_info}}) AS staff
    ORDER BY d.dept_id
    """
    return db.execute_read(query, params)


@router.get("/{staff_id}/reservations")
def staff_reservations(staff_id: str):
    """View reservations processed by a specific staff member."""
    # Verify staff exists
    staff_check = db.execute_read(
        "MATCH (s:Staff {staff_id: $staff_id}) RETURN s.name AS name",
        {"staff_id": staff_id}
    )
    if not staff_check:
        raise HTTPException(status_code=404, detail=f"Staff {staff_id} not found")

    query = """
    MATCH (s:Staff {staff_id: $staff_id})-[:PROCESSES]->(res:Reservation)
    MATCH (g:Guest)-[:MADE]->(res)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    RETURN res.res_id AS res_id, toString(res.check_in_date) AS check_in_date,
           toString(res.check_out_date) AS check_out_date, res.status AS status,
           g.name AS guest_name, r.room_no AS room_no, h.name AS hotel_name
    ORDER BY res.check_in_date DESC
    """
    reservations = db.execute_read(query, {"staff_id": staff_id})
    return {
        "staff_name": staff_check[0]["name"],
        "staff_id": staff_id,
        "reservations": reservations
    }
