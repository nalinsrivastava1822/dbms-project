// ============================================================
// 02_seed_data.cypher
// Hotel Management System — Idempotent Sample Data
// ============================================================
// Uses MERGE to prevent duplicate nodes on re-run.
// Run 01_constraints.cypher FIRST to enforce uniqueness.
// ============================================================

// --- Hotels ---
MERGE (h1:Hotel {hotel_id: 'H001'})
  SET h1.name = 'Grand Palace Hotel', h1.location = 'Mumbai', h1.rating = 4.5;
MERGE (h2:Hotel {hotel_id: 'H002'})
  SET h2.name = 'Royal Orchid Resort', h2.location = 'Delhi', h2.rating = 4.2;
MERGE (h3:Hotel {hotel_id: 'H003'})
  SET h3.name = 'Seaside Inn', h3.location = 'Goa', h3.rating = 3.8;

// --- Room Categories ---
MERGE (c1:RoomCategory {category_name: 'Standard'})
  SET c1.rent = 2500;
MERGE (c2:RoomCategory {category_name: 'Deluxe'})
  SET c2.rent = 5000;
MERGE (c3:RoomCategory {category_name: 'Suite'})
  SET c3.rent = 10000;
MERGE (c4:RoomCategory {category_name: 'Executive'})
  SET c4.rent = 7500;

// --- Rooms for Grand Palace Hotel (H001) ---
MERGE (r101:Room {room_id: 'RM101'}) SET r101.room_no = 101, r101.status = 'Available';
MERGE (r102:Room {room_id: 'RM102'}) SET r102.room_no = 102, r102.status = 'Available';
MERGE (r103:Room {room_id: 'RM103'}) SET r103.room_no = 103, r103.status = 'Available';
MERGE (r104:Room {room_id: 'RM104'}) SET r104.room_no = 104, r104.status = 'Available';
MERGE (r105:Room {room_id: 'RM105'}) SET r105.room_no = 105, r105.status = 'Maintenance';

// --- Rooms for Royal Orchid Resort (H002) ---
MERGE (r201:Room {room_id: 'RM201'}) SET r201.room_no = 201, r201.status = 'Available';
MERGE (r202:Room {room_id: 'RM202'}) SET r202.room_no = 202, r202.status = 'Available';
MERGE (r203:Room {room_id: 'RM203'}) SET r203.room_no = 203, r203.status = 'Available';
MERGE (r204:Room {room_id: 'RM204'}) SET r204.room_no = 204, r204.status = 'Available';

// --- Rooms for Seaside Inn (H003) ---
MERGE (r301:Room {room_id: 'RM301'}) SET r301.room_no = 301, r301.status = 'Available';
MERGE (r302:Room {room_id: 'RM302'}) SET r302.room_no = 302, r302.status = 'Available';
MERGE (r303:Room {room_id: 'RM303'}) SET r303.room_no = 303, r303.status = 'Available';

// --- Hotel-Room relationships ---
MATCH (h:Hotel {hotel_id: 'H001'}), (r:Room) WHERE r.room_no IN [101,102,103,104,105]
MERGE (h)-[:HAS_ROOM]->(r);

MATCH (h:Hotel {hotel_id: 'H002'}), (r:Room) WHERE r.room_no IN [201,202,203,204]
MERGE (h)-[:HAS_ROOM]->(r);

MATCH (h:Hotel {hotel_id: 'H003'}), (r:Room) WHERE r.room_no IN [301,302,303]
MERGE (h)-[:HAS_ROOM]->(r);

// --- Room-Category relationships ---
MATCH (r:Room) WHERE r.room_no IN [101, 201, 301]
MATCH (c:RoomCategory {category_name: 'Standard'})
MERGE (r)-[:BELONGS_TO]->(c);

MATCH (r:Room) WHERE r.room_no IN [102, 202, 302]
MATCH (c:RoomCategory {category_name: 'Deluxe'})
MERGE (r)-[:BELONGS_TO]->(c);

MATCH (r:Room) WHERE r.room_no IN [103, 203, 303]
MATCH (c:RoomCategory {category_name: 'Suite'})
MERGE (r)-[:BELONGS_TO]->(c);

MATCH (r:Room) WHERE r.room_no IN [104, 204]
MATCH (c:RoomCategory {category_name: 'Executive'})
MERGE (r)-[:BELONGS_TO]->(c);

MATCH (r:Room {room_no: 105})
MATCH (c:RoomCategory {category_name: 'Standard'})
MERGE (r)-[:BELONGS_TO]->(c);

