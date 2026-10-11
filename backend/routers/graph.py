"""
Graph Visualization API.
Returns nodes and edges formatted for interactive network visualization.
Supports both live Neo4j and In-Memory Graph Simulator.
"""
from fastapi import APIRouter
from backend.database import db
from backend.mock_store import mock_store

router = APIRouter(prefix="/api/graph", tags=["Graph Visualization"])


@router.get("/data")
def get_graph_data():
    """
    Retrieve full graph topology (nodes and directed edges)
    for interactive network visualization.
    """
    if db.is_connected and db.driver:
        try:
            # Live Neo4j query for nodes and relationships
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN labels(n) AS labels, properties(n) AS props, id(n) AS node_id,
                   type(r) AS rel_type, properties(r) AS rel_props, id(m) AS target_id
            """
            raw = db.execute_read(query)
            # Process Neo4j raw nodes into structured format
            nodes_map = {}
            links = []
            
            for row in raw:
                lbl = row["labels"][0] if row.get("labels") else "Entity"
                props = row.get("props") or {}
                # Determine unique node key
                nid = (
                    props.get("hotel_id") or 
                    props.get("category_name") or 
                    (str(props["room_no"]) if "room_no" in props else None) or 
                    props.get("guest_id") or 
                    props.get("res_id") or 
                    props.get("staff_id") or 
                    props.get("dept_id") or 
                    str(row["node_id"])
                )
                
                name = (
                    props.get("name") or 
                    props.get("category_name") or 
                    (f"Room {props['room_no']}" if "room_no" in props else None) or 
                    props.get("res_id") or 
                    props.get("d_role") or 
                    nid
                )
                
                if nid not in nodes_map:
                    nodes_map[nid] = {
                        "id": nid,
                        "label": lbl,
                        "name": name,
                        "properties": props,
                    }
                
                if row.get("rel_type") and row.get("target_id") is not None:
                    links.append({
                        "source": nid,
                        "target": str(row["target_id"]),
                        "type": row["rel_type"],
                    })
                    
            return {
                "nodes": list(nodes_map.values()),
                "links": links,
                "source": "live_neo4j"
            }
        except Exception as e:
            print(f"[WARN] Failed to fetch live graph ({e}), using mock store.")

    # Fallback to in-memory store
    nodes = []
    links = []

    # 1. Hotels (Red)
    for h_id, h in mock_store.hotels.items():
        nodes.append({
            "id": h_id,
            "label": "Hotel",
            "name": h["name"],
            "caption": h["name"],
            "color": "#ef4444",
            "radius": 22,
            "properties": {
                "Hotel ID": h["hotel_id"],
                "Name": h["name"],
                "Location": h["location"],
                "Rating": f"{h['rating']} ★",
            }
        })

    # 2. Categories (Purple)
    for c_name, c in mock_store.categories.items():
        cid = f"cat_{c_name}"
        nodes.append({
            "id": cid,
            "label": "RoomCategory",
            "name": f"{c_name} (₹{c['rent']})",
            "caption": c_name,
            "color": "#8b5cf6",
            "radius": 16,
            "properties": {
                "Category": c["category_name"],
                "Nightly Rent": f"₹{c['rent']}",
            }
        })

    # 3. Rooms (Blue)
    for r_no, r in mock_store.rooms.items():
        rid = f"room_{r_no}"
        status_color = "#3b82f6" if r["status"] == "Available" else "#f97316" if r["status"] == "Occupied" else "#64748b"
        nodes.append({
            "id": rid,
            "label": "Room",
            "name": f"Room {r_no}",
            "caption": str(r_no),
            "color": status_color,
            "radius": 14,
            "properties": {
                "Room No": r["room_no"],
                "Status": r["status"],
                "Category": r["category_name"],
                "Hotel ID": r["hotel_id"],
            }
        })
        # Link: (Hotel) -> HAS_ROOM -> (Room)
        links.append({"source": r["hotel_id"], "target": rid, "type": "HAS_ROOM"})
        # Link: (Room) -> BELONGS_TO -> (Category)
        links.append({"source": rid, "target": f"cat_{r['category_name']}", "type": "BELONGS_TO"})

    # 4. Departments (Teal)
    for d_id, d in mock_store.departments.items():
        nodes.append({
            "id": d_id,
            "label": "Department",
            "name": f"{d['d_role']} ({d_id})",
            "caption": d["d_role"],
            "color": "#06b6d4",
            "radius": 16,
            "properties": {
                "Dept ID": d["dept_id"],
                "Role": d["d_role"],
                "Head": d["d_head"],
                "Contact": d["contact_info"],
            }
        })
        # Link: (Hotel) -> HAS_DEPARTMENT -> (Department)
        links.append({"source": d["hotel_id"], "target": d_id, "type": "HAS_DEPARTMENT"})

    # 5. Staff (Amber)
    for s_id, s in mock_store.staff.items():
        nodes.append({
            "id": s_id,
            "label": "Staff",
            "name": s["name"],
            "caption": s["name"].split()[0],
            "color": "#f59e0b",
            "radius": 14,
            "properties": {
                "Staff ID": s["staff_id"],
                "Name": s["name"],
                "Age": s["age"],
                "Salary": f"₹{s['salary']:,}",
                "Contact": s["contact_info"],
            }
        })
        # Link: (Department) -> EMPLOYS -> (Staff)
        links.append({"source": s["dept_id"], "target": s_id, "type": "EMPLOYS"})

    # 6. Guests (Emerald Green)
    for g_id, g in mock_store.guests.items():
        nodes.append({
            "id": g_id,
            "label": "Guest",
            "name": g["name"],
            "caption": g["name"].split()[0],
            "color": "#10b981",
            "radius": 16,
            "properties": {
                "Guest ID": g["guest_id"],
                "Name": g["name"],
                "Nationality": g["nationality"],
                "Gender": g["gender"],
                "Contact": g["contact_info"],
            }
        })

    # 7. Reservations (Pink/Rose)
    for res_id, r in mock_store.reservations.items():
        nodes.append({
            "id": res_id,
            "label": "Reservation",
            "name": f"{res_id} ({r['status']})",
            "caption": res_id,
            "color": "#ec4899",
            "radius": 13,
            "properties": {
                "Res ID": r["res_id"],
                "Check In": r["check_in_date"],
                "Check Out": r["check_out_date"],
                "Status": r["status"],
            }
        })
        # Link: (Guest) -> MADE -> (Reservation)
        links.append({"source": r["guest_id"], "target": res_id, "type": "MADE"})
        # Link: (Reservation) -> BOOKS -> (Room)
        links.append({"source": res_id, "target": f"room_{r['room_no']}", "type": "BOOKS"})
        # Link: (Staff) -> PROCESSES -> (Reservation)
        if r.get("staff_id") and r["staff_id"] in mock_store.staff:
            links.append({"source": r["staff_id"], "target": res_id, "type": "PROCESSES"})

    return {
        "nodes": nodes,
        "links": links,
        "source": "in_memory_simulator",
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
        }
    }
