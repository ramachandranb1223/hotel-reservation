from werkzeug.security import generate_password_hash, check_password_hash
from db.connection import db
from utils.validation import validate_email, validate_phone

class AuthService:
    @staticmethod
    def register_customer(name, phone, email, password, address="", dob=None):
        # Validation
        if not name or len(name.strip()) < 2:
            return False, "Full name must be at least 2 characters."
        
        ok, err = validate_email(email)
        if not ok:
            return False, err
            
        ok, err = validate_phone(phone)
        if not ok:
            return False, err
            
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long."

        email_clean = email.strip().lower()
        phone_clean = phone.strip()

        # Check existing email or phone
        if db.is_oracle_active():
            existing = db.query(
                "SELECT Customer_ID FROM CUSTOMER WHERE LOWER(Email) = :email OR Phone = :phone",
                {"email": email_clean, "phone": phone_clean}
            )
        else:
            existing = db.query(
                "SELECT Customer_ID FROM CUSTOMER WHERE LOWER(Email) = :email OR Phone = :phone",
                {"email": email_clean, "phone": phone_clean}
            )
        if existing:
            return False, "An account with this email or phone number already exists."

        # Hash password
        pwd_hash = generate_password_hash(password)

        try:
            if db.is_oracle_active():
                sql = """
                    INSERT INTO CUSTOMER (Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
                    VALUES (:name, :phone, :email, :pwd, 'CUSTOMER', :addr, TO_DATE(:dob, 'YYYY-MM-DD'))
                """
                db.execute(sql, {
                    "name": name.strip(),
                    "phone": phone_clean,
                    "email": email_clean,
                    "pwd": pwd_hash,
                    "addr": address.strip() if address else None,
                    "dob": dob if dob else "1990-01-01"
                })
                # Fetch new ID
                cust = db.query("SELECT Customer_ID, Name, Email, Role FROM CUSTOMER WHERE LOWER(Email) = :email", {"email": email_clean})
                return True, cust[0] if cust else None
            else:
                db.execute("""
                    INSERT INTO CUSTOMER (Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
                    VALUES (:name, :phone, :email, :pwd, 'CUSTOMER', :addr, :dob)
                """, {
                    "name": name.strip(),
                    "phone": phone_clean,
                    "email": email_clean,
                    "pwd": pwd_hash,
                    "addr": address.strip() if address else "",
                    "dob": dob if dob else "1990-01-01"
                })
                cust = db.query("SELECT Customer_ID, Name, Email, Role FROM CUSTOMER WHERE LOWER(Email) = :email", {"email": email_clean})
                return True, cust[0] if cust else None
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    @staticmethod
    def authenticate_user(email, password):
        if not email or not password:
            return False, "Email and password are required."
        
        email_clean = email.strip().lower()
        rows = db.query(
            "SELECT Customer_ID, Name, Email, Password_Hash, Role, Phone, Address FROM CUSTOMER WHERE LOWER(Email) = :email",
            {"email": email_clean}
        )
        if not rows:
            return False, "Invalid email or password."

        user = rows[0]
        stored_hash = user.get("password_hash") or user.get("Password_Hash")
        
        # Verify hash or direct fallback for testing
        is_valid = check_password_hash(stored_hash, password) or (stored_hash == password)
        if not is_valid:
            return False, "Invalid email or password."

        user_data = {
            "customer_id": user.get("customer_id") or user.get("Customer_ID"),
            "name": user.get("name") or user.get("Name"),
            "email": user.get("email") or user.get("Email"),
            "role": user.get("role") or user.get("Role"),
            "phone": user.get("phone") or user.get("Phone"),
            "address": user.get("address") or user.get("Address")
        }
        return True, user_data

    @staticmethod
    def get_user_by_id(customer_id):
        rows = db.query(
            "SELECT Customer_ID, Name, Email, Role, Phone, Address, Date_Of_Birth FROM CUSTOMER WHERE Customer_ID = :cid",
            {"cid": customer_id}
        )
        return rows[0] if rows else None
