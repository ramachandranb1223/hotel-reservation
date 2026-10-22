# Smart Hotel Reservation and Booking Management System
**College Database Systems Mini-Project (DA2 Academic Specification)**

A complete, production-grade, 3-tier web application built with **HTML5/CSS3/Vanilla JavaScript**, **Python Flask**, and **Oracle Database (SQL & PL/SQL)**.

---

## 1. System Architecture

The application implements a classical, decoupled 3-tier architecture:

```
Browser (HTML5, CSS3, Vanilla JS)
       │
       ▼  HTTP / REST JSON
Flask Backend (Python 3, python-oracledb)
       │
       ▼  SQL / PL/SQL Stored Procedures & Triggers
Oracle Database (19c / 21c / 23ai / Express Edition XE)
       ├── Tables & Normalized Relational Constraints
       ├── Analytical Views
       ├── Stored Procedures (SP_CREATE_BOOKING, SP_ADD_BOOKING_SERVICE, SP_GENERATE_INVOICE, SP_RECORD_PAYMENT, SP_CANCEL_BOOKING)
       ├── Stored Functions (FN_CALCULATE_BOOKING_AMOUNT, FN_IS_ROOM_AVAILABLE)
       ├── Triggers (TRG_ENFORCE_DATE_INTEGRITY, TRG_SYNC_ROOM_STATUS, TRG_AUTO_UPDATE_INVOICE_STATUS)
       └── Transactions (SAVEPOINT / ROLLBACK TO / single COMMIT per reservation, SELECT ... FOR UPDATE row locks)
```

---

## 2. Project Directory Structure

```
hotel-reservation/
├── .env.example              # Environment variables template
├── .env                      # Local configuration (Oracle credentials & Flask settings)
├── requirements.txt          # Python dependencies (Flask, python-oracledb, python-dotenv)
├── config.py                 # Configuration loader
├── app.py                    # Flask application entry point with modular REST API
├── setup_db.py               # CLI runner to execute and verify all Oracle SQL scripts
├── README.md                 # Complete project documentation and Viva guide
├── db/                       # Chronological Oracle Database Scripts
│   ├── connection.py         # python-oracledb connection manager & local dev fallback
│   ├── 01_schema.sql         # 10 Normalized tables with identity columns & sequences
│   ├── 02_constraints.sql    # Primary keys, Foreign keys, B-tree indexes, & Checks
│   ├── 03_sample_data.sql    # Realistic sample dataset (12 cust, 5 room types, 20 rooms, 20+ bookings)
│   ├── 04_views.sql          # 5 Operational and analytical views
│   ├── 05_procedures.sql     # PL/SQL stored procedures (SP_CREATE_BOOKING, SP_GENERATE_INVOICE, etc.)
│   ├── 06_functions.sql      # PL/SQL functions (FN_CALCULATE_BOOKING_AMOUNT, etc.)
│   ├── 07_triggers.sql       # Triggers (TRG_ENFORCE_DATE_INTEGRITY, TRG_SYNC_ROOM_STATUS, TRG_AUTO_UPDATE_INVOICE_STATUS)
│   └── 08_queries.sql        # Joins, Aggregates, Group By, Having, Subqueries, & Reports
├── services/                 # Business logic and database callers
│   ├── auth_service.py       # Authentication, password hashing, and customer registration
│   ├── booking_service.py    # Interfacing with room availability and PL/SQL procedures
│   ├── admin_service.py      # Room CRUD, status updates, employee management
│   └── report_service.py     # Analytical KPI execution
├── utils/
│   └── validation.py         # Date range, phone, email, and guest count validation
├── static/
│   ├── css/
│   │   └── style.css         # Modern luxury hotel design system (Navy, Gold, Glassmorphism)
│   └── js/
│       ├── app.js            # Shared UI utilities, modals, toasts, API helper
│       ├── booking.js        # Dynamic room searching, live date calculations, and booking
│       └── admin.js          # Admin dashboard metrics, table management, and reports
├── templates/                # Responsive HTML5 Templates
│   ├── base.html             # Common navigation, footer, modal shells
│   ├── index.html            # Luxury landing page with hero, search, suites, and testimonials
│   ├── rooms.html            # Complete inventory room catalog with filters
│   ├── booking.html          # Direct reservation wizard with add-on services
│   ├── my-bookings.html      # Guest reservation history, cancellation, and reviews
│   ├── invoice.html          # Printable luxury guest folio with itemized tax breakdown
│   ├── login.html            # Sign-in portal with 1-click demo accounts
│   ├── register.html         # Guest registration form
│   ├── admin-dashboard.html  # Executive management dashboard
│   ├── admin-rooms.html      # Physical rooms inventory management
│   ├── admin-bookings.html   # Reservation lifecycle & check-in/out
│   ├── admin-customers.html  # Registered guests and spending totals
│   ├── admin-services.html   # Hotel ancillary services catalog
│   └── admin-reports.html    # Academic SQL/PLSQL analytical reports
└── tests/
    └── test_flow.py          # Automated integration test suite
```

