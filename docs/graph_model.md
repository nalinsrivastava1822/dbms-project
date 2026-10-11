# Graph Data Model Specification — Hotel Management System (Neo4j)

## 1. Executive Summary

This document specifies the Graph Data Model for the **Hotel Management System**, developed for **DBMS Digital Assignment 3 (DA3)**. In DA1 and DA2, the system was implemented using a traditional Relational Database Management System (RDBMS) with normalized tables (up to BCNF), foreign keys, and SQL/PL-SQL procedures. 

In DA3, the system is re-engineered using **Neo4j** (Labeled Property Graph model) and **Cypher Query Language**. The graph model replaces rigid foreign keys and join tables with first-class **Nodes** and directed **Relationships**, leveraging **Index-Free Adjacency** for high-performance traversals.

---

## 2. Relational vs. Graph Model Mapping

| Relational Entity / Concept (DA1 & DA2) | Neo4j Graph Model Element (DA3) | Transformation Rationale |
|---|---|---|
| `Hotel` Table | `:Hotel` Node | Represents hotel branch entity with properties (`hotel_id`, `name`, `location`, `rating`). |
| `RoomCategory` Table | `:RoomCategory` Node | Represents pricing tier/category with properties (`category_name`, `rent`). |
| `Room` Table | `:Room` Node | Represents physical room (`room_no`, `status`). Foreign keys replaced by relationships. |
| `Department` Table | `:Department` Node | Represents administrative unit (`dept_id`, `d_head`, `d_role`, `contact_info`). |
| `Staff` Table | `:Staff` Node | Represents personnel (`staff_id`, `name`, `age`, `salary`, `contact_info`). |
| `Guest` Table | `:Guest` Node | Represents hotel patron (`guest_id`, `name`, `contact_info`, `nationality`, `gender`). |
| `Reservation` Table | `:Reservation` Node | Represents booking transaction (`res_id`, `check_in_date`, `check_out_date`, `status`). |
| Foreign Key `Room.Hotel_ID` | `(:Hotel)-[:HAS_ROOM]->(:Room)` | Explicit directed edge; removes table scan and foreign key lookups. |
| Foreign Key `Room.Category_Name` | `(:Room)-[:BELONGS_TO]->(:RoomCategory)` | Connects room to its rate definition without relational JOIN. |
| Foreign Key `Department.Hotel_ID` | `(:Hotel)-[:HAS_DEPARTMENT]->(:Department)` | Encapsulates department ownership by hotel. |
| Foreign Key `Staff.Dept_ID` | `(:Department)-[:EMPLOYS]->(:Staff)` | Direct organizational relationship. |
| Foreign Key `Reservation.Guest_ID` | `(:Guest)-[:MADE]->(:Reservation)` | Tracks guest reservation history directly. |
| Foreign Key `Reservation.Room_No` | `(:Reservation)-[:BOOKS]->(:Room)` | Connects reservation directly to room node. |
| Foreign Key `Reservation.Staff_ID` | `(:Staff)-[:PROCESSES]->(:Reservation)` | Tracks staff handling of bookings. |

---

## 3. Node Definitions and Properties

### 3.1 `:Hotel`
- **Label**: `Hotel`
- **Business Key**: `hotel_id` (String, e.g., `'H001'`) — Unique Constraint
- **Properties**:
  - `hotel_id`: `STRING` (Mandatory, Unique)
  - `name`: `STRING` (Mandatory)
  - `location`: `STRING` (Mandatory)
  - `rating`: `FLOAT` (Range: 0.0 to 5.0)

### 3.2 `:RoomCategory`
- **Label**: `RoomCategory`
- **Business Key**: `category_name` (String, e.g., `'Deluxe'`) — Unique Constraint
- **Properties**:
  - `category_name`: `STRING` (Mandatory, Unique)
  - `rent`: `FLOAT` (Mandatory, > 0.0)

### 3.3 `:Room`
- **Label**: `Room`
- **Business Key**: `room_no` (Integer, e.g., `101`) — Unique Constraint
- **Properties**:
  - `room_no`: `INTEGER` (Mandatory, Unique across chain)
  - `status`: `STRING` (Enum: `'Available'`, `'Occupied'`, `'Maintenance'`)

### 3.4 `:Department`
- **Label**: `Department`
- **Business Key**: `dept_id` (String, e.g., `'D001'`) — Unique Constraint
- **Properties**:
  - `dept_id`: `STRING` (Mandatory, Unique)
  - `d_head`: `STRING` (Mandatory, Head of Department name)
  - `d_role`: `STRING` (Mandatory, Operational role, e.g., `'Front Desk'`)
  - `contact_info`: `STRING` (Mandatory, Phone or extension)

### 3.5 `:Staff`
- **Label**: `Staff`
- **Business Key**: `staff_id` (String, e.g., `'S001'`) — Unique Constraint
- **Properties**:
  - `staff_id`: `STRING` (Mandatory, Unique)
  - `name`: `STRING` (Mandatory)
  - `age`: `INTEGER` (Mandatory, 18-99)
  - `salary`: `FLOAT` (Mandatory, > 0.0)
  - `contact_info`: `STRING` (Mandatory)

### 3.6 `:Guest`
- **Label**: `Guest`
- **Business Key**: `guest_id` (String, e.g., `'G001'`) — Unique Constraint
- **Properties**:
  - `guest_id`: `STRING` (Mandatory, Unique)
  - `name`: `STRING` (Mandatory)
  - `contact_info`: `STRING` (Mandatory)
  - `nationality`: `STRING` (Mandatory)
  - `gender`: `STRING` (Enum: `'Male'`, `'Female'`, `'Other'`)