// --- Departments ---
MERGE (d1:Department {dept_id: 'D001'})
  SET d1.d_head = 'Rajesh Kumar', d1.d_role = 'Front Desk', d1.contact_info = '9876543210';
MERGE (d2:Department {dept_id: 'D002'})
  SET d2.d_head = 'Priya Sharma', d2.d_role = 'Housekeeping', d2.contact_info = '9876543211';
MERGE (d3:Department {dept_id: 'D003'})
  SET d3.d_head = 'Amit Patel', d3.d_role = 'Front Desk', d3.contact_info = '9876543212';
MERGE (d4:Department {dept_id: 'D004'})
  SET d4.d_head = 'Sneha Reddy', d4.d_role = 'Restaurant', d4.contact_info = '9876543213';
MERGE (d5:Department {dept_id: 'D005'})
  SET d5.d_head = 'Vikram Singh', d5.d_role = 'Front Desk', d5.contact_info = '9876543214';

// --- Hotel-Department relationships ---
MATCH (h:Hotel {hotel_id: 'H001'}), (d:Department) WHERE d.dept_id IN ['D001','D002']
MERGE (h)-[:HAS_DEPARTMENT]->(d);

MATCH (h:Hotel {hotel_id: 'H002'}), (d:Department) WHERE d.dept_id IN ['D003','D004']
MERGE (h)-[:HAS_DEPARTMENT]->(d);

MATCH (h:Hotel {hotel_id: 'H003'}), (d:Department {dept_id: 'D005'})
MERGE (h)-[:HAS_DEPARTMENT]->(d);

// --- Staff ---
MERGE (s1:Staff {staff_id: 'S001'})
  SET s1.name = 'Arjun Mehta', s1.age = 28, s1.salary = 35000, s1.contact_info = '9111111111';
MERGE (s2:Staff {staff_id: 'S002'})
  SET s2.name = 'Meera Joshi', s2.age = 32, s2.salary = 30000, s2.contact_info = '9222222222';
MERGE (s3:Staff {staff_id: 'S003'})
  SET s3.name = 'Rahul Verma', s3.age = 25, s3.salary = 32000, s3.contact_info = '9333333333';
MERGE (s4:Staff {staff_id: 'S004'})
  SET s4.name = 'Kavitha Nair', s4.age = 30, s4.salary = 28000, s4.contact_info = '9444444444';
MERGE (s5:Staff {staff_id: 'S005'})
  SET s5.name = 'Deepak Rao', s5.age = 35, s5.salary = 40000, s5.contact_info = '9555555555';
MERGE (s6:Staff {staff_id: 'S006'})
  SET s6.name = 'Anita Kulkarni', s6.age = 27, s6.salary = 33000, s6.contact_info = '9666666666';

// --- Department-Staff relationships ---
MATCH (d:Department {dept_id: 'D001'}), (s:Staff) WHERE s.staff_id IN ['S001','S002']
MERGE (d)-[:EMPLOYS]->(s);

MATCH (d:Department {dept_id: 'D002'}), (s:Staff {staff_id: 'S003'})
MERGE (d)-[:EMPLOYS]->(s);

MATCH (d:Department {dept_id: 'D003'}), (s:Staff {staff_id: 'S004'})
MERGE (d)-[:EMPLOYS]->(s);

MATCH (d:Department {dept_id: 'D004'}), (s:Staff {staff_id: 'S005'})
MERGE (d)-[:EMPLOYS]->(s);

MATCH (d:Department {dept_id: 'D005'}), (s:Staff {staff_id: 'S006'})
MERGE (d)-[:EMPLOYS]->(s);

// --- Guests ---
MERGE (g1:Guest {guest_id: 'G001'})
  SET g1.name = 'John Smith', g1.contact_info = '1234567890', g1.nationality = 'American', g1.gender = 'Male';
MERGE (g2:Guest {guest_id: 'G002'})
  SET g2.name = 'Aisha Khan', g2.contact_info = '2345678901', g2.nationality = 'Indian', g2.gender = 'Female';
MERGE (g3:Guest {guest_id: 'G003'})
  SET g3.name = 'Carlos Rivera', g3.contact_info = '3456789012', g3.nationality = 'Mexican', g3.gender = 'Male';
MERGE (g4:Guest {guest_id: 'G004'})
  SET g4.name = 'Emily Chen', g4.contact_info = '4567890123', g4.nationality = 'Chinese', g4.gender = 'Female';
MERGE (g5:Guest {guest_id: 'G005'})
  SET g5.name = 'Ravi Iyer', g5.contact_info = '5678901234', g5.nationality = 'Indian', g5.gender = 'Male';