---

## 3. Database Schema Overview (10 Core Tables)

1. **`CUSTOMER`**: Customer and administrator profiles (`Customer_ID`, `Name`, `Phone`, `Email`, `Password_Hash`, `Role`, `Address`, `Date_Of_Birth`, `Created_At`).
2. **`ROOM_TYPE`**: Room categories with base rates and occupancy (`RoomType_ID`, `Type_Name`, `Description`, `Base_Price`, `Max_Occupancy`, `Amenities`, `Image_URL`).
3. **`ROOM`**: Physical rooms across floors (`Room_ID`, `Room_Number`, `Floor`, `RoomType_ID`, `Price_Per_Night`, `Status`).
4. **`BOOKING`**: Reservation records (`Booking_ID`, `Customer_ID`, `Room_ID`, `Booking_Date`, `No_Of_Guests`, `Check_In_Date`, `Check_Out_Date`, `Total_Amount`, `Status`).
5. **`PAYMENT`**: Financial transactions (`Payment_ID`, `Booking_ID`, `Payment_Date`, `Amount`, `Payment_Mode`, `Status`).
6. **`INVOICE`**: Billing statements enforcing 1:1 with booking (`Invoice_ID`, `Booking_ID`, `Invoice_Date`, `Room_Charge`, `Service_Charge`, `Tax_Amount`, `Total_Amount`, `Payment_Status`).
7. **`SERVICE`**: Ancillary hospitality offerings (`Service_ID`, `Service_Name`, `Category`, `Price`).
8. **`BOOKING_SERVICE`**: Junction table resolving M:N relationship between bookings and services (`BookingService_ID`, `Booking_ID`, `Service_ID`, `Quantity`, `Service_Amount`, `Service_Date`).
9. **`EMPLOYEE`**: Hotel staff directory (`Employee_ID`, `Name`, `Designation`, `Phone`, `Email`, `Salary`, `Hire_Date`).
10. **`FEEDBACK`**: Guest reviews and ratings 1–5 (`Feedback_ID`, `Customer_ID`, `Booking_ID`, `Feedback_Date`, `Rating`, `Comments`).

---

## 4. Setup & Execution Instructions

