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
        """Creates a booking + its (unpaid) invoice. Used by tests / admin tools."""
        try:
            booking_id = db.sp_create_booking(customer_id, int(room_id), check_in_str, check_out_str, int(no_of_guests))
            # Auto-generate initial invoice (Payment_Status = PENDING until paid)
            db.sp_generate_invoice(booking_id)
            return True, booking_id
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_full_booking(customer_id, room_id, check_in_str, check_out_str, no_of_guests,
                            services=None, payment_mode="CREDIT_CARD"):
        """
        Booking + services + invoice + payment in ONE database transaction.
        If anything fails, nothing is saved.
        """
        try:
            service_lines = []
            for srv in services or []:
                srv_id = srv.get("service_id") if isinstance(srv, dict) else srv
                qty = srv.get("quantity", 1) if isinstance(srv, dict) else 1
                service_lines.append((int(srv_id), int(qty)))

            booking_id = db.create_full_booking(
                customer_id=int(customer_id),
                room_id=int(room_id),
                check_in_str=check_in_str,
                check_out_str=check_out_str,
                no_of_guests=int(no_of_guests),
                services=service_lines,
                payment_mode=BookingService._clean_payment_mode(payment_mode),
            )
            return True, booking_id
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _clean_payment_mode(payment_mode):
        modes = ('CREDIT_CARD', 'DEBIT_CARD', 'UPI', 'NET_BANKING', 'CASH')
        mode_clean = (payment_mode or '').upper()
        return mode_clean if mode_clean in modes else 'CREDIT_CARD'

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
        """Calls SP_ADD_BOOKING_SERVICE (inserts the line and regenerates the invoice atomically)."""
        try:
            db.sp_add_booking_service(int(booking_id), int(service_id), int(quantity))
            return True, "Service added successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def record_payment(booking_id, amount, payment_mode):
        """
        Calls SP_RECORD_PAYMENT. amount=None pays the full outstanding invoice balance.
        Invoice status becomes PAID / PARTIAL based on what was actually received.
        """
        try:
            amt = None if amount is None else float(amount)
            db.sp_record_payment(int(booking_id), BookingService._clean_payment_mode(payment_mode), amt)
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

            # A review tied to a booking must be for the reviewer's own, completed stay
            if bid is not None:
                owner = db.query(
                    "SELECT Customer_ID, Status FROM BOOKING WHERE Booking_ID = :bid",
                    {"bid": bid}
                )
                if not owner:
                    return False, "Booking not found."
                row = owner[0]
                owner_id = row.get("customer_id", row.get("Customer_ID"))
                status = row.get("status", row.get("Status"))
                if int(owner_id) != int(customer_id):
                    return False, "You can only review your own bookings."
                if status != "CHECKED_OUT":
                    return False, "You can review a stay after you have checked out."

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

            # ORA-00001 (Oracle) / UNIQUE constraint failed (SQLite) -> UQ_FEEDBACK_BOOKING
            if "ORA-00001" in error_message or "UNIQUE constraint failed" in error_message:
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
