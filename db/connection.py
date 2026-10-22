import os
import sys
import re
import logging
import sqlite3
import threading
from datetime import datetime, date
from config import Config

logger = logging.getLogger("hotel_db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ORACLEDB_AVAILABLE = False

try:
    import oracledb

    # python-oracledb's default "thin mode" connects directly to Oracle Database
    # 12.1+ (including 19c/21c/23ai) in pure Python - no Oracle Client / Instant
    # Client install needed, so we deliberately do NOT call init_oracle_client()
    # here. Thick mode (which does need Instant Client) is only required for
    # older servers like Oracle 11g; if this project is ever pointed at an 11g
    # database, uncomment the two lines below and set lib_dir to your Instant
    # Client folder:
    #
    # oracledb.init_oracle_client(lib_dir=r"C:\path\to\instantclient")

    ORACLEDB_AVAILABLE = True

except ImportError:
    ORACLEDB_AVAILABLE = False
    print("Warning: python-oracledb is not installed. Fallback engine will be used.")

except Exception as e:
    ORACLEDB_AVAILABLE = False
    print(f"Warning: Oracle client could not be initialized: {e}")


class DatabaseManager:
    """
    Unified Database Manager.
    Primary Mode: Oracle Database 19c/21c/23ai/XE via python-oracledb.
    Secondary Mode: Autonomous local SQLite engine mirroring Oracle schema & PL/SQL procedures
                    so the website runs instantly even before Oracle service is started.
    """
    _instance = None
    _is_oracle = False
    _pool = None
    _sqlite_conn = None
    _sqlite_lock = threading.RLock()  # serialises write transactions on the shared SQLite connection

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        use_oracle = Config.USE_ORACLE_DB in ("oracle", "true", "1")
        auto_oracle = Config.USE_ORACLE_DB in ("auto", "")

        if (use_oracle or auto_oracle) and ORACLEDB_AVAILABLE:
            try:
                logger.info(f"Attempting connection to Oracle Database at {Config.ORACLE_DSN} as {Config.ORACLE_USER}...")
                # Try Oracle thin mode connection
                if Config.ORACLE_WALLET_DIR:
                    test_conn = oracledb.connect(
                        user=Config.ORACLE_USER,
                        password=Config.ORACLE_PASSWORD,
                        dsn=Config.ORACLE_DSN,
                        wallet_location=Config.ORACLE_WALLET_DIR,
                        wallet_password=Config.ORACLE_WALLET_PASSWORD
                    )
                else:
                    test_conn = oracledb.connect(
                        user=Config.ORACLE_USER,
                        password=Config.ORACLE_PASSWORD,
                        dsn=Config.ORACLE_DSN
                    )
                test_conn.close()
                self._is_oracle = True
                logger.info("Successfully connected to Oracle Database.")
            except Exception as e:
                logger.warning(f"Oracle connection unsuccessful: {e}")
                if use_oracle:
                    logger.error("USE_ORACLE_DB is explicitly required, raising error.")
                    raise
                logger.info("Operating in local development engine with identical Oracle schema & PL/SQL emulation.")
                self._init_sqlite_mirror()
        else:
            logger.info("Initializing local development database engine.")
            self._init_sqlite_mirror()

    def is_oracle_active(self):
        return self._is_oracle

    def get_oracle_connection(self):
        if Config.ORACLE_WALLET_DIR:
            return oracledb.connect(
                user=Config.ORACLE_USER,
                password=Config.ORACLE_PASSWORD,
                dsn=Config.ORACLE_DSN,
                wallet_location=Config.ORACLE_WALLET_DIR,
                wallet_password=Config.ORACLE_WALLET_PASSWORD
            )
        return oracledb.connect(
            user=Config.ORACLE_USER,
            password=Config.ORACLE_PASSWORD,
            dsn=Config.ORACLE_DSN
        )

    def _init_sqlite_mirror(self):
        """Initializes SQLite mirror with identical schema & seeded realistic sample data."""
        self._is_oracle = False
        db_path = os.path.join(os.path.dirname(__file__), "hotel_dev.db")
        self._sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        self._sqlite_conn.row_factory = sqlite3.Row
        self._sqlite_conn.execute("PRAGMA foreign_keys = ON")
        self._create_sqlite_schema()

    def _create_sqlite_schema(self):
        cur = self._sqlite_conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS CUSTOMER (
            Customer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Phone TEXT NOT NULL UNIQUE,
            Email TEXT NOT NULL UNIQUE,
            Password_Hash TEXT NOT NULL,
            Role TEXT DEFAULT 'CUSTOMER' NOT NULL CHECK (Role IN ('CUSTOMER', 'ADMIN')),
            Address TEXT,
            Date_Of_Birth TEXT,
            Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ROOM_TYPE (
            RoomType_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Type_Name TEXT NOT NULL UNIQUE,
            Description TEXT NOT NULL,
            Base_Price REAL NOT NULL CHECK (Base_Price >= 0),
            Max_Occupancy INTEGER DEFAULT 2 NOT NULL CHECK (Max_Occupancy > 0),
            Amenities TEXT,
            Image_URL TEXT
        );

        CREATE TABLE IF NOT EXISTS ROOM (
            Room_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Room_Number TEXT NOT NULL UNIQUE,
            Floor INTEGER NOT NULL,
            RoomType_ID INTEGER NOT NULL REFERENCES ROOM_TYPE(RoomType_ID) ON DELETE CASCADE,
            Price_Per_Night REAL NOT NULL CHECK (Price_Per_Night >= 0),
            Status TEXT DEFAULT 'AVAILABLE' NOT NULL CHECK (Status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE'))
        );

        CREATE TABLE IF NOT EXISTS BOOKING (
            Booking_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Customer_ID INTEGER NOT NULL REFERENCES CUSTOMER(Customer_ID),
            Room_ID INTEGER NOT NULL REFERENCES ROOM(Room_ID),
            Booking_Date TEXT DEFAULT CURRENT_DATE NOT NULL,
            No_Of_Guests INTEGER DEFAULT 1 NOT NULL CHECK (No_Of_Guests > 0),
            Check_In_Date TEXT NOT NULL,
            Check_Out_Date TEXT NOT NULL,
            Total_Amount REAL DEFAULT 0 NOT NULL CHECK (Total_Amount >= 0),
            Status TEXT DEFAULT 'CONFIRMED' NOT NULL CHECK (Status IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED')),
            CHECK (Check_Out_Date > Check_In_Date)
        );

        CREATE TABLE IF NOT EXISTS PAYMENT (
            Payment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Booking_ID INTEGER NOT NULL REFERENCES BOOKING(Booking_ID) ON DELETE CASCADE,
            Payment_Date TEXT DEFAULT CURRENT_DATE NOT NULL,
            Amount REAL NOT NULL CHECK (Amount >= 0),
            Payment_Mode TEXT NOT NULL CHECK (Payment_Mode IN ('CREDIT_CARD', 'DEBIT_CARD', 'UPI', 'NET_BANKING', 'CASH')),
            Status TEXT DEFAULT 'COMPLETED' NOT NULL CHECK (Status IN ('COMPLETED', 'PENDING', 'FAILED', 'REFUNDED'))
        );

        CREATE TABLE IF NOT EXISTS INVOICE (
            Invoice_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Booking_ID INTEGER NOT NULL UNIQUE REFERENCES BOOKING(Booking_ID) ON DELETE CASCADE,
            Invoice_Date TEXT DEFAULT CURRENT_DATE NOT NULL,
            Room_Charge REAL NOT NULL CHECK (Room_Charge >= 0),
            Service_Charge REAL DEFAULT 0 NOT NULL CHECK (Service_Charge >= 0),
            Tax_Amount REAL DEFAULT 0 NOT NULL CHECK (Tax_Amount >= 0),
            Total_Amount REAL NOT NULL CHECK (Total_Amount >= 0),
            Payment_Status TEXT DEFAULT 'PENDING' NOT NULL CHECK (Payment_Status IN ('PAID', 'PENDING', 'PARTIAL'))
        );

        CREATE TABLE IF NOT EXISTS SERVICE (
            Service_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Service_Name TEXT NOT NULL UNIQUE,
            Category TEXT NOT NULL,
            Price REAL NOT NULL CHECK (Price >= 0)
        );

        CREATE TABLE IF NOT EXISTS BOOKING_SERVICE (
            BookingService_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Booking_ID INTEGER NOT NULL REFERENCES BOOKING(Booking_ID) ON DELETE CASCADE,
            Service_ID INTEGER NOT NULL REFERENCES SERVICE(Service_ID),
            Quantity INTEGER DEFAULT 1 NOT NULL CHECK (Quantity > 0),
            Service_Amount REAL NOT NULL CHECK (Service_Amount >= 0),
            Service_Date TEXT DEFAULT CURRENT_DATE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS EMPLOYEE (
            Employee_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Designation TEXT NOT NULL,
            Phone TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Salary REAL NOT NULL CHECK (Salary >= 0),
            Hire_Date TEXT DEFAULT CURRENT_DATE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS FEEDBACK (
            Feedback_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Customer_ID INTEGER NOT NULL REFERENCES CUSTOMER(Customer_ID),
            Booking_ID INTEGER REFERENCES BOOKING(Booking_ID) ON DELETE SET NULL,
            Feedback_Date TEXT DEFAULT CURRENT_DATE NOT NULL,
            Rating INTEGER NOT NULL CHECK (Rating BETWEEN 1 AND 5),
            Comments TEXT
        );

        CREATE VIEW IF NOT EXISTS VW_AVAILABLE_ROOMS AS
        SELECT 
            r.Room_ID, r.Room_Number, r.Floor, r.Price_Per_Night, r.Status AS Room_Status,
            rt.RoomType_ID, rt.Type_Name, rt.Description AS RoomType_Description,
            rt.Base_Price, rt.Max_Occupancy, rt.Amenities, rt.Image_URL
        FROM ROOM r
        INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID;
        """)
        self._sqlite_conn.commit()

        # One review per booking (mirrors UQ_FEEDBACK_BOOKING in Oracle; NULLs allowed).
        # Created separately so an older dev DB that already has duplicate reviews still starts.
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS UQ_FEEDBACK_BOOKING ON FEEDBACK (Booking_ID)")
            self._sqlite_conn.commit()
        except sqlite3.IntegrityError:
            logger.warning("Existing dev DB has duplicate reviews per booking; delete db/hotel_dev.db to rebuild it.")

        # Seed data if empty
        row = cur.execute("SELECT COUNT(*) AS c FROM CUSTOMER").fetchone()
        if row["c"] == 0:
            self._seed_sqlite_data()

    def _seed_sqlite_data(self):
        cur = self._sqlite_conn.cursor()
        # Insert admin & customers
        admin_hash = "scrypt:32768:8:1$IgOTtmTfEOdrrsm5$adad85a5256f9e7e04433b250713dfa9e279eb917a85ff7036d395b30e6a07f3b77352357bcf19c27266f09d712389109a81400dba34fed5d4dc9fff2db0bea6"
        cust_hash = "scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454"
        
        customers = [
            ("Grand Luxe Admin", "+1-555-0100", "admin@grandluxe.com", admin_hash, "ADMIN", "Grand Luxe Tower, Penthouse Level, NY", "1985-05-15"),
            ("Alice Montgomery", "+1-555-0101", "alice@example.com", cust_hash, "CUSTOMER", "742 Evergreen Terrace, Springfield, OR", "1992-04-12"),
            ("Brian O'Connor", "+1-555-0102", "brian@example.com", cust_hash, "CUSTOMER", "1327 Ocean Drive, Miami Beach, FL", "1988-11-23"),
            ("Catherine Zhao", "+1-555-0103", "catherine@example.com", cust_hash, "CUSTOMER", "88 Financial Plaza, San Francisco, CA", "1995-02-18"),
            ("David Miller", "+1-555-0104", "david@example.com", cust_hash, "CUSTOMER", "452 Michigan Ave, Chicago, IL", "1983-09-05"),
            ("Elena Rostova", "+1-555-0105", "elena@example.com", cust_hash, "CUSTOMER", "19 Kensington Palace Gardens, London, UK", "1990-07-30"),
            ("Franklin Harris", "+1-555-0106", "franklin@example.com", cust_hash, "CUSTOMER", "302 Beacon St, Boston, MA", "1979-12-14"),
            ("Grace Hopper", "+1-555-0107", "grace@example.com", cust_hash, "CUSTOMER", "512 Arlington Rd, Arlington, VA", "1991-03-22"),
            ("Hassan Al-Mansoor", "+1-555-0108", "hassan@example.com", cust_hash, "CUSTOMER", "Sheikh Zayed Rd, Dubai, UAE", "1987-08-19"),
            ("Isabella Rossi", "+1-555-0109", "isabella@example.com", cust_hash, "CUSTOMER", "Via del Corso 44, Rome, Italy", "1994-10-09"),
            ("James Wilson", "+1-555-0110", "james@example.com", cust_hash, "CUSTOMER", "601 Congress Ave, Austin, TX", "1986-06-11"),
            ("Kavita Sharma", "+1-555-0111", "kavita@example.com", cust_hash, "CUSTOMER", "14 Marine Drive, Mumbai, India", "1993-01-25")
        ]
        cur.executemany("INSERT INTO CUSTOMER (Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth) VALUES (?, ?, ?, ?, ?, ?, ?)", customers)

        room_types = [
            ("Deluxe Suite", "Spacious luxury suite with king-size bed, private marble balcony, rain shower, and skyline city views.", 250.00, 2, "King Bed, Balcony, Wi-Fi 6, Smart TV, Mini Bar, Espresso Maker", "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"),
            ("Executive Business Room", "Designed for high-productivity business travelers with ergonomic executive desk, printer, and quiet acoustic insulation.", 320.00, 2, "Ergonomic Desk, High-Speed LAN, Conference Access, King Bed, Lounge Access", "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"),
            ("Presidential Ocean Suite", "Opulent top-floor oceanfront suite with wraparound terrace, private whirlpool jacuzzi, and dedicated butler service.", 650.00, 4, "Panoramic Ocean View, Jacuzzi, Butler Service, Dining Room, 2 King Beds, Wine Cellar", "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"),
            ("Royal Garden Villa", "Private detached garden bungalow featuring a personal heated plunge pool, lush tropical surroundings, and sun deck.", 520.00, 3, "Private Plunge Pool, Garden Patio, Outdoor Shower, King Bed + Daybed, Butler", "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80"),
            ("Classic Heritage Room", "Timeless elegance crafted with handcrafted walnut wood, plush bedding, and artisanal amenities for a cozy retreat.", 180.00, 2, "Queen Bed, Rain Shower, Wi-Fi, Coffee Station, 55-inch OLED TV", "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80")
        ]
        cur.executemany("INSERT INTO ROOM_TYPE (Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL) VALUES (?, ?, ?, ?, ?, ?)", room_types)

        rooms = [
            ("101", 1, 5, 180.00, "AVAILABLE"), ("102", 1, 5, 180.00, "AVAILABLE"), ("103", 1, 5, 190.00, "AVAILABLE"),
            ("104", 1, 1, 250.00, "AVAILABLE"), ("105", 1, 1, 250.00, "AVAILABLE"), ("201", 2, 1, 260.00, "AVAILABLE"),
            ("202", 2, 1, 260.00, "AVAILABLE"), ("203", 2, 2, 320.00, "AVAILABLE"), ("204", 2, 2, 320.00, "OCCUPIED"),
            ("205", 2, 2, 330.00, "AVAILABLE"), ("301", 3, 2, 330.00, "AVAILABLE"), ("302", 3, 4, 520.00, "OCCUPIED"),
            ("303", 3, 4, 520.00, "AVAILABLE"), ("304", 3, 4, 540.00, "AVAILABLE"), ("305", 3, 4, 540.00, "MAINTENANCE"),
            ("401", 4, 3, 650.00, "OCCUPIED"), ("402", 4, 3, 650.00, "AVAILABLE"), ("403", 4, 3, 680.00, "AVAILABLE"),
            ("404", 4, 3, 680.00, "AVAILABLE"), ("405", 4, 3, 700.00, "AVAILABLE")
        ]
        cur.executemany("INSERT INTO ROOM (Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (?, ?, ?, ?, ?)", rooms)

        services = [
            ("Airport VIP Limousine Transfer", "TRANSPORT", 85.00),
            ("Aromatherapy Full Body Spa (60 min)", "SPA", 120.00),
            ("Champagne Candlelight Beach Dinner", "DINING", 175.00),
            ("Artisanal Champagne & Caviar Breakfast", "DINING", 45.00),
            ("Executive Valet Laundry & Dry Cleaning", "LAUNDRY", 35.00),
            ("Private Sunset Catamaran Yacht Tour", "EXPERIENCE", 220.00),
            ("In-Room Wellness Yoga & Meditation Session", "WELLNESS", 60.00),
            ("Ultra High-Speed Dedicated VPN Router", "BUSINESS", 25.00)
        ]
        cur.executemany("INSERT INTO SERVICE (Service_Name, Category, Price) VALUES (?, ?, ?)", services)

        employees = [
            ("Arthur Pendelton", "General Manager", "+1-555-0201", "gm@grandluxe.com", 9500.00, "2021-03-01"),
            ("Seraphina Laurent", "Head Concierge", "+1-555-0202", "concierge@grandluxe.com", 6200.00, "2022-01-15"),
            ("Marcus Sterling", "Executive Chef", "+1-555-0203", "chef@grandluxe.com", 7800.00, "2021-06-10"),
            ("Chloe Davenport", "Spa & Wellness Director", "+1-555-0204", "spa@grandluxe.com", 5400.00, "2023-02-20"),
            ("Vikram Malhotra", "Operations Lead", "+1-555-0205", "frontdesk@grandluxe.com", 4800.00, "2022-08-01"),
            ("Maria Santos", "Executive Housekeeper", "+1-555-0206", "housekeeping@grandluxe.com", 4200.00, "2022-11-05"),
            ("Jonathan Vance", "Chief Security Officer", "+1-555-0207", "security@grandluxe.com", 4900.00, "2023-04-12"),
            ("Nadia Petrova", "Guest Relations Specialist", "+1-555-0208", "guestrelations@grandluxe.com", 4100.00, "2024-01-10")
        ]
        cur.executemany("INSERT INTO EMPLOYEE (Name, Designation, Phone, Email, Salary, Hire_Date) VALUES (?, ?, ?, ?, ?, ?)", employees)

        bookings = [
            (2, 1, "2026-08-01", 2, "2026-08-10", "2026-08-13", 540.00, "CHECKED_OUT"),
            (3, 1, "2026-08-15", 1, "2026-08-20", "2026-08-23", 540.00, "CHECKED_OUT"),
            (4, 2, "2026-08-05", 2, "2026-08-12", "2026-08-15", 540.00, "CHECKED_OUT"),
            (5, 4, "2026-08-10", 2, "2026-08-18", "2026-08-22", 1000.00, "CHECKED_OUT"),
            (6, 6, "2026-08-12", 2, "2026-08-25", "2026-08-29", 1040.00, "CHECKED_OUT"),
            (7, 8, "2026-08-20", 1, "2026-08-28", "2026-08-31", 960.00, "CHECKED_OUT"),
            (8, 13, "2026-08-22", 3, "2026-09-01", "2026-09-04", 1560.00, "CHECKED_OUT"),
            (9, 17, "2026-08-25", 2, "2026-09-05", "2026-09-08", 1950.00, "CHECKED_OUT"),
            (10, 5, "2026-08-28", 2, "2026-09-10", "2026-09-14", 1000.00, "CANCELLED"),
            (2, 9, "2026-09-15", 2, "2026-09-18", "2026-09-22", 1280.00, "CHECKED_IN"),
            (4, 12, "2026-09-16", 2, "2026-09-19", "2026-09-23", 2080.00, "CHECKED_IN"),
            (6, 16, "2026-09-14", 3, "2026-09-17", "2026-09-21", 2600.00, "CHECKED_IN"),
            (7, 1, "2026-09-18", 2, "2026-09-25", "2026-09-28", 540.00, "CONFIRMED"),
            (8, 3, "2026-09-18", 1, "2026-09-26", "2026-09-30", 760.00, "CONFIRMED"),
            (11, 4, "2026-09-19", 2, "2026-10-01", "2026-10-05", 1000.00, "CONFIRMED"),
            (12, 6, "2026-09-19", 2, "2026-10-02", "2026-10-06", 1040.00, "CONFIRMED"),
            (3, 7, "2026-09-19", 2, "2026-10-04", "2026-10-08", 1040.00, "CONFIRMED"),
            (5, 11, "2026-09-20", 2, "2026-10-05", "2026-10-09", 1320.00, "CONFIRMED"),
            (9, 13, "2026-09-20", 3, "2026-10-10", "2026-10-14", 2080.00, "CONFIRMED"),
            (10, 18, "2026-09-20", 2, "2026-10-12", "2026-10-16", 2720.00, "CONFIRMED"),
            (11, 10, "2026-09-17", 1, "2026-10-15", "2026-10-18", 990.00, "CANCELLED")
        ]
        cur.executemany("INSERT INTO BOOKING (Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", bookings)

        # Invoices and Payments for Bookings
        for b_id in range(1, 21):
            if b_id in (9, 21):
                continue
            cur.execute("INSERT INTO PAYMENT (Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (?, '2026-09-18', 500.0, 'CREDIT_CARD', 'COMPLETED')", (b_id,))
            cur.execute("INSERT INTO INVOICE (Booking_ID, Invoice_Date, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status) VALUES (?, '2026-09-18', 500.0, 0.0, 60.0, 560.0, 'PAID')", (b_id,))

        feedbacks = [
            (2, 1, 5, "Exceptional experience! The limousine transfer and breakfast on the balcony made our anniversary unforgettable."),
            (3, 2, 5, "Impeccable cleanliness and courteous concierge team. The room acoustics were phenomenal for remote meetings."),
            (4, 3, 4, "Very comfortable bed and smooth check-in process. Room service breakfast was warm and delicious."),
            (5, 4, 5, "The full body aromatherapy spa was world class. One of the best luxury hotel experiences I have ever had."),
            (6, 5, 5, "The beach dinner was magical! Chef Marcus personally checked on our dietary preferences. 10/10 recommendation."),
            (7, 6, 4, "Great business amenities. Ergonomic chair and fast Wi-Fi helped me close a crucial merger during my stay."),
            (8, 7, 5, "The private sunset yacht tour was the highlight of our vacation. Stunning villa and serene heated pool."),
            (9, 8, 5, "Presidential suite views are breathtaking. The dedicated butler service made us feel like royalty."),
            (10, None, 4, "Smooth cancellation process when my flights got rescheduled. Excellent customer care team."),
            (11, None, 5, "Grand Luxe sets the benchmark for modern hospitality. Can't wait for our next stay in October!")
        ]
        cur.executemany("INSERT INTO FEEDBACK (Customer_ID, Booking_ID, Rating, Comments) VALUES (?, ?, ?, ?)", feedbacks)
        self._sqlite_conn.commit()

    def query(self, sql, params=None):
        """Executes a SELECT query and returns a list of dictionaries."""
        params = params or {}
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    columns = [col[0].lower() for col in cur.description] if cur.description else []
                    rows = cur.fetchall()
                    result = []
                    for r in rows:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            val = r[i]
                            if isinstance(val, (datetime, date)):
                                val = val.strftime("%Y-%m-%d")
                            row_dict[col] = val
                        result.append(row_dict)
                    return result
            finally:
                conn.close()
        else:
            # SQLite query execution
            sqlite_sql = sql
            sqlite_params = {}
            for k, v in params.items():
                sqlite_params[k] = v
            # Replace Oracle-specific NVL with IFNULL
            sqlite_sql = sqlite_sql.replace("NVL(", "IFNULL(").replace("nvl(", "ifnull(")
            # Replace SYSDATE with CURRENT_DATE
            sqlite_sql = sqlite_sql.replace("SYSDATE", "CURRENT_DATE").replace("sysdate", "current_date")
            cur = self._sqlite_conn.cursor()
            cur.execute(sqlite_sql, sqlite_params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def execute(self, sql, params=None):
        """Executes an INSERT, UPDATE, or DELETE statement."""
        params = params or {}
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        else:
            sqlite_sql = sql.replace("NVL(", "IFNULL(").replace("SYSDATE", "CURRENT_DATE")
            cur = self._sqlite_conn.cursor()
            cur.execute(sqlite_sql, params)
            self._sqlite_conn.commit()
            return cur.lastrowid

    # -------------------------------------------------------------------------
    # PL/SQL PROCEDURES & FUNCTIONS EXECUTION INTERFACE
    # -------------------------------------------------------------------------
    def sp_create_booking(self, customer_id, room_id, check_in_str, check_out_str, no_of_guests):
        """
        Executes SP_CREATE_BOOKING on its own and commits.
        Validates dates, locks the room, checks overlap, inserts booking.
        """
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    booking_id = self._ora_create_booking(cur, customer_id, room_id, check_in_str, check_out_str, no_of_guests)
                conn.commit()
                return booking_id
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            with self._sqlite_lock:
                try:
                    cur = self._sqlite_conn.cursor()
                    booking_id = self._sqlite_create_booking(cur, customer_id, room_id, check_in_str, check_out_str, no_of_guests)
                    self._sqlite_conn.commit()
                    return booking_id
                except Exception:
                    self._sqlite_conn.rollback()
                    raise

    def sp_generate_invoice(self, booking_id):
        """
        Executes SP_GENERATE_INVOICE on its own and commits.
        Calculates room charges, service charges, 12% tax and payment status.
        """
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    invoice_id = self._ora_generate_invoice(cur, booking_id)
                conn.commit()
                return invoice_id
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            with self._sqlite_lock:
                try:
                    cur = self._sqlite_conn.cursor()
                    invoice_id = self._sqlite_generate_invoice(cur, booking_id)
                    self._sqlite_conn.commit()
                    return invoice_id
                except Exception:
                    self._sqlite_conn.rollback()
                    raise

    def sp_add_booking_service(self, booking_id, service_id, quantity):
        """Executes SP_ADD_BOOKING_SERVICE on its own and commits. Returns the line subtotal."""
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    subtotal = self._ora_add_booking_service(cur, booking_id, service_id, quantity)
                conn.commit()
                return subtotal
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            with self._sqlite_lock:
                try:
                    cur = self._sqlite_conn.cursor()
                    subtotal = self._sqlite_add_booking_service(cur, booking_id, service_id, quantity)
                    self._sqlite_conn.commit()
                    return subtotal
                except Exception:
                    self._sqlite_conn.rollback()
                    raise

    def sp_record_payment(self, booking_id, payment_mode, amount=None):
        """
        Executes SP_RECORD_PAYMENT on its own and commits.
        amount=None charges the full outstanding invoice balance.
        """
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    payment_id = self._ora_record_payment(cur, booking_id, payment_mode, amount)
                conn.commit()
                return payment_id
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            with self._sqlite_lock:
                try:
                    cur = self._sqlite_conn.cursor()
                    payment_id = self._sqlite_record_payment(cur, booking_id, payment_mode, amount)
                    self._sqlite_conn.commit()
                    return payment_id
                except Exception:
                    self._sqlite_conn.rollback()
                    raise

    def create_full_booking(self, customer_id, room_id, check_in_str, check_out_str,
                            no_of_guests, services, payment_mode):
        """
        ONE atomic transaction for a complete reservation:
            SP_CREATE_BOOKING -> SP_ADD_BOOKING_SERVICE (xN) -> SP_GENERATE_INVOICE -> SP_RECORD_PAYMENT
        then a single COMMIT. If any step fails (bad service ID, overlap, payment
        error...), everything is rolled back and no half-finished booking remains.

        services: list of (service_id, quantity) tuples.
        """
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    booking_id = self._ora_create_booking(cur, customer_id, room_id, check_in_str, check_out_str, no_of_guests)
                    for service_id, qty in services:
                        self._ora_add_booking_service(cur, booking_id, service_id, qty)
                    self._ora_generate_invoice(cur, booking_id)
                    self._ora_record_payment(cur, booking_id, payment_mode, None)
                conn.commit()
                return booking_id
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            with self._sqlite_lock:
                try:
                    cur = self._sqlite_conn.cursor()
                    booking_id = self._sqlite_create_booking(cur, customer_id, room_id, check_in_str, check_out_str, no_of_guests)
                    for service_id, qty in services:
                        self._sqlite_add_booking_service(cur, booking_id, service_id, qty)
                    self._sqlite_generate_invoice(cur, booking_id)
                    self._sqlite_record_payment(cur, booking_id, payment_mode, None)
                    self._sqlite_conn.commit()
                    return booking_id
                except Exception:
                    self._sqlite_conn.rollback()
                    raise

    # -------------------------------------------------------------------------
    # Oracle step helpers: call the PL/SQL procedure on an existing cursor,
    # WITHOUT committing, so several steps can share one transaction.
    # -------------------------------------------------------------------------
    @staticmethod
    def _ora_create_booking(cur, customer_id, room_id, check_in_str, check_out_str, no_of_guests):
        dt_in = datetime.strptime(check_in_str, "%Y-%m-%d")
        dt_out = datetime.strptime(check_out_str, "%Y-%m-%d")
        out_booking_id = cur.var(oracledb.NUMBER)
        cur.callproc("SP_CREATE_BOOKING", [customer_id, room_id, dt_in, dt_out, no_of_guests, out_booking_id])
        return int(out_booking_id.getvalue())

    @staticmethod
    def _ora_generate_invoice(cur, booking_id):
        out_invoice_id = cur.var(oracledb.NUMBER)
        cur.callproc("SP_GENERATE_INVOICE", [booking_id, out_invoice_id])
        return int(out_invoice_id.getvalue())

    @staticmethod
    def _ora_add_booking_service(cur, booking_id, service_id, quantity):
        out_subtotal = cur.var(oracledb.NUMBER)
        cur.callproc("SP_ADD_BOOKING_SERVICE", [booking_id, service_id, quantity, out_subtotal])
        return float(out_subtotal.getvalue())

    @staticmethod
    def _ora_record_payment(cur, booking_id, payment_mode, amount):
        out_payment_id = cur.var(oracledb.NUMBER)
        cur.callproc("SP_RECORD_PAYMENT", [booking_id, payment_mode, amount, out_payment_id])
        return int(out_payment_id.getvalue())

    # -------------------------------------------------------------------------
    # SQLite mirror step helpers: same rules as the PL/SQL procedures, no commit.
    # -------------------------------------------------------------------------
    @staticmethod
    def _sqlite_create_booking(cur, customer_id, room_id, check_in_str, check_out_str, no_of_guests):
        dt_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        dt_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        today = date.today()

        if dt_out <= dt_in:
            raise ValueError("Check-out date must be strictly later than check-in date.")
        if dt_in < today:
            raise ValueError("Check-in date cannot be in the past.")
        if no_of_guests <= 0:
            raise ValueError("Number of guests must be at least 1.")

        room = cur.execute("SELECT r.Status, r.Price_Per_Night, rt.Max_Occupancy FROM ROOM r JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID WHERE r.Room_ID = ?", (room_id,)).fetchone()
        if not room:
            raise ValueError("Selected room does not exist in inventory.")
        if room["Status"] == "MAINTENANCE":
            raise ValueError("Selected room is currently undergoing maintenance.")
        if no_of_guests > room["Max_Occupancy"]:
            raise ValueError(f"Guest count exceeds maximum room occupancy of {room['Max_Occupancy']}.")

        overlap = cur.execute("""
            SELECT COUNT(*) as c FROM BOOKING
            WHERE Room_ID = ? AND Status IN ('CONFIRMED', 'CHECKED_IN')
              AND Check_In_Date < ? AND Check_Out_Date > ?
        """, (room_id, check_out_str, check_in_str)).fetchone()
        if overlap["c"] > 0:
            raise ValueError("Room is not available for the selected dates due to a conflicting reservation.")

        nights = (dt_out - dt_in).days
        total_amount = nights * room["Price_Per_Night"]

        cur.execute("""
            INSERT INTO BOOKING (Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
            VALUES (?, ?, CURRENT_DATE, ?, ?, ?, ?, 'CONFIRMED')
        """, (customer_id, room_id, no_of_guests, check_in_str, check_out_str, total_amount))
        return cur.lastrowid

    @staticmethod
    def _sqlite_generate_invoice(cur, booking_id):
        booking = cur.execute("SELECT Total_Amount FROM BOOKING WHERE Booking_ID = ?", (booking_id,)).fetchone()
        if not booking:
            raise ValueError(f"Booking ID {booking_id} not found.")
        room_charge = booking["Total_Amount"]

        srv = cur.execute("SELECT IFNULL(SUM(Service_Amount), 0) as s FROM BOOKING_SERVICE WHERE Booking_ID = ?", (booking_id,)).fetchone()
        service_charge = srv["s"]
        subtotal = room_charge + service_charge
        tax_amount = round(subtotal * 0.12, 2)
        total_amount = round(subtotal + tax_amount, 2)

        paid = cur.execute("SELECT IFNULL(SUM(Amount), 0) AS p FROM PAYMENT WHERE Booking_ID = ? AND Status = 'COMPLETED'", (booking_id,)).fetchone()["p"]
        if paid >= total_amount - 0.005:
            pay_status = "PAID"
        elif paid > 0:
            pay_status = "PARTIAL"
        else:
            pay_status = "PENDING"

        cur.execute("""
            INSERT INTO INVOICE (Booking_ID, Invoice_Date, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
            VALUES (?, CURRENT_DATE, ?, ?, ?, ?, ?)
            ON CONFLICT(Booking_ID) DO UPDATE SET
                Room_Charge = excluded.Room_Charge,
                Service_Charge = excluded.Service_Charge,
                Tax_Amount = excluded.Tax_Amount,
                Total_Amount = excluded.Total_Amount,
                Payment_Status = excluded.Payment_Status,
                Invoice_Date = CURRENT_DATE
        """, (booking_id, room_charge, service_charge, tax_amount, total_amount, pay_status))
        inv = cur.execute("SELECT Invoice_ID FROM INVOICE WHERE Booking_ID = ?", (booking_id,)).fetchone()
        return inv["Invoice_ID"]

    @classmethod
    def _sqlite_add_booking_service(cls, cur, booking_id, service_id, quantity):
        if quantity is None or quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        b = cur.execute("SELECT Status FROM BOOKING WHERE Booking_ID = ?", (booking_id,)).fetchone()
        if not b:
            raise ValueError("Booking not found.")
        if b["Status"] == "CANCELLED":
            raise ValueError("Cannot add services to a cancelled booking.")
        s = cur.execute("SELECT Price FROM SERVICE WHERE Service_ID = ?", (service_id,)).fetchone()
        if not s:
            raise ValueError("Service not found.")
        line_total = s["Price"] * quantity
        cur.execute("""
            INSERT INTO BOOKING_SERVICE (Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date)
            VALUES (?, ?, ?, ?, CURRENT_DATE)
        """, (booking_id, service_id, quantity, line_total))
        cls._sqlite_generate_invoice(cur, booking_id)
        return float(line_total)

    @classmethod
    def _sqlite_record_payment(cls, cur, booking_id, payment_mode, amount):
        b = cur.execute("SELECT Status FROM BOOKING WHERE Booking_ID = ?", (booking_id,)).fetchone()
        if not b:
            raise ValueError("Booking not found.")
        if b["Status"] == "CANCELLED":
            raise ValueError("Cannot take payment for a cancelled booking.")
        cls._sqlite_generate_invoice(cur, booking_id)
        total = cur.execute("SELECT Total_Amount FROM INVOICE WHERE Booking_ID = ?", (booking_id,)).fetchone()["Total_Amount"]
        paid = cur.execute("SELECT IFNULL(SUM(Amount), 0) AS p FROM PAYMENT WHERE Booking_ID = ? AND Status = 'COMPLETED'", (booking_id,)).fetchone()["p"]
        amt = round(total - paid, 2) if amount is None else float(amount)
        if amt <= 0:
            raise ValueError("Nothing to pay: invoice is already settled.")
        cur.execute("""
            INSERT INTO PAYMENT (Booking_ID, Payment_Date, Amount, Payment_Mode, Status)
            VALUES (?, CURRENT_DATE, ?, ?, 'COMPLETED')
        """, (booking_id, amt, payment_mode))
        payment_id = cur.lastrowid
        cls._sqlite_generate_invoice(cur, booking_id)
        return payment_id

    def sp_cancel_booking(self, booking_id, customer_id):
        """
        Executes SP_CANCEL_BOOKING:
        Marks booking status as CANCELLED (preserving audit trail) and frees up room.
        """
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    out_res = cur.var(oracledb.STRING)
                    cur.callproc("SP_CANCEL_BOOKING", [booking_id, customer_id, out_res])
                    conn.commit()
                    return str(out_res.getvalue())
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        else:
            cur = self._sqlite_conn.cursor()
            b = cur.execute("SELECT Customer_ID, Status, Room_ID FROM BOOKING WHERE Booking_ID = ?", (booking_id,)).fetchone()
            if not b:
                raise ValueError("Booking record not found.")
            if customer_id != 0 and b["Customer_ID"] != customer_id:
                raise ValueError("Unauthorized: You can only cancel your own bookings.")
            if b["Status"] == "CANCELLED":
                raise ValueError("This booking has already been cancelled.")
            if b["Status"] == "CHECKED_OUT":
                raise ValueError("Completed stays cannot be cancelled.")

            cur.execute("UPDATE BOOKING SET Status = 'CANCELLED' WHERE Booking_ID = ?", (booking_id,))
            cur.execute("UPDATE PAYMENT SET Status = 'REFUNDED' WHERE Booking_ID = ?", (booking_id,))
            cur.execute("UPDATE ROOM SET Status = 'AVAILABLE' WHERE Room_ID = ? AND Status = 'OCCUPIED'", (b["Room_ID"],))
            self._sqlite_conn.commit()
            return f"Booking #{booking_id} successfully cancelled."

    def fn_calculate_booking_amount(self, room_id, check_in_str, check_out_str, booking_id=None):
        """
        Executes FN_CALCULATE_BOOKING_AMOUNT.
        """
        if self._is_oracle:
            conn = self.get_oracle_connection()
            try:
                with conn.cursor() as cur:
                    dt_in = datetime.strptime(check_in_str, "%Y-%m-%d")
                    dt_out = datetime.strptime(check_out_str, "%Y-%m-%d")
                    amount = cur.callfunc("FN_CALCULATE_BOOKING_AMOUNT", oracledb.NUMBER, [room_id, dt_in, dt_out, booking_id])
                    return float(amount)
            finally:
                conn.close()
        else:
            dt_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            dt_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
            if dt_out <= dt_in:
                return 0.0
            nights = (dt_out - dt_in).days
            cur = self._sqlite_conn.cursor()
            r = cur.execute("SELECT Price_Per_Night FROM ROOM WHERE Room_ID = ?", (room_id,)).fetchone()
            if not r:
                return 0.0
            cost = nights * r["Price_Per_Night"]
            if booking_id:
                s = cur.execute("SELECT IFNULL(SUM(Service_Amount), 0) as s FROM BOOKING_SERVICE WHERE Booking_ID = ?", (booking_id,)).fetchone()
                cost += s["s"]
            return float(cost)

db = DatabaseManager()
