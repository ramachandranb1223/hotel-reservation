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
       ├── Stored Procedures (SP_CREATE_BOOKING, SP_GENERATE_INVOICE, SP_CANCEL_BOOKING)
       ├── Stored Functions (FN_CALCULATE_BOOKING_AMOUNT, FN_IS_ROOM_AVAILABLE)
       ├── Triggers (TRG_CHECK_BOOKING_OVERLAP, TRG_SYNC_ROOM_STATUS)
       └── Transactions (COMMIT / ROLLBACK)
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
│   ├── 07_triggers.sql       # Integrity triggers (TRG_CHECK_BOOKING_OVERLAP, TRG_SYNC_ROOM_STATUS)
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
   - Explain how `SP_CREATE_BOOKING` executed inside Oracle Database.
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
2. **PL/SQL Stored Procedure Layer**: `SP_CREATE_BOOKING` performs this verification within an isolated transaction before issuing the `INSERT`.
3. **Trigger Layer**: `TRG_CHECK_BOOKING_OVERLAP` provides low-level database engine enforcement before any row insert or update.

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
- **SAVEPOINT**: Marks an intermediate checkpoint within a transaction allowing partial rollbacks if a sub-step fails. In our procedures, an `EXCEPTION WHEN OTHERS THEN ROLLBACK; RAISE;` block guarantees that if any step fails (e.g., during invoice generation or payment logging), the entire transaction rolls back to prevent inconsistent states.

### Q10: Why is Oracle Database and PL/SQL suitable for this project?
**Answer**: Oracle Database is the industry benchmark for enterprise-scale relational data management, providing strict ACID compliance, robust constraint enforcement, cost-based query optimization, and native support for PL/SQL. PL/SQL (Procedural Language/SQL) allows business logic to execute directly inside the database engine, reducing network round-trips, improving performance, and centralizing security rules.

### Q11: Why is Flask used for the backend?
**Answer**: Flask is a lightweight, WSGI-compliant Python web framework that provides routing, session management, and templating without forcing an unnecessary ORM. It allows direct, performant integration with Oracle Database via `python-oracledb` using parameterized SQL and native PL/SQL procedure execution.
