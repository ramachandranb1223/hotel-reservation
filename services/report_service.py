from db.connection import db

class ReportService:
    @staticmethod
    def get_dashboard_summary():
        # Room KPI
        rooms = db.query("""
            SELECT 
                COUNT(*) AS total_rooms,
                SUM(CASE WHEN Status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_rooms,
                SUM(CASE WHEN Status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_rooms,
                SUM(CASE WHEN Status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_rooms
            FROM ROOM
        """)
        room_kpi = rooms[0] if rooms else {"total_rooms": 0, "available_rooms": 0, "occupied_rooms": 0, "maintenance_rooms": 0}

        # Booking KPI
        bookings = db.query("""
            SELECT 
                COUNT(*) AS total_bookings,
                SUM(CASE WHEN Status = 'CONFIRMED' THEN 1 ELSE 0 END) AS upcoming_bookings,
                SUM(CASE WHEN Status = 'CHECKED_IN' THEN 1 ELSE 0 END) AS active_stays,
                SUM(CASE WHEN Status = 'CHECKED_OUT' THEN 1 ELSE 0 END) AS completed_stays,
                SUM(CASE WHEN Status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_bookings,
                NVL(SUM(CASE WHEN Status != 'CANCELLED' THEN Total_Amount ELSE 0 END), 0) AS gross_booking_value
            FROM BOOKING
        """)
        bk_kpi = bookings[0] if bookings else {"total_bookings": 0, "upcoming_bookings": 0, "active_stays": 0, "completed_stays": 0, "cancelled_bookings": 0, "gross_booking_value": 0}

        # Payment KPI
        payments = db.query("SELECT NVL(SUM(Amount), 0) AS total_collected FROM PAYMENT WHERE Status = 'COMPLETED'")
        total_collected = payments[0]["total_collected"] if payments else 0

        # Customer Count
        customers = db.query("SELECT COUNT(*) AS total_customers FROM CUSTOMER WHERE Role = 'CUSTOMER'")
        total_cust = customers[0]["total_customers"] if customers else 0

        return {
            "rooms": room_kpi,
            "bookings": bk_kpi,
            "total_collected": total_collected,
            "total_customers": total_cust
        }

    @staticmethod
    def get_revenue_by_month():
        # Oracle stores DATE values, so the month must come from TO_CHAR(..., 'YYYY-MM').
        # (SUBSTR on an Oracle DATE converts it with the session NLS format, e.g.
        # '23-SEP-26', and would group by day-month instead of year-month.)
        # The SQLite mirror stores dates as 'YYYY-MM-DD' text, so SUBSTR works there.
        if db.is_oracle_active():
            month_expr = "TO_CHAR(b.Check_In_Date, 'YYYY-MM')"
        else:
            month_expr = "SUBSTR(b.Check_In_Date, 1, 7)"

        sql = f"""
            SELECT 
                {month_expr} AS Booking_Month,
                COUNT(b.Booking_ID) AS Total_Bookings,
                NVL(SUM(b.Total_Amount), 0) AS Gross_Revenue,
                NVL(SUM(p.Paid_Amount), 0) AS Collected_Amount
            FROM BOOKING b
            LEFT JOIN (
                -- Pre-aggregate so a booking with several payments is counted once
                SELECT Booking_ID, SUM(Amount) AS Paid_Amount
                FROM PAYMENT
                WHERE Status = 'COMPLETED'
                GROUP BY Booking_ID
            ) p ON b.Booking_ID = p.Booking_ID
            WHERE b.Status != 'CANCELLED'
            GROUP BY {month_expr}
            ORDER BY Booking_Month DESC
        """
        return db.query(sql)

    @staticmethod
    def get_most_booked_room_types():
        sql = """
            SELECT 
                rt.Type_Name,
                rt.Base_Price,
                COUNT(b.Booking_ID) AS Total_Bookings,
                NVL(SUM(b.Total_Amount), 0) AS Total_Revenue
            FROM ROOM_TYPE rt
            LEFT JOIN ROOM r ON rt.RoomType_ID = r.RoomType_ID
            LEFT JOIN BOOKING b ON r.Room_ID = b.Room_ID AND b.Status != 'CANCELLED'
            GROUP BY rt.Type_Name, rt.Base_Price
            ORDER BY Total_Bookings DESC, Total_Revenue DESC
        """
        return db.query(sql)

    @staticmethod
    def get_service_usage():
        sql = """
            SELECT 
                s.Service_Name,
                s.Category,
                s.Price AS Unit_Price,
                COUNT(bs.BookingService_ID) AS Times_Ordered,
                NVL(SUM(bs.Quantity), 0) AS Total_Units,
                NVL(SUM(bs.Service_Amount), 0) AS Revenue_Generated
            FROM SERVICE s
            LEFT JOIN BOOKING_SERVICE bs ON s.Service_ID = bs.Service_ID
            GROUP BY s.Service_Name, s.Category, s.Price
            ORDER BY Revenue_Generated DESC
        """
        return db.query(sql)

    @staticmethod
    def get_top_customers(limit=10):
        sql = """
            SELECT 
                c.Customer_ID,
                c.Name,
                c.Email,
                c.Phone,
                COUNT(b.Booking_ID) AS Total_Stays,
                NVL(SUM(b.Total_Amount), 0) AS Total_Spent
            FROM CUSTOMER c
            INNER JOIN BOOKING b ON c.Customer_ID = b.Customer_ID
            WHERE b.Status != 'CANCELLED'
            GROUP BY c.Customer_ID, c.Name, c.Email, c.Phone
            ORDER BY Total_Spent DESC
        """
        rows = db.query(sql)
        return rows[:limit]

    @staticmethod
    def get_room_occupancy_rates():
        sql = """
            SELECT 
                rt.Type_Name,
                COUNT(r.Room_ID) AS Total_Rooms,
                SUM(CASE WHEN r.Status = 'AVAILABLE' THEN 1 ELSE 0 END) AS Available,
                SUM(CASE WHEN r.Status = 'OCCUPIED' THEN 1 ELSE 0 END) AS Occupied,
                SUM(CASE WHEN r.Status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS Maintenance
            FROM ROOM_TYPE rt
            LEFT JOIN ROOM r ON rt.RoomType_ID = r.RoomType_ID
            GROUP BY rt.Type_Name
            ORDER BY rt.Type_Name ASC
        """
        return db.query(sql)
