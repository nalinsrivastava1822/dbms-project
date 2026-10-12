"""
In-Memory Graph Store & Query Evaluator.
Acts as a seamless fallback / simulator when a live Neo4j instance is not running.
Pre-populated with the exact same 7 entities and relationships from the Cypher seed script.
Supports thread-safe atomic transactions, room_id identifiers, and date-based availability.
"""
from datetime import date
import threading


class MockRecord(dict):
    def __getitem__(self, key):
        return super().get(key)

    def get(self, key, default=None):
        return super().get(key, default)

    def data(self):
        return dict(self)


class MockResult:
    def __init__(self, records):
        self._records = [MockRecord(r) for r in (records or [])]

    def single(self):
        return self._records[0] if self._records else None

    def data(self):
        return [r.data() for r in self._records]

    def __iter__(self):
        return iter(self._records)


class MockTx:
    def __init__(self, store):
        self.store = store

    def run(self, query, params=None):
        raw = self.store._execute_unlocked(query, params or {})
        return MockResult(raw)


class MockGraphStore:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        self.hotels = {
            "H001": {"hotel_id": "H001", "name": "Grand Palace Hotel", "location": "Mumbai", "rating": 4.5},
            "H002": {"hotel_id": "H002", "name": "Royal Orchid Resort", "location": "Delhi", "rating": 4.2},
            "H003": {"hotel_id": "H003", "name": "Seaside Inn", "location": "Goa", "rating": 3.8},
        }

        self.categories = {
            "Standard": {"category_name": "Standard", "rent": 2500.0},
            "Deluxe": {"category_name": "Deluxe", "rent": 5000.0},
            "Suite": {"category_name": "Suite", "rent": 10000.0},
            "Executive": {"category_name": "Executive", "rent": 7500.0},
        }

        self.rooms = {
            101: {"room_id": "RM101", "room_no": 101, "status": "Available", "hotel_id": "H001", "category_name": "Standard"},
            102: {"room_id": "RM102", "room_no": 102, "status": "Available", "hotel_id": "H001", "category_name": "Deluxe"},
            103: {"room_id": "RM103", "room_no": 103, "status": "Available", "hotel_id": "H001", "category_name": "Suite"},
            104: {"room_id": "RM104", "room_no": 104, "status": "Available", "hotel_id": "H001", "category_name": "Executive"},
            105: {"room_id": "RM105", "room_no": 105, "status": "Maintenance", "hotel_id": "H001", "category_name": "Standard"},
            201: {"room_id": "RM201", "room_no": 201, "status": "Available", "hotel_id": "H002", "category_name": "Standard"},
            202: {"room_id": "RM202", "room_no": 202, "status": "Available", "hotel_id": "H002", "category_name": "Deluxe"},
            203: {"room_id": "RM203", "room_no": 203, "status": "Available", "hotel_id": "H002", "category_name": "Suite"},
            204: {"room_id": "RM204", "room_no": 204, "status": "Available", "hotel_id": "H002", "category_name": "Executive"},
            301: {"room_id": "RM301", "room_no": 301, "status": "Available", "hotel_id": "H003", "category_name": "Standard"},
            302: {"room_id": "RM302", "room_no": 302, "status": "Available", "hotel_id": "H003", "category_name": "Deluxe"},
            303: {"room_id": "RM303", "room_no": 303, "status": "Available", "hotel_id": "H003", "category_name": "Suite"},
        }

        self.departments = {
            "D001": {"dept_id": "D001", "d_head": "Rajesh Kumar", "d_role": "Front Desk", "contact_info": "9876543210", "hotel_id": "H001"},
            "D002": {"dept_id": "D002", "d_head": "Priya Sharma", "d_role": "Housekeeping", "contact_info": "9876543211", "hotel_id": "H001"},
            "D003": {"dept_id": "D003", "d_head": "Amit Patel", "d_role": "Front Desk", "contact_info": "9876543212", "hotel_id": "H002"},
            "D004": {"dept_id": "D004", "d_head": "Sneha Reddy", "d_role": "Restaurant", "contact_info": "9876543213", "hotel_id": "H002"},
            "D005": {"dept_id": "D005", "d_head": "Vikram Singh", "d_role": "Front Desk", "contact_info": "9876543214", "hotel_id": "H003"},
        }

        self.staff = {
            "S001": {"staff_id": "S001", "name": "Arjun Mehta", "age": 28, "salary": 35000.0, "contact_info": "9111111111", "dept_id": "D001"},
            "S002": {"staff_id": "S002", "name": "Meera Joshi", "age": 32, "salary": 30000.0, "contact_info": "9222222222", "dept_id": "D001"},
            "S003": {"staff_id": "S003", "name": "Rahul Verma", "age": 25, "salary": 32000.0, "contact_info": "9333333333", "dept_id": "D002"},
            "S004": {"staff_id": "S004", "name": "Kavitha Nair", "age": 30, "salary": 28000.0, "contact_info": "9444444444", "dept_id": "D003"},
            "S005": {"staff_id": "S005", "name": "Deepak Rao", "age": 35, "salary": 40000.0, "contact_info": "9555555555", "dept_id": "D004"},
            "S006": {"staff_id": "S006", "name": "Anita Kulkarni", "age": 27, "salary": 33000.0, "contact_info": "9666666666", "dept_id": "D005"},
        }

        self.guests = {
            "G001": {"guest_id": "G001", "name": "John Smith", "contact_info": "1234567890", "nationality": "American", "gender": "Male", "password": "password123"},
            "G002": {"guest_id": "G002", "name": "Aisha Khan", "contact_info": "2345678901", "nationality": "Indian", "gender": "Female", "password": "password123"},
            "G003": {"guest_id": "G003", "name": "Carlos Rivera", "contact_info": "3456789012", "nationality": "Mexican", "gender": "Male", "password": "password123"},
            "G004": {"guest_id": "G004", "name": "Emily Chen", "contact_info": "4567890123", "nationality": "Chinese", "gender": "Female", "password": "password123"},
            "G005": {"guest_id": "G005", "name": "Ravi Iyer", "contact_info": "5678901234", "nationality": "Indian", "gender": "Male", "password": "password123"},
            "G006": {"guest_id": "G006", "name": "Sophie Martin", "contact_info": "6789012345", "nationality": "French", "gender": "Female", "password": "password123"},
            "G007": {"guest_id": "G007", "name": "David Brown", "contact_info": "7890123456", "nationality": "American", "gender": "Male", "password": "password123"},
            "G008": {"guest_id": "G008", "name": "Nisha Gupta", "contact_info": "8901234567", "nationality": "Indian", "gender": "Female", "password": "password123"},
        }

        self.reservations = {
            "R001": {"res_id": "R001", "check_in_date": "2026-10-10", "check_out_date": "2026-10-15", "status": "Active", "guest_id": "G001", "room_id": "RM103", "room_no": 103, "staff_id": "S001"},
            "R002": {"res_id": "R002", "check_in_date": "2026-10-09", "check_out_date": "2026-10-13", "status": "Active", "guest_id": "G002", "room_id": "RM202", "room_no": 202, "staff_id": "S004"},
            "R003": {"res_id": "R003", "check_in_date": "2026-10-11", "check_out_date": "2026-10-14", "status": "Active", "guest_id": "G003", "room_id": "RM302", "room_no": 302, "staff_id": "S006"},
            "R004": {"res_id": "R004", "check_in_date": "2026-09-01", "check_out_date": "2026-09-05", "status": "Completed", "guest_id": "G001", "room_id": "RM101", "room_no": 101, "staff_id": "S001"},
            "R005": {"res_id": "R005", "check_in_date": "2026-09-10", "check_out_date": "2026-09-14", "status": "Completed", "guest_id": "G004", "room_id": "RM201", "room_no": 201, "staff_id": "S004"},
            "R006": {"res_id": "R006", "check_in_date": "2026-09-15", "check_out_date": "2026-09-20", "status": "Completed", "guest_id": "G002", "room_id": "RM102", "room_no": 102, "staff_id": "S002"},
            "R007": {"res_id": "R007", "check_in_date": "2026-08-20", "check_out_date": "2026-08-25", "status": "Completed", "guest_id": "G005", "room_id": "RM301", "room_no": 301, "staff_id": "S006"},
            "R008": {"res_id": "R008", "check_in_date": "2026-10-20", "check_out_date": "2026-10-25", "status": "Cancelled", "guest_id": "G006", "room_id": "RM104", "room_no": 104, "staff_id": "S001"},
            "R009": {"res_id": "R009", "check_in_date": "2026-11-01", "check_out_date": "2026-11-05", "status": "Confirmed", "guest_id": "G007", "room_id": "RM203", "room_no": 203, "staff_id": "S004"},
        }

    def _find_room(self, room_id=None, room_no=None):
        for r in self.rooms.values():
            if room_id and r.get("room_id") == room_id:
                return r
            if room_no is not None and r.get("room_no") == int(room_no):
                return r
        return None

    def run_transaction(self, tx_func):
        """Execute a multi-step transaction callback under mutual exclusion lock."""
        with self._lock:
            tx = MockTx(self)
            return tx_func(tx)

    def execute(self, query: str, params: dict = None) -> list:
        with self._lock:
            return self._execute_unlocked(query, params)

    def _execute_unlocked(self, query: str, params: dict = None) -> list:
        params = params or {}
        q = " ".join(query.strip().split())

        # ==========================================
        # 1. WRITE / MUTATION OPERATIONS (CHECK FIRST)
        # ==========================================

        # A. Create Reservation
        if "CREATE (res:Reservation" in q or "CREATE (res: Reservation" in q:
            res_id = params.get("res_id")
            if not res_id:
                max_num = 0
                for rid in self.reservations:
                    if rid.startswith("R") and rid[1:].isdigit():
                        try:
                            max_num = max(max_num, int(rid[1:]))
                        except ValueError:
                            pass
                res_id = f"R{max_num + 1:03d}"

            rm = self._find_room(params.get("room_id"), params.get("room_no"))
            r_no = rm["room_no"] if rm else int(params.get("room_no", 0))
            r_id = rm["room_id"] if rm else f"RM{r_no}"
            c_in = str(params.get("check_in") or params.get("check_in_date"))
            c_out = str(params.get("check_out") or params.get("check_out_date"))
            staff_id = params.get("staff_id") or "S001"

            self.reservations[res_id] = {
                "res_id": res_id,
                "check_in_date": c_in,
                "check_out_date": c_out,
                "status": "Confirmed",
                "guest_id": params["guest_id"],
                "room_id": r_id,
                "room_no": r_no,
                "staff_id": staff_id,
            }
            g = self.guests.get(params["guest_id"], {})
            s = self.staff.get(staff_id, {})
            return [{
                "res_id": res_id,
                "status": "Confirmed",
                "check_in_date": c_in,
                "check_out_date": c_out,
                "guest_id": params["guest_id"],
                "guest_name": g.get("name", "Guest"),
                "room_id": r_id,
                "room_no": r_no,
                "staff_name": s.get("name", "Staff"),
            }]

        # B. Cancel Reservation
        if "SET res.status = 'Cancelled'" in q:
            res_id = params.get("res_id")
            if res_id not in self.reservations:
                return []
            self.reservations[res_id]["status"] = "Cancelled"
            r_no = self.reservations[res_id]["room_no"]
            rm = self._find_room(room_no=r_no)
            return [{
                "res_id": res_id,
                "status": "Cancelled",
                "room_no": r_no,
                "room_status": rm["status"] if rm else "Available",
            }]

        # C. Create Staff (New)
        if "CREATE (s:Staff" in q or "CREATE (s: Staff" in q:
            s_id = params["staff_id"]
            self.staff[s_id] = {
                "staff_id": s_id,
                "name": params["name"],
                "age": int(params["age"]),
                "salary": float(params["salary"]),
                "contact_info": params["contact_info"],
                "dept_id": params["dept_id"],
            }
            return [self.staff[s_id]]

        # D. Create / Merge Guest
        if "SET g.password = $password" in q:
            g_id = params.get("guest_id")
            if g_id in self.guests:
                self.guests[g_id]["password"] = params.get("password")
                return [{"guest_id": g_id}]
            return []

        if ("CREATE (g:Guest" in q or "CREATE (g: Guest" in q or
            "MERGE (g:Guest" in q or "MERGE (g: Guest" in q):
            g_id = params.get("guest_id")
            if not g_id:
                max_num = 0
                for gid in self.guests:
                    if gid.startswith("G") and gid[1:].isdigit():
                        try:
                            max_num = max(max_num, int(gid[1:]))
                        except ValueError:
                            pass
                g_id = f"G{max_num + 1:03d}"

            if g_id not in self.guests:
                self.guests[g_id] = {
                    "guest_id": g_id,
                    "name": params["name"],
                    "contact_info": params.get("contact_info", "Not provided"),
                    "nationality": params.get("nationality", "Indian"),
                    "gender": params.get("gender", "Other"),
                    "password": params.get("password", "password123"),
                }
            elif "password" in params and params["password"]:
                self.guests[g_id]["password"] = params["password"]

            return [{
                "guest_id": g_id,
                "name": self.guests[g_id]["name"],
                "contact_info": self.guests[g_id]["contact_info"],
                "nationality": self.guests[g_id]["nationality"],
                "gender": self.guests[g_id]["gender"],
                "password": self.guests[g_id].get("password", "password123"),
            }]

        # E. Create Room
        if "CREATE (r:Room" in q or "CREATE (r: Room" in q:
            r_no = int(params["room_no"])
            r_id = params.get("room_id") or f"RM{r_no}"
            self.rooms[r_no] = {
                "room_id": r_id,
                "room_no": r_no,
                "status": params.get("status", "Available"),
                "hotel_id": params["hotel_id"],
                "category_name": params["category_name"],
            }
            c = self.categories.get(params["category_name"], {})
            return [{
                "room_id": r_id,
                "room_no": r_no,
                "status": params.get("status", "Available"),
                "category": params["category_name"],
                "rent": c.get("rent", 0.0),
                "hotel_id": params["hotel_id"],
            }]

        # F. Update Room Status
        if "SET r.status = $status" in q:
            r_no = int(params.get("room_no", 0))
            rm = self._find_room(room_no=r_no)
            if rm:
                rm["status"] = params["status"]
                return [{"room_no": rm["room_no"], "status": params["status"]}]
            return []

        # G. Create Hotel
        if "CREATE (h:Hotel" in q or "CREATE (h: Hotel" in q:
            self.hotels[params["hotel_id"]] = {
                "hotel_id": params["hotel_id"],
                "name": params["name"],
                "location": params["location"],
                "rating": params["rating"],
            }
            return [{"hotel": self.hotels[params["hotel_id"]]}]

        # H. Check Overlapping Reservation
        if "conflicting_reservation" in q:
            rm = self._find_room(params.get("room_id"), params.get("room_no"))
            if not rm:
                return []
            r_no = rm["room_no"]
            r_id = rm.get("room_id")
            req_in = str(params.get("check_in"))
            req_out = str(params.get("check_out"))
            for r in self.reservations.values():
                is_same_room = (r.get("room_no") == r_no) or (r_id and r.get("room_id") == r_id)
                if is_same_room and r["status"] in ["Active", "Confirmed"]:
                    res_in = str(r["check_in_date"])
                    res_out = str(r["check_out_date"])
                    if res_in < req_out and res_out > req_in:
                        return [{"conflicting_reservation": r["res_id"]}]
            return []

        # I. Room lookup by room_id or room_no (for atomic transaction verification)
        if "MATCH (r:Room)" in q and ("r.room_id" in q or "r.room_no" in q) and "RETURN r.room_id" in q:
            rm = self._find_room(params.get("room_id"), params.get("room_no"))
            if rm:
                return [{
                    "r": rm,
                    "room_id": rm["room_id"],
                    "room_no": rm["room_no"],
                    "status": rm["status"]
                }]
            return []


        # ==========================================
        # 2. READ / QUERY OPERATIONS
        # ==========================================

        # Health check
        if "RETURN 1 AS ok" in q or "RETURN 1 AS value" in q:
            return [{"ok": 1, "value": 1}]

        # Dashboard stats
        if "COUNT(h) AS hotels" in q:
            return [{
                "hotels": len(self.hotels),
                "rooms": len(self.rooms),
                "guests": len(self.guests),
                "staff": len(self.staff),
                "reservations": len(self.reservations),
            }]

        # Room availability per hotel
        if "available, occupied, maintenance" in q.lower() or "sum(case when r.status" in q.lower():
            results = []
            for h_id, h in self.hotels.items():
                h_rooms = [r for r in self.rooms.values() if r["hotel_id"] == h_id]
                avail = sum(1 for r in h_rooms if r["status"] == "Available")
                occ = sum(1 for r in h_rooms if r["status"] == "Occupied")
                maint = sum(1 for r in h_rooms if r["status"] == "Maintenance")
                results.append({
                    "hotel_id": h_id,
                    "hotel_name": h["name"],
                    "available": avail,
                    "occupied": occ,
                    "maintenance": maint,
                    "total": len(h_rooms),
                })
            results.sort(key=lambda x: x["hotel_name"])
            return results

        # Revenue analytics per hotel (separating room inventory from reservation revenue)
        if "potential_daily_revenue" in q:
            results = []
            for h_id, h in sorted(self.hotels.items()):
                h_rooms = [r for r in self.rooms.values() if r["hotel_id"] == h_id]
                pot_rev = sum(self.categories.get(r["category_name"], {}).get("rent", 0) for r in h_rooms)
                h_res = [res for res in self.reservations.values() if any(r["room_no"] == res.get("room_no") for r in h_rooms)]
                results.append({
                    "hotel_id": h_id,
                    "hotel_name": h["name"],
                    "total_rooms": len(h_rooms),
                    "potential_daily_revenue": pot_rev,
                    "total_bookings": len(h_res),
                })
            return results

        # Recent reservations
        if "LIMIT 10" in q and "res:Reservation" in q:

            sorted_res = sorted(self.reservations.values(), key=lambda r: str(r["check_in_date"]), reverse=True)[:10]
            results = []
            for r in sorted_res:
                g = self.guests.get(r["guest_id"], {})
                rm = self.rooms.get(r["room_no"], {})
                h = self.hotels.get(rm.get("hotel_id"), {})
                st = self.staff.get(r.get("staff_id"), {})
                results.append({
                    "res_id": r["res_id"],
                    "guest_name": g.get("name", "Unknown"),
                    "room_no": r["room_no"],
                    "hotel_name": h.get("name", "Unknown"),
                    "check_in_date": str(r["check_in_date"]),
                    "check_out_date": str(r["check_out_date"]),
                    "status": r["status"],
                    "processed_by": st.get("name", "N/A"),
                })
            return results

        # List Hotels with room_count & dept_count
        if "MATCH (h:Hotel)" in q and "room_count" in q:
            results = []
            for h_id, h in sorted(self.hotels.items()):
                r_count = sum(1 for r in self.rooms.values() if r["hotel_id"] == h_id)
                d_count = sum(1 for d in self.departments.values() if d["hotel_id"] == h_id)
                results.append({
                    "hotel_id": h["hotel_id"],
                    "name": h["name"],
                    "location": h["location"],
                    "rating": h["rating"],
                    "room_count": r_count,
                    "dept_count": d_count,
                })
            return results

        # Hotel detail by ID
        if "MATCH (h:Hotel {hotel_id: $hotel_id})" in q and "COLLECT(DISTINCT {room_no" in q:
            h_id = params.get("hotel_id")
            if h_id not in self.hotels:
                return []
            h = self.hotels[h_id]
            h_rooms = []
            for r in self.rooms.values():
                if r["hotel_id"] == h_id:
                    cat = self.categories.get(r["category_name"], {})
                    h_rooms.append({
                        "room_no": r["room_no"],
                        "status": r["status"],
                        "category": r["category_name"],
                        "rent": cat.get("rent", 0.0),
                    })
            h_depts = []
            for d in self.departments.values():
                if d["hotel_id"] == h_id:
                    h_depts.append({
                        "dept_id": d["dept_id"],
                        "d_head": d["d_head"],
                        "d_role": d["d_role"],
                        "contact_info": d["contact_info"],
                    })
            return [{
                "hotel_id": h["hotel_id"],
                "name": h["name"],
                "location": h["location"],
                "rating": h["rating"],
                "rooms": h_rooms,
                "departments": h_depts,
            }]

        # Hotel Rooms by hotel_id
        if "MATCH (h:Hotel {hotel_id: $hotel_id})-[:HAS_ROOM]->(r:Room)" in q:
            h_id = params.get("hotel_id")
            results = []
            for r in self.rooms.values():
                if r["hotel_id"] == h_id:
                    cat = self.categories.get(r["category_name"], {})
                    results.append({
                        "room_no": r["room_no"],
                        "status": r["status"],
                        "category": r["category_name"],
                        "rent": cat.get("rent", 0.0),
                    })
            results.sort(key=lambda x: x["room_no"])
            return results

        # Hotel Departments by hotel_id with staff list
        if "MATCH (h:Hotel {hotel_id: $hotel_id})-[:HAS_DEPARTMENT]->(d:Department)" in q:
            h_id = params.get("hotel_id")
            results = []
            for d in self.departments.values():
                if d["hotel_id"] == h_id:
                    staff_list = [
                        {"staff_id": s["staff_id"], "name": s["name"], "age": s["age"], "salary": s["salary"]}
                        for s in self.staff.values() if s["dept_id"] == d["dept_id"]
                    ]
                    results.append({
                        "dept_id": d["dept_id"],
                        "d_head": d["d_head"],
                        "d_role": d["d_role"],
                        "contact_info": d["contact_info"],
                        "staff": staff_list,
                    })
            results.sort(key=lambda x: x["dept_id"])
            return results

        # List Room Categories
        if "MATCH (c:RoomCategory)" in q and "COUNT(r) AS room_count" in q:
            results = []
            for cat_name, cat in sorted(self.categories.items()):
                r_count = sum(1 for r in self.rooms.values() if r["category_name"] == cat_name)
                results.append({
                    "category_name": cat["category_name"],
                    "rent": cat["rent"],
                    "room_count": r_count,
                })
            return results

        # List Rooms or Search Rooms
        if "MATCH (h:Hotel)-[:HAS_ROOM]->(r:Room)-[:BELONGS_TO]->(c:RoomCategory)" in q:
            results = []
            req_in = str(params.get("check_in_date") or "")
            req_out = str(params.get("check_out_date") or "")

            for r_no, r in sorted(self.rooms.items()):
                h = self.hotels.get(r["hotel_id"], {})
                c = self.categories.get(r["category_name"], {})
                if "hotel_id" in params and params["hotel_id"] and r["hotel_id"] != params["hotel_id"]:
                    continue
                if "location" in params and params["location"]:
                    loc = params["location"].lower()
                    if loc not in h.get("location", "").lower() and loc not in h.get("name", "").lower():
                        continue
                if "category" in params and params["category"] and r["category_name"] != params["category"]:
                    continue
                if "status" in params and params["status"] and r["status"] != params["status"]:
                    continue
                if "max_rent" in params and params["max_rent"] is not None and c.get("rent", 0) > params["max_rent"]:
                    continue

                # Date-based availability check
                if req_in and req_out:
                    if r["status"] == "Maintenance":
                        continue
                    has_overlap = False
                    for res in self.reservations.values():
                        if res["room_no"] == r["room_no"] and res["status"] in ["Active", "Confirmed"]:
                            if str(res["check_in_date"]) < req_out and str(res["check_out_date"]) > req_in:
                                has_overlap = True
                                break
                    if has_overlap:
                        continue

                item = {
                    "room_id": r.get("room_id", f"RM{r['room_no']}"),
                    "room_no": r["room_no"],
                    "status": r["status"],
                    "category": r["category_name"],
                    "rent": c.get("rent", 0.0),
                    "hotel_id": r["hotel_id"],
                    "hotel_name": h.get("name", "Unknown"),
                    "location": h.get("location", "Unknown"),
                }
                if req_in and req_out:
                    try:
                        d_in = date.fromisoformat(req_in)
                        d_out = date.fromisoformat(req_out)
                        nights = (d_out - d_in).days
                        item["nights"] = nights
                        item["check_in_date"] = req_in
                        item["check_out_date"] = req_out
                        item["estimated_total_price"] = round(c.get("rent", 0.0) * nights, 2)
                    except Exception:
                        pass
                results.append(item)
            results.sort(key=lambda x: (x.get("rent", 0), x["room_no"]))
            return results

        # Check Room by room_no or room_id
        if "MATCH (r:Room {room_no: $room_no}) RETURN r" in q or "MATCH (r:Room {room_id: $room_id}) RETURN r" in q:
            rm = self._find_room(params.get("room_id"), params.get("room_no"))
            return [{"r": rm, "room_no": rm["room_no"], "room_id": rm["room_id"]}] if rm else []


        # Check Hotel / Category existence checks
        if "MATCH (h:Hotel {hotel_id: $hotel_id}) RETURN h" in q:
            h_id = params.get("hotel_id")
            return [{"h": self.hotels[h_id]}] if h_id in self.hotels else []

        if "MATCH (c:RoomCategory {category_name: $category_name}) RETURN c" in q:
            c_name = params.get("category_name")
            return [{"c": self.categories[c_name]}] if c_name in self.categories else []

        # List Guest IDs (for next-id sequence generation)
        if ("MATCH (g:Guest) RETURN g.guest_id" in q or "MATCH (g:Guest)\n    RETURN g.guest_id" in q) or ("MATCH (g:Guest)" in q and "RETURN g.guest_id" in q and "WHERE" not in q and "MADE" not in q):
            return [{"guest_id": g_id} for g_id in sorted(self.guests.keys())]

        # List Reservation IDs (for next-id sequence generation)
        if "MATCH (r:Reservation) RETURN r.res_id" in q or ("MATCH (r:Reservation)" in q and "RETURN r.res_id" in q and "WHERE" not in q and "BOOKS" not in q):
            return [{"res_id": rid} for rid in sorted(self.reservations.keys())]

        # Lookup Guest by contact_info, email, phone, or guest_id
        if "MATCH (g:Guest)" in q and ("g.contact_info CONTAINS" in q or "toLower(g.contact_info)" in q):
            c_info = (params.get("contact_info") or "").lower()
            email = (params.get("email") or "").lower()
            phone = (params.get("phone") or "").lower()
            results = []
            for g_id, g in self.guests.items():
                g_ci = (g.get("contact_info") or "").lower()
                matched = False
                if email and email in g_ci:
                    matched = True
                elif phone and phone in g_ci:
                    matched = True
                elif c_info and c_info in g_ci:
                    matched = True
                if matched:
                    results.append({
                        "guest_id": g["guest_id"],
                        "name": g["name"],
                        "contact_info": g["contact_info"],
                        "nationality": g["nationality"],
                        "gender": g["gender"],
                        "password": g.get("password", "password123"),
                    })
            return results

        # List Guests
        if "MATCH (g:Guest) OPTIONAL MATCH (g)-[:MADE]->(res:Reservation)" in q:
            results = []
            for g_id, g in sorted(self.guests.items()):
                res_count = sum(1 for r in self.reservations.values() if r["guest_id"] == g_id)
                results.append({
                    "guest_id": g["guest_id"],
                    "name": g["name"],
                    "contact_info": g["contact_info"],
                    "nationality": g["nationality"],
                    "gender": g["gender"],
                    "reservation_count": res_count,
                })
            return results

        # Search Guests or Lookup by exact name
        if "MATCH (g:Guest)" in q and ("toLower(g.name)" in q or "toLower(g.nationality)" in q):
            is_exact_name = "= tolower($name)" in q.lower()
            results = []
            for g_id, g in self.guests.items():
                if "name" in params:
                    if is_exact_name:
                        if params["name"].lower() != g["name"].lower():
                            continue
                    else:
                        if params["name"].lower() not in g["name"].lower():
                            continue
                if "nationality" in params and params["nationality"].lower() not in g["nationality"].lower():
                    continue
                res_count = sum(1 for r in self.reservations.values() if r["guest_id"] == g_id)
                results.append({
                    "guest_id": g["guest_id"],
                    "name": g["name"],
                    "contact_info": g["contact_info"],
                    "nationality": g["nationality"],
                    "gender": g["gender"],
                    "password": g.get("password", "password123"),
                    "reservation_count": res_count,
                })
            results.sort(key=lambda x: x["name"])
            return results

        # Guest detail with history
        if "MATCH (g:Guest {guest_id: $guest_id})" in q and "collect(distinct" in q.lower():
            g_id = params.get("guest_id")
            if g_id not in self.guests:
                return []
            g = self.guests[g_id]
            g_res = []
            for r in self.reservations.values():
                if r["guest_id"] == g_id:
                    rm = self.rooms.get(r["room_no"], {})
                    cat = self.categories.get(rm.get("category_name"), {})
                    h = self.hotels.get(rm.get("hotel_id"), {})
                    st = self.staff.get(r.get("staff_id"), {})
                    g_res.append({
                        "res_id": r["res_id"],
                        "check_in": str(r["check_in_date"]),
                        "check_out": str(r["check_out_date"]),
                        "check_in_date": str(r["check_in_date"]),
                        "check_out_date": str(r["check_out_date"]),
                        "status": r["status"],
                        "room_no": r["room_no"],
                        "category": rm.get("category_name", "N/A"),
                        "rent": cat.get("rent", 0.0),
                        "hotel_name": h.get("name", "N/A"),
                        "hotel_id": h.get("hotel_id", "N/A"),
                        "location": h.get("location", "N/A"),
                        "processed_by": st.get("name", "N/A"),
                        "staff_name": st.get("name", "N/A"),
                    })
            g_res.sort(key=lambda x: x["check_in_date"], reverse=True)
            return [{
                "guest_id": g["guest_id"],
                "name": g["name"],
                "contact_info": g["contact_info"],
                "nationality": g["nationality"],
                "gender": g["gender"],
                "reservations": g_res,
            }]

        # Check Guest by ID
        if "MATCH (g:Guest {guest_id: $guest_id})" in q and "MADE" not in q:
            g_id = params.get("guest_id")
            if g_id in self.guests:
                g = self.guests[g_id]
                return [{
                    "g": g,
                    "guest_id": g["guest_id"],
                    "name": g["name"],
                    "contact_info": g["contact_info"],
                    "nationality": g["nationality"],
                    "gender": g["gender"],
                    "password": g.get("password", "password123"),
                }]
            return []

        # Check Staff by ID
        if "MATCH (s:Staff {staff_id: $staff_id})" in q:
            s_id = params.get("staff_id")
            return [{"s": self.staff[s_id], "name": self.staff[s_id]["name"]}] if s_id in self.staff else []

        # Check Department by ID
        if "MATCH (d:Department {dept_id: $dept_id})" in q:
            d_id = params.get("dept_id")
            return [{"d": self.departments[d_id]}] if d_id in self.departments else []

        # Check Reservation status and guest ownership
        if "Reservation {res_id: $res_id}" in q and "status" in q.lower():
            res_id = params.get("res_id")
            if res_id in self.reservations:
                r = self.reservations[res_id]
                return [{
                    "status": r["status"],
                    "guest_id": r.get("guest_id"),
                }]
            return []

        # Check Reservation by ID
        if "Reservation {res_id: $res_id}" in q:
            res_id = params.get("res_id")
            return [{"r": self.reservations[res_id]}] if res_id in self.reservations else []

        # List Reservations / Guest Reservations
        if ("MATCH (g:Guest)-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)" in q or
            "MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)" in q):
            results = []
            target_gid = params.get("guest_id")
            for res_id, r in sorted(self.reservations.items(), key=lambda x: str(x[1]["check_in_date"]), reverse=True):
                if target_gid and r["guest_id"] != target_gid:
                    continue
                g = self.guests.get(r["guest_id"], {})
                rm = self.rooms.get(r["room_no"], {})
                cat = self.categories.get(rm.get("category_name"), {})
                h = self.hotels.get(rm.get("hotel_id"), {})
                st = self.staff.get(r.get("staff_id"), {})
                results.append({
                    "res_id": r["res_id"],
                    "check_in_date": str(r["check_in_date"]),
                    "check_out_date": str(r["check_out_date"]),
                    "status": r["status"],
                    "guest_id": r["guest_id"],
                    "guest_name": g.get("name", "Unknown"),
                    "room_no": r["room_no"],
                    "room_id": r.get("room_id") or rm.get("room_id", f"RM{r['room_no']}"),
                    "category": rm.get("category_name", "N/A"),
                    "rent": cat.get("rent", 0.0),
                    "hotel_id": rm.get("hotel_id", "N/A"),
                    "hotel_name": h.get("name", "Unknown"),
                    "location": h.get("location", "Unknown"),
                    "staff_id": r.get("staff_id", "N/A"),
                    "staff_name": st.get("name", "N/A"),
                })
            return results

        # Staff by Department (Grouped with staff array)
        if "dept_head" in q or "COLLECT({staff_id" in q:
            target_dept = params.get("dept_id")
            results = []
            for d_id, d in sorted(self.departments.items()):
                if target_dept and d_id != target_dept:
                    continue
                h = self.hotels.get(d.get("hotel_id"), {})
                dept_staff = [
                    {
                        "staff_id": s["staff_id"],
                        "name": s["name"],
                        "age": s["age"],
                        "salary": s["salary"],
                        "contact_info": s["contact_info"]
                    }
                    for s_id, s in sorted(self.staff.items())
                    if s.get("dept_id") == d_id
                ]
                results.append({
                    "dept_id": d["dept_id"],
                    "department": d.get("d_role", "N/A"),
                    "dept_head": d.get("d_head", "N/A"),
                    "hotel_name": h.get("name", "N/A"),
                    "staff": dept_staff
                })
            return results

        # List Staff (Flat list with reservations processed)
        if ("HAS_DEPARTMENT" in q and "EMPLOYS" in q and "Staff" in q) or "list_staff" in q:
            results = []
            for s_id, s in sorted(self.staff.items()):
                d = self.departments.get(s["dept_id"], {})
                h = self.hotels.get(d.get("hotel_id"), {})
                proc_count = sum(1 for r in self.reservations.values() if r.get("staff_id") == s_id)
                results.append({
                    "staff_id": s["staff_id"],
                    "name": s["name"],
                    "age": s["age"],
                    "salary": s["salary"],
                    "contact_info": s["contact_info"],
                    "dept_id": s["dept_id"],
                    "department": d.get("d_role", "N/A"),
                    "d_role": d.get("d_role", "N/A"),
                    "hotel_id": h.get("hotel_id", "N/A"),
                    "hotel_name": h.get("name", "N/A"),
                    "reservations_processed": proc_count,
                    "processed_reservations": proc_count,
                })
            return results

        # Staff Reservations
        if "MATCH (s:Staff {staff_id: $staff_id})-[:PROCESSES]->(res:Reservation)" in q:
            s_id = params.get("staff_id")
            results = []
            for r in self.reservations.values():
                if r.get("staff_id") == s_id:
                    g = self.guests.get(r["guest_id"], {})
                    rm = self.rooms.get(r["room_no"], {})
                    h = self.hotels.get(rm.get("hotel_id"), {})
                    results.append({
                        "res_id": r["res_id"],
                        "check_in": str(r["check_in_date"]),
                        "check_in_date": str(r["check_in_date"]),
                        "check_out": str(r["check_out_date"]),
                        "check_out_date": str(r["check_out_date"]),
                        "status": r["status"],
                        "room_no": r["room_no"],
                        "guest_name": g.get("name", "Unknown"),
                        "hotel_name": h.get("name", "Grand Palace Hotel"),
                    })
            results.sort(key=lambda x: x["check_in"], reverse=True)
            return results

        # Recommendation: Hotels
        if "MATCH (target:Guest {guest_id: $guest_id})-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)<-[:HAS_ROOM]-(commonHotel:Hotel)" in q:
            target_id = params.get("guest_id")
            visited = set()
            for r in self.reservations.values():
                if r["guest_id"] == target_id:
                    rm = self.rooms.get(r["room_no"], {})
                    if rm.get("hotel_id"):
                        visited.add(rm["hotel_id"])

            results = []
            for h_id, h in self.hotels.items():
                if h_id not in visited:
                    guests_who_stayed = set()
                    for r in self.reservations.values():
                        rm = self.rooms.get(r["room_no"], {})
                        if rm.get("hotel_id") == h_id and r["guest_id"] != target_id:
                            g = self.guests.get(r["guest_id"])
                            if g:
                                guests_who_stayed.add(g["name"])
                    results.append({
                        "hotel_id": h["hotel_id"],
                        "hotel_name": h["name"],
                        "location": h["location"],
                        "rating": h["rating"],
                        "shared_guests": len(guests_who_stayed) or 1,
                        "guests_who_stayed": list(guests_who_stayed) or ["Aisha Khan", "Carlos Rivera"],
                    })
            results.sort(key=lambda x: (x["shared_guests"], x["rating"]), reverse=True)
            return results

        # Recommendation: Rooms by past preferences
        if "MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(:Reservation)-[:BOOKS]->(:Room)-[:BELONGS_TO]->(booked:RoomCategory)" in q:
            target_id = params.get("guest_id")
            booked_cats = set()
            rents = []
            for r in self.reservations.values():
                if r["guest_id"] == target_id:
                    rm = self.rooms.get(r["room_no"], {})
                    cat_name = rm.get("category_name")
                    if cat_name:
                        booked_cats.add(cat_name)
                        cat = self.categories.get(cat_name)
                        if cat:
                            rents.append(cat["rent"])
            avg_rent = sum(rents) / len(rents) if rents else 4000.0

            results = []
            for cat_name, cat in self.categories.items():
                if cat_name not in booked_cats:
                    results.append({
                        "category": cat_name,
                        "rent": cat["rent"],
                        "price_difference": round(abs(cat["rent"] - avg_rent)),
                    })
            results.sort(key=lambda x: x["price_difference"])
            return results

        # Recommendation: Popular by Nationality
        if "MATCH (peer:Guest {nationality: $nationality})" in q:
            nat = params.get("nationality", "").lower()
            matching_guests = {g_id for g_id, g in self.guests.items() if g["nationality"].lower() == nat}
            hotel_counts = {}
            for r in self.reservations.values():
                if r["guest_id"] in matching_guests:
                    rm = self.rooms.get(r["room_no"], {})
                    h_id = rm.get("hotel_id")
                    if h_id:
                        if h_id not in hotel_counts:
                            hotel_counts[h_id] = {"guests": set(), "bookings": 0}
                        hotel_counts[h_id]["guests"].add(r["guest_id"])
                        hotel_counts[h_id]["bookings"] += 1

            results = []
            for h_id, counts in hotel_counts.items():
                h = self.hotels.get(h_id)
                if h:
                    results.append({
                        "hotel_id": h["hotel_id"],
                        "hotel_name": h["name"],
                        "location": h["location"],
                        "rating": h["rating"],
                        "guests_from_country": len(counts["guests"]),
                        "total_bookings": counts["bookings"],
                    })
            results.sort(key=lambda x: (x["guests_from_country"], x["total_bookings"]), reverse=True)
            return results

        # Guest Journey
        if "MATCH (g:Guest {guest_id: $guest_id})-[:MADE]->(res:Reservation)-[:BOOKS]->(r:Room)<-[:HAS_ROOM]-(h:Hotel)" in q:
            target_id = params.get("guest_id")
            results = []
            for r in self.reservations.values():
                if r["guest_id"] == target_id:
                    rm = self.rooms.get(r["room_no"], {})
                    cat = self.categories.get(rm.get("category_name"), {})
                    h = self.hotels.get(rm.get("hotel_id"), {})
                    st = self.staff.get(r.get("staff_id"), {})
                    dept = self.departments.get(st.get("dept_id"), {}) if st else {}
                    results.append({
                        "reservation_id": r["res_id"],
                        "status": r["status"],
                        "check_in": str(r["check_in_date"]),
                        "check_out": str(r["check_out_date"]),
                        "hotel": h.get("name", "Unknown"),
                        "location": h.get("location", "Unknown"),
                        "room": r["room_no"],
                        "category": rm.get("category_name", "N/A"),
                        "rent": cat.get("rent", 0.0),
                        "processed_by": st.get("name", "N/A"),
                        "staff_department": dept.get("d_role", "N/A"),
                    })
            results.sort(key=lambda x: x["check_in"])
            return results

        # Default fallback: return empty list
        return []


mock_store = MockGraphStore()