### Step 1: Install Dependencies
Ensure Python 3.10+ is installed. Open terminal in the project directory:
```bash
python -m pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and set your Oracle Database XE or Enterprise credentials:
```ini
ORACLE_USER=hotel_admin
ORACLE_PASSWORD=hotel_password_123
ORACLE_DSN=localhost:1521/xe
USE_ORACLE_DB=auto
```
*(Note: When `USE_ORACLE_DB=auto`, the application connects directly to Oracle if available. If Oracle is temporarily offline during initial frontend preview, the system gracefully activates an identical local mirror engine so that testing and demonstrations run immediately!)*

### Step 3: Initialize Oracle Database (Optional / For Oracle Live)
To run all SQL scripts against your live Oracle database with one command:
```bash
python setup_db.py
```
Or open **Oracle SQL Developer**, connect as your database user, and run the scripts in `db/` in order (`01_schema.sql` through `07_triggers.sql`).

### Step 4: Run Automated Tests
Run the comprehensive integration test suite to verify booking calculations, overlap rejection, and transactions:
```bash
python -m unittest tests/test_flow.py
```

### Step 5: Start the Web Application
Start the Flask server:
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 5. Demo Accounts

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Administrator** | `admin@grandluxe.com` | `admin123` | Full access to Admin Portal, Rooms CRUD, Bookings, Reports |
| **Customer** | `alice@example.com` | `password123` | Room searching, reservations, invoice view, cancellations |

*(Both accounts are pre-configured with 1-click fill buttons on the `/login` page for convenience during project evaluations!)*

---

## 6. DA2 Demonstration Checklist

Follow this sequence during your project demonstration to examiner / professor:

1. **Homepage & High-Fidelity UI (`/`)**:
   - Show responsive luxury styling, hero banner, room category showcase, and verified customer testimonials.
2. **Room Search & Live Availability (`/rooms` or `/`)**:
   - Enter check-in and check-out dates.
   - Show that only non-conflicting rooms with adequate occupancy are displayed.
3. **Atomic Booking Creation (`/booking`)**:
   - Select an available room, add an ancillary service (e.g. Airport Limousine), and complete the reservation.
   - Explain that booking, services, invoice and payment were saved in **one transaction** (`SP_CREATE_BOOKING` → `SP_ADD_BOOKING_SERVICE` → `SP_GENERATE_INVOICE` → `SP_RECORD_PAYMENT`, then a single `COMMIT`). If any step fails, nothing is saved.
4. **Printable Tax Invoice / Folio (`/invoice/<id>`)**:
   - Show computerized invoice generated via `SP_GENERATE_INVOICE`, displaying itemized room rate, service charges, 12% GST tax, and total.
5. **Overlap Rejection (Double Booking Test)**:
   - Try booking the exact same room for overlapping dates.
   - Show the system rejecting the request with an error message.
6. **Guest Dashboard & Cancellation (`/my-bookings`)**:
   - Show booking history. Cancel an upcoming booking.
   - Point out that status changed to `CANCELLED` while preserving the historical audit trail in Oracle.
7. **Admin Portal & Executive KPIs (`/admin/dashboard`)**:
   - Log in as `admin@grandluxe.com`.
   - Show real-time counters: Total Inventory, Available Rooms, Occupied Rooms, Gross Revenue.
8. **Rooms & Bookings Management (`/admin/rooms`, `/admin/bookings`)**:
   - Show room CRUD operations and status transition (e.g., checking in a guest to occupy a room).
9. **Analytical Reports & SQL Showcase (`/admin/reports`)**:
   - Demonstrate pre-compiled Oracle views: `VW_MONTHLY_REVENUE_REPORT`, `VW_ROOM_OCCUPANCY_SUMMARY`, and `BOOKING_SERVICE` junction analytics.
10. **Open Oracle SQL Developer**:
    - Run representative queries from `db/08_queries.sql` to demonstrate joins, group by, having, and subqueries.

---

## 7. Viva Voce Defense Framework (Questions & Answers)

### Q1: What is the difference between DBMS and RDBMS?
**Answer**: A DBMS (Database Management System) manages data stored as files without enforcing relational links or ACID constraints across tables. An RDBMS (Relational DBMS, like Oracle) organizes data into tables (relations) with rows and columns, enforces primary and foreign key constraints to maintain referential integrity, supports mathematical set operations (joins, unions), and guarantees ACID (Atomicity, Consistency, Isolation, Durability) transaction compliance.

### Q2: Explain Primary Key vs. Foreign Key.
**Answer**:
- **Primary Key (PK)**: A column or set of columns that uniquely identifies every tuple in a relation. It automatically enforces `UNIQUE` and `NOT NULL` constraints (e.g., `Customer_ID` in `CUSTOMER`).
- **Foreign Key (FK)**: A column in one relation that references the primary key of another relation to enforce referential integrity (e.g., `Room_ID` in `BOOKING` references `Room_ID` in `ROOM`).

### Q3: What level of Normalization does this database achieve? Explain BCNF.
**Answer**: The database is normalized up to Boyce-Codd Normal Form (BCNF) / 3NF:
- **1NF**: All attributes are atomic; no repeating groups or comma-separated values.
- **2NF**: In 1NF and every non-key attribute is fully functionally dependent on the entire primary key (no partial dependencies).
- **3NF**: In 2NF and no non-key attribute is transitively dependent on the primary key.
- **BCNF**: For every functional dependency $X \rightarrow Y$, the determinant $X$ is a superkey. In our schema, room pricing is tied to physical rooms or room types, service charges are isolated in `SERVICE`, and the M:N relationship between bookings and services is resolved via the junction relation `BOOKING_SERVICE`.

### Q4: How do you prevent overlapping bookings (double booking) in this project?
**Answer**: Double booking is prevented at multiple defensive layers:
1. **Application / View Layer**: The availability query checks `NOT EXISTS (SELECT 1 FROM BOOKING WHERE Room_ID = :room_id AND Status IN ('CONFIRMED', 'CHECKED_IN') AND Check_In_Date < :requested_check_out AND Check_Out_Date > :requested_check_in)`.
2. **PL/SQL Stored Procedure Layer**: `SP_CREATE_BOOKING` first locks the chosen room with `SELECT ... FROM ROOM ... FOR UPDATE`, then runs the same overlap check, then inserts. The lock matters for **concurrency**: if two guests book the same room at the same moment, the second session waits on the lock until the first commits, and its overlap check then sees the first booking and rejects the second. Without the lock, both sessions could see "0 overlaps" and both insert (a race condition).
3. **Constraint / Trigger Layer**: `CHK_BOOKING_DATES` and `TRG_ENFORCE_DATE_INTEGRITY` guarantee a valid date range on every insert/update.

*Why not an overlap trigger?* A row-level trigger on `BOOKING` cannot query `BOOKING` itself (Oracle raises **ORA-04091: table is mutating**), and even a compound trigger would still need a lock to be safe under concurrency. Locking the parent `ROOM` row inside the procedure is the standard, simpler solution.

### Q5: What is the difference between a Stored Procedure and a Stored Function?
**Answer**:
- A **Procedure** (e.g., `SP_CREATE_BOOKING`, `SP_GENERATE_INVOICE`) performs actions or business operations, can have zero or multiple `IN`, `OUT`, and `IN OUT` parameters, and is invoked via `CALL` or `EXECUTE`.
- A **Function** (e.g., `FN_CALCULATE_BOOKING_AMOUNT`, `FN_IS_ROOM_AVAILABLE`) must return a single value via the `RETURN` statement, and can be used directly inside SQL expressions (e.g., `SELECT FN_CALCULATE_BOOKING_AMOUNT(...) FROM DUAL`).

### Q6: What is a Database Trigger and why is it used?
**Answer**: A trigger is a stored PL/SQL block that automatically executes (fires) in response to a specific event on a table, such as `BEFORE` or `AFTER` `INSERT`, `UPDATE`, or `DELETE`. In this project, `TRG_SYNC_ROOM_STATUS` automatically synchronizes the physical room status (`OCCUPIED` / `AVAILABLE`) whenever a guest's booking status changes, removing the burden from application code and ensuring consistency.

### Q7: What is a Cursor?
**Answer**: A cursor is a pointer to a private SQL memory area allocated by Oracle to process a multi-row query. It allows row-by-row retrieval and manipulation of query results. Oracle uses implicit cursors for single SQL statements, and explicit cursors (`CURSOR c IS SELECT...; OPEN; FETCH; CLOSE;`) for procedural multi-row handling.

### Q8: What is a View and why is it useful?
**Answer**: A view is a stored SQL query definition that acts as a virtual table. It contains no physical data of its own; instead, it dynamically fetches data from underlying base tables upon query execution. In this project, `VW_AVAILABLE_ROOMS` and `VW_MONTHLY_REVENUE_REPORT` simplify complex multi-table joins, enhance performance, and restrict direct exposure of base tables.

### Q9: Explain Transaction Control: COMMIT, ROLLBACK, and SAVEPOINT.
**Answer**:
- **COMMIT**: Permanently saves all database modifications made within the current transaction.
- **ROLLBACK**: Undoes all changes made during the current transaction back to the last commit or savepoint.
- **SAVEPOINT**: Marks an intermediate checkpoint within a transaction allowing partial rollbacks if a sub-step fails.

**How this project uses them:** the procedures do *not* commit on their own. Each one starts with `SAVEPOINT <name>` and its exception handler does `ROLLBACK TO <name>; RAISE;`, undoing only its own work and passing the error up. The **caller owns the transaction**: when a guest books, the application calls `SP_CREATE_BOOKING`, `SP_ADD_BOOKING_SERVICE` (once per add-on), `SP_GENERATE_INVOICE` and `SP_RECORD_PAYMENT` on one connection and issues a single `COMMIT` at the end, or a full `ROLLBACK` if any step fails. This is atomicity (the A in ACID): there is never a booking without its invoice, or a paid booking missing its services. (A procedure that commits internally would break this, because a later failure could no longer undo the earlier steps.)

When testing a procedure by hand in SQL Developer, run `COMMIT;` afterwards to keep the result.

### Q9b: How is the invoice payment status decided?
**Answer**: New invoices start as `PENDING`. `SP_GENERATE_INVOICE` sums the `COMPLETED` payments for the booking and sets `PAID` (paid ≥ total), `PARTIAL` (some paid) or `PENDING` (nothing paid). `SP_RECORD_PAYMENT` charges the outstanding balance (room + services + 12% tax) and then refreshes the status.

### Q10: Why is Oracle Database and PL/SQL suitable for this project?
**Answer**: Oracle Database is the industry benchmark for enterprise-scale relational data management, providing strict ACID compliance, robust constraint enforcement, cost-based query optimization, and native support for PL/SQL. PL/SQL (Procedural Language/SQL) allows business logic to execute directly inside the database engine, reducing network round-trips, improving performance, and centralizing security rules.

### Q11: Why is Flask used for the backend?
**Answer**: Flask is a lightweight, WSGI-compliant Python web framework that provides routing, session management, and templating without forcing an unnecessary ORM. It allows direct, performant integration with Oracle Database via `python-oracledb` using parameterized SQL and native PL/SQL procedure execution.

---

## 8. Extension: Vector Database (Chroma) — Semantic Search

This section covers the mini-project extension in the **Vector Database** category.

### 8.1 Why a second database at all?

Oracle is excellent at what it was chosen for: transactions, constraints, joins,
referential integrity. It is structurally incapable of one thing — judging whether two
pieces of text *mean* the same thing.

A guest complaining about noise might write "too loud", "thin walls", "could hear
everything next door", or "couldn't sleep". To Oracle these share almost no characters,
so `WHERE Comments LIKE '%noisy%'` matches none of them. There is no index, no clever
join, and no amount of PL/SQL that fixes this, because the information Oracle is missing
is *semantic*, not structural.

A vector database solves exactly this, and only this.

### 8.2 How it works

Each review is passed through a language model that converts it into an **embedding**:
a vector of 384 numbers positioned so that text with similar meaning sits close together
in that 384-dimensional space. Searching is then a geometry problem — find the vectors
nearest the query vector (approximate nearest-neighbour search, using cosine distance
here) — and it returns semantically related reviews even when they share no words at all
with the query.

### 8.3 Architecture — Oracle stays the system of record

```
      WRITE PATH                              READ PATH (semantic)
  ┌──────────────────┐                     ┌────────────────────────┐
  │  Flask + PL/SQL  │                     │  /api/semantic/reviews │
  └────────┬─────────┘                     └───────────┬────────────┘
           │ ACID transaction                          │ similarity query
           ▼                                           ▼
  ┌──────────────────┐   build_vector_index.py   ┌──────────────┐
  │  ORACLE 23ai     │ ────────────────────────► │   CHROMA     │
  │  system of record│      (derived index)      │ vector store │
  └──────────────────┘                           └──────────────┘
