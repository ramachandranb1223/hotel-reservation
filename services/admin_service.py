from db.connection import db

class AdminService:
    # -------------------------------------------------------------------------
    # ROOM TYPES CRUD
    # -------------------------------------------------------------------------
    @staticmethod
    def get_all_room_types():
        return db.query("SELECT RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL FROM ROOM_TYPE ORDER BY RoomType_ID ASC")

    @staticmethod
    def create_room_type(name, description, base_price, max_occupancy, amenities, image_url):
        if not name or float(base_price) < 0 or int(max_occupancy) <= 0:
            return False, "Invalid room type attributes."
        try:
            if db.is_oracle_active():
                sql = """
                    INSERT INTO ROOM_TYPE (Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
                    VALUES (:name, :descr, :price, :occ, :amen, :img)
                """
            else:
                sql = """
                    INSERT INTO ROOM_TYPE (Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
                    VALUES (:name, :descr, :price, :occ, :amen, :img)
                """
            db.execute(sql, {
                "name": name.strip(),
                "descr": description.strip(),
                "price": float(base_price),
                "occ": int(max_occupancy),
                "amen": amenities.strip(),
                "img": image_url.strip() if image_url else "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"
            })
            return True, "Room type created successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_room_type(rtid, name, description, base_price, max_occupancy, amenities, image_url):
        try:
            sql = """
                UPDATE ROOM_TYPE
                SET Type_Name = :name,
                    Description = :descr,
                    Base_Price = :price,
                    Max_Occupancy = :occ,
                    Amenities = :amen,
                    Image_URL = :img
                WHERE RoomType_ID = :rtid
            """
            db.execute(sql, {
                "rtid": int(rtid),
                "name": name.strip(),
                "descr": description.strip(),
                "price": float(base_price),
                "occ": int(max_occupancy),
                "amen": amenities.strip(),
                "img": image_url.strip()
            })
            return True, "Room type updated successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_room_type(rtid):
        try:
            db.execute("DELETE FROM ROOM_TYPE WHERE RoomType_ID = :rtid", {"rtid": int(rtid)})
            return True, "Room type deleted."
        except Exception as e:
            return False, str(e)

    # -------------------------------------------------------------------------
    # ROOMS CRUD
    # -------------------------------------------------------------------------
    @staticmethod
    def create_room(room_number, floor, room_type_id, price_per_night, status="AVAILABLE"):
        try:
            sql = """
                INSERT INTO ROOM (Room_Number, Floor, RoomType_ID, Price_Per_Night, Status)
                VALUES (:rnum, :floor, :rtid, :price, :status)
            """
            db.execute(sql, {
                "rnum": str(room_number).strip(),
                "floor": int(floor),
                "rtid": int(room_type_id),
                "price": float(price_per_night),
                "status": status.upper()
            })
            return True, "Room created successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_room(room_id, room_number, floor, room_type_id, price_per_night, status):
        try:
            sql = """
                UPDATE ROOM
                SET Room_Number = :rnum,
                    Floor = :floor,
                    RoomType_ID = :rtid,
                    Price_Per_Night = :price,
                    Status = :status
                WHERE Room_ID = :rid
            """
            db.execute(sql, {
                "rid": int(room_id),
                "rnum": str(room_number).strip(),
                "floor": int(floor),
                "rtid": int(room_type_id),
                "price": float(price_per_night),
                "status": status.upper()
            })
            return True, "Room updated successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_room(room_id):
        try:
            db.execute("DELETE FROM ROOM WHERE Room_ID = :rid", {"rid": int(room_id)})
            return True, "Room deleted successfully."
        except Exception as e:
            return False, str(e)

    # -------------------------------------------------------------------------
    # BOOKINGS MANAGEMENT
    # -------------------------------------------------------------------------
    @staticmethod
    def get_all_bookings(status=None):
        sql = """
            SELECT 
                b.Booking_ID, b.Customer_ID, b.Room_ID, b.Booking_Date, b.No_Of_Guests,
                b.Check_In_Date, b.Check_Out_Date, b.Total_Amount, b.Status AS Booking_Status,
                c.Name AS Customer_Name, c.Email AS Customer_Email, c.Phone AS Customer_Phone,
                r.Room_Number, rt.Type_Name AS Room_Type,
                i.Invoice_ID, i.Payment_Status, i.Total_Amount AS Invoice_Total
            FROM BOOKING b
            INNER JOIN CUSTOMER c ON b.Customer_ID = c.Customer_ID
            INNER JOIN ROOM r ON b.Room_ID = r.Room_ID
            INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
            LEFT JOIN INVOICE i ON b.Booking_ID = i.Booking_ID
            WHERE 1=1
        """
        params = {}
        if status:
            sql += " AND b.Status = :status"
            params["status"] = status.upper()
        sql += " ORDER BY b.Booking_ID DESC"
        return db.query(sql, params)

    @staticmethod
    def update_booking_status(booking_id, new_status):
        valid_statuses = ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED')
        status_clean = new_status.upper()
        if status_clean not in valid_statuses:
            return False, f"Invalid status. Choose from: {', '.join(valid_statuses)}"
        try:
            b = db.query("SELECT Room_ID FROM BOOKING WHERE Booking_ID = :bid", {"bid": int(booking_id)})
            if not b:
                return False, "Booking not found."
            room_id = b[0]["room_id"] if "room_id" in b[0] else b[0]["Room_ID"]

            db.execute("UPDATE BOOKING SET Status = :status WHERE Booking_ID = :bid", {
                "status": status_clean,
                "bid": int(booking_id)
            })

            # Synchronize room status
            if status_clean == "CHECKED_IN":
                db.execute("UPDATE ROOM SET Status = 'OCCUPIED' WHERE Room_ID = :rid", {"rid": room_id})
            elif status_clean in ("CHECKED_OUT", "CANCELLED"):
                db.execute("UPDATE ROOM SET Status = 'AVAILABLE' WHERE Room_ID = :rid AND Status = 'OCCUPIED'", {"rid": room_id})

            return True, f"Booking status updated to {status_clean}."
        except Exception as e:
            return False, str(e)

    # -------------------------------------------------------------------------
    # CUSTOMERS & EMPLOYEES & SERVICES
    # -------------------------------------------------------------------------
    @staticmethod
    def get_all_customers():
        sql = """
            SELECT 
                c.Customer_ID, c.Name, c.Email, c.Phone, c.Role, c.Address, c.Date_Of_Birth, c.Created_At,
                COUNT(b.Booking_ID) AS Total_Bookings,
                NVL(SUM(CASE WHEN b.Status != 'CANCELLED' THEN b.Total_Amount ELSE 0 END), 0) AS Total_Spent
            FROM CUSTOMER c
            LEFT JOIN BOOKING b ON c.Customer_ID = b.Customer_ID
            GROUP BY c.Customer_ID, c.Name, c.Email, c.Phone, c.Role, c.Address, c.Date_Of_Birth, c.Created_At
            ORDER BY c.Customer_ID ASC
        """
        return db.query(sql)

    @staticmethod
    def get_all_employees():
        return db.query("SELECT Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date FROM EMPLOYEE ORDER BY Employee_ID ASC")

    @staticmethod
    def create_employee(name, designation, phone, email, salary):
        try:
            if db.is_oracle_active():
                sql = """
                    INSERT INTO EMPLOYEE (Name, Designation, Phone, Email, Salary, Hire_Date)
                    VALUES (:name, :desig, :phone, :email, :salary, SYSDATE)
                """
            else:
                sql = """
                    INSERT INTO EMPLOYEE (Name, Designation, Phone, Email, Salary, Hire_Date)
                    VALUES (:name, :desig, :phone, :email, :salary, CURRENT_DATE)
                """
            db.execute(sql, {
                "name": name.strip(),
                "desig": designation.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "salary": float(salary)
            })
            return True, "Employee registered successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_service(name, category, price):
        try:
            sql = "INSERT INTO SERVICE (Service_Name, Category, Price) VALUES (:name, :cat, :price)"
            db.execute(sql, {
                "name": name.strip(),
                "cat": category.strip().upper(),
                "price": float(price)
            })
            return True, "Service created successfully."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_service(service_id):
        try:
            db.execute("DELETE FROM SERVICE WHERE Service_ID = :sid", {"sid": int(service_id)})
            return True, "Service deleted successfully."
        except Exception as e:
            return False, str(e)
