from db.connection import db
from utils.validation import validate_booking_dates, validate_guest_count, validate_feedback

class BookingService:
    @staticmethod
    def get_room_types():
        sql = "SELECT RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL FROM ROOM_TYPE ORDER BY Base_Price ASC"
        return db.query(sql)

    @staticmethod
    def get_all_rooms(room_type_id=None, status=None, floor=None, max_price=None):
        sql = """
            SELECT 
                r.Room_ID, r.Room_Number, r.Floor, r.Price_Per_Night, r.Status,
                rt.RoomType_ID, rt.Type_Name, rt.Description, rt.Max_Occupancy, rt.Amenities, rt.Image_URL
            FROM ROOM r
            INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
            WHERE 1=1
        """
        params = {}
        if room_type_id:
            sql += " AND r.RoomType_ID = :rtid"
            params["rtid"] = int(room_type_id)
        if status:
            sql += " AND r.Status = :status"
            params["status"] = status.upper()
        if floor:
            sql += " AND r.Floor = :floor"
            params["floor"] = int(floor)
        if max_price:
            sql += " AND r.Price_Per_Night <= :max_price"
            params["max_price"] = float(max_price)

        sql += " ORDER BY r.Floor ASC, r.Room_Number ASC"
        return db.query(sql, params)

    @staticmethod
    def search_available_rooms(check_in_str, check_out_str, guests=1, room_type_id=None):
        ok, res = validate_booking_dates(check_in_str, check_out_str)
        if not ok:
            return False, res
        check_in, check_out, nights = res

        g_ok, guests_val = validate_guest_count(guests)
        if not g_ok:
            return False, guests_val

        # Overlap rejection logic:
        # A room is available IF:
        # 1. Room is not in MAINTENANCE
        # 2. Room max occupancy >= guests
        # 3. NOT EXISTS active booking with (Check_In_Date < p_check_out AND Check_Out_Date > p_check_in)
        if db.is_oracle_active():
            sql = """
                SELECT 
                    r.Room_ID, r.Room_Number, r.Floor, r.Price_Per_Night, r.Status,
                    rt.RoomType_ID, rt.Type_Name, rt.Description, rt.Max_Occupancy, rt.Amenities, rt.Image_URL,
                    (:nights * r.Price_Per_Night) AS Total_Estimated_Cost
                FROM ROOM r
                INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
                WHERE r.Status != 'MAINTENANCE'
                  AND rt.Max_Occupancy >= :guests
                  AND NOT EXISTS (
                      SELECT 1 FROM BOOKING b
                      WHERE b.Room_ID = r.Room_ID
                        AND b.Status IN ('CONFIRMED', 'CHECKED_IN')
                        AND b.Check_In_Date < TO_DATE(:check_out, 'YYYY-MM-DD')
                        AND b.Check_Out_Date > TO_DATE(:check_in, 'YYYY-MM-DD')
                  )
            """
            params = {
                "check_in": check_in_str,
                "check_out": check_out_str,
                "guests": guests_val,
                "nights": nights
            }
            if room_type_id:
                sql += " AND r.RoomType_ID = :rtid"
                params["rtid"] = int(room_type_id)
            sql += " ORDER BY rt.Base_Price ASC, r.Room_Number ASC"
            rooms = db.query(sql, params)
        else:
            sql = """
                SELECT 
                    r.Room_ID, r.Room_Number, r.Floor, r.Price_Per_Night, r.Status,
                    rt.RoomType_ID, rt.Type_Name, rt.Description, rt.Max_Occupancy, rt.Amenities, rt.Image_URL,
                    (:nights * r.Price_Per_Night) AS Total_Estimated_Cost
                FROM ROOM r
                INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
                WHERE r.Status != 'MAINTENANCE'
                  AND rt.Max_Occupancy >= :guests
                  AND NOT EXISTS (
                      SELECT 1 FROM BOOKING b
                      WHERE b.Room_ID = r.Room_ID
                        AND b.Status IN ('CONFIRMED', 'CHECKED_IN')
                        AND b.Check_In_Date < :check_out
                        AND b.Check_Out_Date > :check_in
                  )
            """
            params = {
                "check_in": check_in_str,
                "check_out": check_out_str,
                "guests": guests_val,
                "nights": nights
            }
            if room_type_id:
                sql += " AND r.RoomType_ID = :rtid"
                params["rtid"] = int(room_type_id)
            sql += " ORDER BY rt.Base_Price ASC, r.Room_Number ASC"
            rooms = db.query(sql, params)

        return True, {
            "check_in": check_in_str,
            "check_out": check_out_str,
            "nights": nights,
            "guests": guests_val,
            "rooms": rooms
        }

    @staticmethod
    def create_booking(customer_id, room_id, check_in_str, check_out_str, no_of_guests):
        try:
            booking_id = db.sp_create_booking(customer_id, int(room_id), check_in_str, check_out_str, int(no_of_guests))
            # Auto-generate initial invoice
            db.sp_generate_invoice(booking_id)
            return True, booking_id
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_booking_details(booking_id):
        sql = """
            SELECT 
                b.Booking_ID, b.Customer_ID, b.Room_ID, b.Booking_Date, b.No_Of_Guests,
                b.Check_In_Date, b.Check_Out_Date, b.Total_Amount, b.Status AS Booking_Status,
                c.Name AS Customer_Name, c.Email AS Customer_Email, c.Phone AS Customer_Phone,
                r.Room_Number, r.Floor, r.Price_Per_Night,
                rt.Type_Name AS Room_Type, rt.Description, rt.Amenities, rt.Image_URL
            FROM BOOKING b
            INNER JOIN CUSTOMER c ON b.Customer_ID = c.Customer_ID
            INNER JOIN ROOM r ON b.Room_ID = r.Room_ID
            INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
            WHERE b.Booking_ID = :bid
        """
        rows = db.query(sql, {"bid": int(booking_id)})
        if not rows:
            return None
        
        booking = rows[0]
        # Attach services
        srv_sql = """
            SELECT bs.BookingService_ID, bs.Service_ID, s.Service_Name, s.Category, s.Price, bs.Quantity, bs.Service_Amount
            FROM BOOKING_SERVICE bs
            INNER JOIN SERVICE s ON bs.Service_ID = s.Service_ID
            WHERE bs.Booking_ID = :bid
        """
        booking["services"] = db.query(srv_sql, {"bid": int(booking_id)})

        # Attach invoice
        inv_sql = """
            SELECT Invoice_ID, Invoice_Date, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status
            FROM INVOICE WHERE Booking_ID = :bid
        """
        inv_rows = db.query(inv_sql, {"bid": int(booking_id)})
        booking["invoice"] = inv_rows[0] if inv_rows else None

        # Attach payments
        pay_sql = """
            SELECT Payment_ID, Payment_Date, Amount, Payment_Mode, Status
            FROM PAYMENT WHERE Booking_ID = :bid
        """
        booking["payments"] = db.query(pay_sql, {"bid": int(booking_id)})
        return booking

    @staticmethod
    def get_customer_bookings(customer_id):
        sql = """
            SELECT 
                b.Booking_ID,
                b.Room_ID,
                b.Booking_Date,
                b.No_Of_Guests,
                b.Check_In_Date,
                b.Check_Out_Date,
                b.Total_Amount,
                b.Status AS Booking_Status,

            r.Room_Number,
            rt.Type_Name AS Room_Type,
            rt.Image_URL,

            i.Invoice_ID,
            i.Total_Amount AS Invoice_Total,
            i.Payment_Status,

            f.Feedback_ID,
            f.Rating AS Feedback_Rating,
            f.Comments AS Feedback_Comments,
            f.Feedback_Date

        FROM BOOKING b

        INNER JOIN ROOM r
            ON b.Room_ID = r.Room_ID

        INNER JOIN ROOM_TYPE rt
            ON r.RoomType_ID = rt.RoomType_ID

        LEFT JOIN INVOICE i
            ON b.Booking_ID = i.Booking_ID

        LEFT JOIN FEEDBACK f
            ON b.Booking_ID = f.Booking_ID
            AND f.Customer_ID = b.Customer_ID

        WHERE b.Customer_ID = :cid

        ORDER BY b.Booking_ID DESC
    """

        return db.query(sql, {"cid": int(customer_id)}) 

    @staticmethod
    def cancel_booking(booking_id, customer_id):
        try:
            res = db.sp_cancel_booking(int(booking_id), int(customer_id))
            return True, res
        except Exception as e:
            return False, str(e)

    @staticmethod
    def add_booking_service(booking_id, service_id, quantity=1):
        try:
            # Check price
            srv = db.query("SELECT Price FROM SERVICE WHERE Service_ID = :sid", {"sid": int(service_id)})
            if not srv:
                return False, "Service not found."
            unit_price = srv[0]["price"] if "price" in srv[0] else srv[0]["Price"]
            line_total = float(unit_price) * int(quantity)

            # Insert or call procedure
            if db.is_oracle_active():
                sql = """
                    INSERT INTO BOOKING_SERVICE (Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date)
                    VALUES (:bid, :sid, :qty, :amt, SYSDATE)
                """
                db.execute(sql, {"bid": int(booking_id), "sid": int(service_id), "qty": int(quantity), "amt": line_total})
            else:
                db.execute("""
                    INSERT INTO BOOKING_SERVICE (Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date)
                    VALUES (:bid, :sid, :qty, :amt, CURRENT_DATE)
                """, {"bid": int(booking_id), "sid": int(service_id), "qty": int(quantity), "amt": line_total})

            # Regenerate invoice
            db.sp_generate_invoice(int(booking_id))
            return True, "Service added successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def record_payment(booking_id, amount, payment_mode):
        try:
            modes = ('CREDIT_CARD', 'DEBIT_CARD', 'UPI', 'NET_BANKING', 'CASH')
            mode_clean = payment_mode.upper()
            if mode_clean not in modes:
                mode_clean = 'CREDIT_CARD'

            if db.is_oracle_active():
                sql = """
                    INSERT INTO PAYMENT (Booking_ID, Payment_Date, Amount, Payment_Mode, Status)
                    VALUES (:bid, SYSDATE, :amt, :mode, 'COMPLETED')
                """
                db.execute(sql, {"bid": int(booking_id), "amt": float(amount), "mode": mode_clean})
            else:
                db.execute("""
                    INSERT INTO PAYMENT (Booking_ID, Payment_Date, Amount, Payment_Mode, Status)
                    VALUES (:bid, CURRENT_DATE, :amt, :mode, 'COMPLETED')
                """, {"bid": int(booking_id), "amt": float(amount), "mode": mode_clean})

            # Update Invoice to PAID
            db.sp_generate_invoice(int(booking_id))
            return True, "Payment recorded successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_services():
        return db.query("SELECT Service_ID, Service_Name, Category, Price FROM SERVICE ORDER BY Category ASC, Price ASC")

    @staticmethod
    def submit_feedback(customer_id, booking_id, rating, comments):
        ok, err = validate_feedback(rating, comments)

        if not ok:
            return False, err

        try:
            bid = int(booking_id) if booking_id else None

            if db.is_oracle_active():
                sql = """
                    INSERT INTO FEEDBACK
                        (Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
                    VALUES
                        (:cid, :bid, SYSDATE, :rating, :comments)
                """

                db.execute(
                    sql,
                    {
                        "cid": int(customer_id),
                        "bid": bid,
                        "rating": int(rating),
                        "comments": comments
                    }
                )

            else:
                db.execute(
                    """
                    INSERT INTO FEEDBACK
                        (Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
                    VALUES
                        (:cid, :bid, CURRENT_DATE, :rating, :comments)
                    """,
                    {
                        "cid": int(customer_id),
                        "bid": bid,
                        "rating": int(rating),
                        "comments": comments
                    }
                )

            return True, "Thank you for your valuable feedback!"

        except Exception as e:
            error_message = str(e)

            if "ORA-00001" in error_message:
                return False, "You have already submitted a review for this booking."

            return False, error_message

    @staticmethod
    def get_testimonials(limit=6):
        sql = """
            SELECT f.Feedback_ID, f.Rating, f.Comments, f.Feedback_Date, c.Name AS Customer_Name
            FROM FEEDBACK f
            INNER JOIN CUSTOMER c ON f.Customer_ID = c.Customer_ID
            WHERE f.Rating >= 4
            ORDER BY f.Feedback_ID DESC
        """
        rows = db.query(sql)
        return rows[:limit]