```

Chroma stores **no original data**. It is a derived index, rebuilt from Oracle on demand;
deleting `vector_store/` loses nothing. Every booking, payment and review is still written
to Oracle first, inside a transaction, protected by the constraints and triggers above.
This is the standard **polyglot persistence** pattern: each database does what it is
actually good at.

### 8.4 Setup

```bash
pip install chromadb          # one extra dependency
python setup_db.py            # Oracle first — it is the source of truth
python build_vector_index.py  # then build the derived vector index
```

The first index build downloads the embedding model (~80MB, one time). After that it
runs fully offline on the CPU — no API key, no cloud service.

Useful flags:
```bash
python build_vector_index.py --status   # what is currently indexed
python build_vector_index.py --demo     # rebuild, then run the comparison query
```

> **Python 3.14 note:** Chroma's default embedding model runs on `onnxruntime`, which may
> not yet publish wheels for very new Python releases. If `pip install chromadb` fails,
> run the project in a virtualenv on Python 3.12 or 3.13, or supply a different embedding
> function via `semantic_service.set_embedding_function()`.

### 8.5 Data model (vector-side schema design)

| Collection | Documents | Embedded text | Metadata (filterable) |
|---|---|---|---|
| `hotel_reviews` | one per `FEEDBACK` row with comments | the review text | `feedback_id`, `rating`, `customer_name`, `room_type` |
| `hotel_room_types` | one per `ROOM_TYPE` row | name + description + amenities | `roomtype_id`, `type_name`, `base_price`, `max_occupancy` |

Note the deliberate design choice: the **metadata mirrors the Oracle primary keys**
(`feedback_id`, `roomtype_id`), so any vector hit can be traced straight back to its
authoritative Oracle row.

### 8.6 Core operations and technology-specific queries

| Operation | Vector database | Relational equivalent |
|---|---|---|
| Insert | `collection.upsert(ids, documents, metadatas)` | `INSERT` |
| Similarity query | `collection.query(query_texts=[...], n_results=5)` | *no equivalent* |
| Filtered similarity | `query(..., where={"rating": {"$gte": 4}})` | `WHERE rating >= 4` |
| Count | `collection.count()` | `SELECT COUNT(*)` |
| Delete | `client.delete_collection(name)` | `DROP TABLE` |

The third row is the interesting one: it combines a similarity search with a structured
metadata filter in a single call — "find reviews that *mean* this, but only from guests
who rated 4 or above."

### 8.7 Demonstration

The search feature appears in two places, deliberately separated:

- **`/smart-search`** (public, "Find Your Stay") is the guest-facing feature. It uses the
  vector index but exposes none of the machinery: no scores, no index internals, no
  mention of Oracle, Chroma or embeddings. This is what a real guest would see.
- **`/admin/search-insights`** (staff only) is the internal comparison tool. It runs one
  query through both engines and shows them side by side: Oracle's `LIKE` on the left,
  the vector search on the right. **Log in as an administrator to reach it** — this is
  the page to use when demonstrating why the vector database was added.

The CLI also prints the same comparison without needing the browser:
`python build_vector_index.py --demo`

Suggested demo queries (chosen because no review contains these words literally, so SQL
returns zero rows while vector search still finds the right reviews):

| Query | SQL `LIKE` | Vector search finds |
|---|---|---|
| "somewhere peaceful to get work done" | 0 rows | the remote-meetings and business-amenities reviews |
| "was the food any good" | 0 rows | the breakfast and beach-dinner reviews |
| "romantic getaway" | 0 rows | the anniversary and sunset-yacht reviews |
| "easy to change my plans" | 0 rows | the cancellation review |

The page also has a room matcher: describe a stay in plain English ("a big quiet space
for a family with a view") and it ranks room categories by how well their description and
amenities match, without using any category names or filters.

### 8.8 Comparative analysis

| | Oracle (relational) | Chroma (vector) |
|---|---|---|
| Data model | tables, rows, typed columns | collections of embeddings + metadata |
| Query language | SQL — declarative, exact | nearest-neighbour by distance |
| Matching | exact / substring / range | similarity of meaning |
| Transactions | full ACID | none |
| Constraints | PK, FK, CHECK, triggers | none |
| Results | deterministic, complete | approximate, ranked, top-*k* |
| Best at | bookings, payments, invoices | free text: reviews, descriptions |
| Fails at | "find things that mean this" | anything needing correctness |

**Why this split is the right one:** a vector database has no transactions and no
constraints, so a booking must never live in it — a double-booking or a lost payment
would be unrecoverable. Equally, Oracle cannot rank free text by meaning no matter how
the query is written. Using one database for both jobs would mean accepting a serious
weakness in one half of the system. Keeping Oracle authoritative and Chroma derived means
each database is used only where it is genuinely the better tool, and the vector index
can be deleted and rebuilt at any time without risking a single booking.

### 8.9 Files added

| File | Purpose |
|---|---|
| `services/semantic_service.py` | Chroma client, indexing, similarity search, SQL baseline |
| `build_vector_index.py` | CLI builder — reads Oracle, embeds into Chroma |
| `templates/smart-search.html` | Side-by-side demo page |
| `/api/semantic/*` routes in `app.py` | status, review search, room matching, admin rebuild |

---

## 9. Security Model

The application was hardened before being considered production-shaped. The issues below
were found by review and each is now covered by an automated regression test.

### 9.1 Access control

| Resource | Rule |
|---|---|
| `/invoice/<id>`, `GET /api/bookings/<id>`, `GET /api/invoices/<id>` | Signed in **and** owns the booking, or is staff |
| `POST /api/payments`, `POST /api/bookings/<id>/services` | Same — these write financial records |
| `POST /api/bookings`, `POST /api/feedback` | Signed in; identity taken from the session |
| `/admin/*`, `/api/admin/*` | Administrator role required |
| `/api/semantic/*` (guest search) | Public, and returns no index internals |

Ownership is checked by a single helper, `_owns_booking_or_admin()`, so the rule is
defined once rather than repeated per route.

### 9.2 Issues fixed

1. **Any invoice was readable by anyone.** `/invoice/<id>` had no authentication at all —
   changing the number in the URL displayed another guest's name, email, phone and spend.
2. **Identity was accepted from the request body.** `POST /api/bookings` and
   `POST /api/feedback` read `customer_id` from JSON, so a caller could book (and bill)
   or post reviews as any other customer. Identity now comes from the session only.
3. **Payments required no login.** `POST /api/payments` was fully open.
4. **A password hash was accepted as a password.** `authenticate_user` fell back to
   `stored_hash == password`, so anyone holding the hash could sign in with it.
5. **Debug mode and a shared secret key were the defaults.** `FLASK_DEBUG` defaulted to
   `True` (Flask's debugger exposes an interactive console on error) alongside a
   hardcoded `SECRET_KEY` that would let anyone forge a session cookie, and the server
   bound to `0.0.0.0`. Defaults are now off, random, and localhost respectively.
6. **Demo credentials were printed on the login page.** The one-click fill buttons were
   removed; the accounts still exist and are listed in section 5 of this document.

### 9.3 Before deploying

Set these in `.env` — the defaults are safe but development-oriented:

```ini
SECRET_KEY=<a long random value, not the placeholder>
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True     # once served over HTTPS
USE_ORACLE_DB=oracle           # never silently fall back to SQLite in production
```

Also run the app behind a real WSGI server (gunicorn/waitress) rather than
`python app.py`, and give `hotel_admin` only the privileges it needs — `DBA` was granted
during setup for convenience, which is more than the application requires.