MERGE (g6:Guest {guest_id: 'G006'})
  SET g6.name = 'Sophie Martin', g6.contact_info = '6789012345', g6.nationality = 'French', g6.gender = 'Female';
MERGE (g7:Guest {guest_id: 'G007'})
  SET g7.name = 'David Brown', g7.contact_info = '7890123456', g7.nationality = 'American', g7.gender = 'Male';
MERGE (g8:Guest {guest_id: 'G008'})
  SET g8.name = 'Nisha Gupta', g8.contact_info = '8901234567', g8.nationality = 'Indian', g8.gender = 'Female';

// --- Reservations ---
// Active reservations (rooms currently occupied)
MERGE (res1:Reservation {res_id: 'R001'})
  SET res1.check_in_date = date('2026-10-10'), res1.check_out_date = date('2026-10-15'), res1.status = 'Active';
MERGE (res2:Reservation {res_id: 'R002'})
  SET res2.check_in_date = date('2026-10-09'), res2.check_out_date = date('2026-10-13'), res2.status = 'Active';
MERGE (res3:Reservation {res_id: 'R003'})
  SET res3.check_in_date = date('2026-10-11'), res3.check_out_date = date('2026-10-14'), res3.status = 'Active';

// Completed reservations (past stays)
MERGE (res4:Reservation {res_id: 'R004'})
  SET res4.check_in_date = date('2026-09-01'), res4.check_out_date = date('2026-09-05'), res4.status = 'Completed';
MERGE (res5:Reservation {res_id: 'R005'})
  SET res5.check_in_date = date('2026-09-10'), res5.check_out_date = date('2026-09-14'), res5.status = 'Completed';
MERGE (res6:Reservation {res_id: 'R006'})
  SET res6.check_in_date = date('2026-09-15'), res6.check_out_date = date('2026-09-20'), res6.status = 'Completed';
MERGE (res7:Reservation {res_id: 'R007'})
  SET res7.check_in_date = date('2026-08-20'), res7.check_out_date = date('2026-08-25'), res7.status = 'Completed';

// Cancelled reservation
MERGE (res8:Reservation {res_id: 'R008'})
  SET res8.check_in_date = date('2026-10-20'), res8.check_out_date = date('2026-10-25'), res8.status = 'Cancelled';

// Future reservation
MERGE (res9:Reservation {res_id: 'R009'})
  SET res9.check_in_date = date('2026-11-01'), res9.check_out_date = date('2026-11-05'), res9.status = 'Confirmed';

// --- Guest-Reservation relationships ---
MATCH (g:Guest {guest_id: 'G001'}), (r:Reservation {res_id: 'R001'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G002'}), (r:Reservation {res_id: 'R002'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G003'}), (r:Reservation {res_id: 'R003'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G001'}), (r:Reservation {res_id: 'R004'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G004'}), (r:Reservation {res_id: 'R005'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G002'}), (r:Reservation {res_id: 'R006'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G005'}), (r:Reservation {res_id: 'R007'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G006'}), (r:Reservation {res_id: 'R008'}) MERGE (g)-[:MADE]->(r);
MATCH (g:Guest {guest_id: 'G007'}), (r:Reservation {res_id: 'R009'}) MERGE (g)-[:MADE]->(r);

// --- Reservation-Room relationships ---
MATCH (r:Reservation {res_id: 'R001'}), (rm:Room {room_no: 103}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R002'}), (rm:Room {room_no: 202}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R003'}), (rm:Room {room_no: 302}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R004'}), (rm:Room {room_no: 101}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R005'}), (rm:Room {room_no: 201}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R006'}), (rm:Room {room_no: 102}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R007'}), (rm:Room {room_no: 301}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R008'}), (rm:Room {room_no: 104}) MERGE (r)-[:BOOKS]->(rm);
MATCH (r:Reservation {res_id: 'R009'}), (rm:Room {room_no: 203}) MERGE (r)-[:BOOKS]->(rm);

// --- Staff-Reservation relationships ---
MATCH (s:Staff {staff_id: 'S001'}), (r:Reservation {res_id: 'R001'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S001'}), (r:Reservation {res_id: 'R004'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S004'}), (r:Reservation {res_id: 'R002'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S004'}), (r:Reservation {res_id: 'R005'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S006'}), (r:Reservation {res_id: 'R003'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S006'}), (r:Reservation {res_id: 'R007'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S002'}), (r:Reservation {res_id: 'R006'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S001'}), (r:Reservation {res_id: 'R008'}) MERGE (s)-[:PROCESSES]->(r);
MATCH (s:Staff {staff_id: 'S004'}), (r:Reservation {res_id: 'R009'}) MERGE (s)-[:PROCESSES]->(r);
