"""
Recommendations API — Graph-based traversal queries.
Demonstrates multi-hop Cypher queries for recommendations.
"""
from fastapi import APIRouter, HTTPException
from backend.database import db

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.get("/hotels/{guest_id}")
def recommend_hotels(guest_id: str):
    """
    Recommend hotels to a guest based on where similar guests have stayed.

    Graph traversal path (multi-hop):
        (Target Guest) → [:MADE] → (Reservation) → [:BOOKS] → (Room)
        ← [:HAS_ROOM] ← (Common Hotel) → [:HAS_ROOM] → (Room)
        ← [:BOOKS] ← (Reservation) ← [:MADE] ← (Other Guest)
        → [:MADE] → (Reservation) → [:BOOKS] → (Room)
        ← [:HAS_ROOM] ← (Recommended Hotel)

    This query traverses 6+ hops and would require multiple self-joins
    with subqueries in SQL, making it a natural fit for graph databases.
    """
    # Verify guest exists
    guest_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g.name AS name",
        {"guest_id": guest_id}
    )
    if not guest_check:
        raise HTTPException(status_code=404, detail=f"Guest {guest_id} not found")

    query = """
    MATCH (target:Guest {guest_id: $guest_id})-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(commonHotel:Hotel)
    MATCH (commonHotel)-[:HAS_ROOM]->(:Room)<-[:BOOKS]-(:Reservation)<-[:MADE]-(otherGuest:Guest)
    WHERE otherGuest <> target
    MATCH (otherGuest)-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(recommended:Hotel)
    WHERE NOT (target)-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(recommended)
    RETURN DISTINCT recommended.hotel_id AS hotel_id,
           recommended.name AS hotel_name,
           recommended.location AS location,
           recommended.rating AS rating,
           COUNT(DISTINCT otherGuest) AS shared_guests,
           COLLECT(DISTINCT otherGuest.name) AS guests_who_stayed
    ORDER BY shared_guests DESC, rating DESC
    """
    recommendations = db.execute_read(query, {"guest_id": guest_id})
    return {
        "guest_name": guest_check[0]["name"],
        "guest_id": guest_id,
        "recommendations": recommendations,
        "explanation": (
            "Hotels recommended based on where other guests who stayed at the same "
            "hotels as this guest have also stayed. This multi-hop graph traversal "
            "identifies patterns of guest movement across hotels."
        )
    }


@router.get("/rooms/{guest_id}")
def recommend_room_categories(guest_id: str):
    """
    Recommend room categories to a guest based on past preferences.

    Finds categories the guest has booked, then suggests similar categories
    (by price range) they haven't tried yet.
    """
    guest_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g.name AS name",
        {"guest_id": guest_id}
    )
    if not guest_check:
        raise HTTPException(status_code=404, detail=f"Guest {guest_id} not found")

    query = """
    MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)-[:BELONGS_TO]->(booked:RoomCategory)
    WITH g, COLLECT(DISTINCT booked.category_name) AS bookedCategories, AVG(booked.rent) AS avgRent
    MATCH (c:RoomCategory)
    WHERE NOT c.category_name IN bookedCategories
    RETURN c.category_name AS category, c.rent AS rent,
           ROUND(ABS(c.rent - avgRent)) AS price_difference
    ORDER BY price_difference ASC
    """
    return {
        "guest_name": guest_check[0]["name"],
        "recommendations": db.execute_read(query, {"guest_id": guest_id})
    }


@router.get("/popular-by-nationality/{nationality}")
def popular_hotels_by_nationality(nationality: str):
    """
    Recommend hotels popular among guests of a specific nationality.

    Traverses: (Guest{nationality}) → Reservation → Room ← Hotel
    """
    query = """
    MATCH (peer:Guest {nationality: $nationality})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    WHERE res.status IN ['Active', 'Completed', 'Confirmed']
    RETURN h.hotel_id AS hotel_id, h.name AS hotel_name,
           h.location AS location, h.rating AS rating,
           COUNT(DISTINCT peer) AS guests_from_country,
           COUNT(DISTINCT res) AS total_bookings
    ORDER BY guests_from_country DESC, total_bookings DESC
    """
    return {
        "nationality": nationality,
        "popular_hotels": db.execute_read(query, {"nationality": nationality})
    }


@router.get("/guest-journey/{guest_id}")
def guest_journey(guest_id: str):
    """
    Trace a guest's complete journey through the hotel system.
    Combines forward and backward traversals across all node types.
    """
    guest_check = db.execute_read(
        "MATCH (g:Guest {guest_id: $guest_id}) RETURN g.name AS name, g.nationality AS nationality",
        {"guest_id": guest_id}
    )
    if not guest_check:
        raise HTTPException(status_code=404, detail=f"Guest {guest_id} not found")

    query = """
    MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)
    MATCH (r)-[:BELONGS_TO]->(c:RoomCategory)
    OPTIONAL MATCH (s:Staff)-[:PROCESSES]->(res)
    OPTIONAL MATCH (h)-[:HAS_DEPARTMENT]->(d:Department)-[:EMPLOYS]->(s)
    RETURN res.res_id AS reservation_id, res.status AS status,
           toString(res.check_in_date) AS check_in, toString(res.check_out_date) AS check_out,
           h.name AS hotel, h.location AS location,
           r.room_no AS room, c.category_name AS category, c.rent AS rent,
           s.name AS processed_by, d.d_role AS staff_department
    ORDER BY res.check_in_date
    """
    journey = db.execute_read(query, {"guest_id": guest_id})
    return {
        "guest": guest_check[0],
        "journey": journey,
        "explanation": (
            "This query traverses Guest → Reservation → Room → Hotel and also "
            "Staff → Department, spanning all 7 entity types in a single query."
        )
    }