### 3.7 `:Reservation`
- **Label**: `Reservation`
- **Business Key**: `res_id` (String, e.g., `'R001'`) — Unique Constraint
- **Properties**:
  - `res_id`: `STRING` (Mandatory, Unique)
  - `check_in_date`: `DATE` (ISO 8601 date, e.g., `date('2026-11-01')`)
  - `check_out_date`: `DATE` (ISO 8601 date, e.g., `date('2026-11-05')`)
  - `status`: `STRING` (Enum: `'Confirmed'`, `'Cancelled'`, `'Completed'`)

---

## 4. Relationship Types and Semantics

```mermaid
graph LR
    Hotel((Hotel)) -->|HAS_ROOM| Room((Room))
    Room -->|BELONGS_TO| RoomCategory((RoomCategory))
    Hotel -->|HAS_DEPARTMENT| Department((Department))
    Department -->|EMPLOYS| Staff((Staff))
    Guest((Guest)) -->|MADE| Reservation((Reservation))
    Reservation -->|BOOKS| Room
    Staff -->|PROCESSES| Reservation
```

| Relationship Type | Source Node | Target Node | Cardinality | Semantic Description |
|---|---|---|---|---|
| `HAS_ROOM` | `Hotel` | `Room` | `1 : N` | A hotel branch manages and contains multiple physical rooms. |
| `BELONGS_TO` | `Room` | `RoomCategory` | `N : 1` | Each room belongs to exactly one category determining nightly rent. |
| `HAS_DEPARTMENT` | `Hotel` | `Department` | `1 : N` | A hotel contains multiple administrative and functional departments. |
| `EMPLOYS` | `Department` | `Staff` | `1 : N` | A department employs multiple staff members. |
| `MADE` | `Guest` | `Reservation` | `1 : N` | A registered guest initiates and holds one or more reservations. |
| `BOOKS` | `Reservation` | `Room` | `N : 1` | A reservation reserves a specific physical room for a date range. |
| `PROCESSES` | `Staff` | `Reservation` | `1 : N` | A staff member handles booking check-in, confirmation, or checkout. |

---

## 5. Schema Constraints and Indexing Strategy

In Neo4j 5.x+, schema constraints enforce data integrity and automatically create underlying b-tree/range indexes:

```cypher
// 1. Uniqueness Constraints (acts as Primary Keys & creates Indexes)
CREATE CONSTRAINT hotel_id_unique IF NOT EXISTS
FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE;

CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (rc:RoomCategory) REQUIRE rc.category_name IS UNIQUE;

CREATE CONSTRAINT room_no_unique IF NOT EXISTS
FOR (r:Room) REQUIRE r.room_no IS UNIQUE;

CREATE CONSTRAINT dept_id_unique IF NOT EXISTS
FOR (d:Department) REQUIRE d.dept_id IS UNIQUE;

CREATE CONSTRAINT staff_id_unique IF NOT EXISTS
FOR (s:Staff) REQUIRE s.staff_id IS UNIQUE;

CREATE CONSTRAINT guest_id_unique IF NOT EXISTS
FOR (g:Guest) REQUIRE g.guest_id IS UNIQUE;

CREATE CONSTRAINT res_id_unique IF NOT EXISTS
FOR (res:Reservation) REQUIRE res.res_id IS UNIQUE;

// 2. Performance Lookup Indexes
CREATE INDEX guest_nationality_idx IF NOT EXISTS
FOR (g:Guest) ON (g.nationality);

CREATE INDEX room_status_idx IF NOT EXISTS
FOR (r:Room) ON (r.status);

CREATE INDEX res_status_dates_idx IF NOT EXISTS
FOR (res:Reservation) ON (res.status, res.check_in_date, res.check_out_date);
```

---

## 6. Graph Traversal and Algorithmic Advantages

### 6.1 Index-Free Adjacency (IFA)
In a relational database, finding a guest's reserved rooms and associated hotel details requires joining four tables:
$$\text{Guest} \bowtie \text{Reservation} \bowtie \text{Room} \bowtie \text{Hotel}$$
Each join performs an index lookup ($O(\log N)$) or hash join. As table sizes increase into millions of rows, relational query performance degrades.

In Neo4j, each node physically stores direct memory pointers (relationship records) to adjacent nodes. Traversing from `Guest` to `Hotel` is $O(k)$ where $k$ is the degree of the node, completely independent of total graph size $N$.

### 6.2 Reservation Overlap Detection
Overlap verification is formulated as a graph pattern check:
```cypher
MATCH (res:Reservation)-[:BOOKS]->(r:Room {room_no: $room_no})
WHERE res.status = 'Confirmed'
  AND NOT (res.check_out_date <= $check_in_date OR res.check_in_date >= $check_out_date)
RETURN count(res) AS conflicts
```

### 6.3 Guest-to-Guest Collaborative Recommendation
Finding recommendations based on traveler similarity utilizes a 6-hop bidirectional path:
$$(g_1:\text{Guest}) \to (\text{MADE}) \to (r_1:\text{Reservation}) \to (\text{BOOKS}) \to (rm:\text{Room}) \leftarrow (\text{BOOKS}) \leftarrow (r_2) \leftarrow (\text{MADE}) \leftarrow (g_2:\text{Guest})$$
This traversal identifies guests who stayed in the same rooms or have similar profiles, surfacing hotels they enjoyed that $g_1$ has not yet visited. In SQL, this pattern requires self-joins across millions of rows; in Cypher, it executes in single-digit milliseconds.
