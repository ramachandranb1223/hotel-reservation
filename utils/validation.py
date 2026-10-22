import re
from datetime import datetime, date

def validate_email(email):
    if not email or not isinstance(email, str):
        return False, "Email address is required."
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email.strip()):
        return False, "Invalid email address format."
    return True, None

def validate_phone(phone):
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required."
    cleaned = re.sub(r'[\s\-\+\(\)]', '', phone)
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False, "Phone number must be between 7 and 15 digits."
    return True, None

def validate_booking_dates(check_in_str, check_out_str):
    if not check_in_str or not check_out_str:
        return False, "Both check-in and check-out dates are required."
    try:
        check_in = datetime.strptime(check_in_str.strip(), "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD."

    today = date.today()
    if check_in < today:
        return False, "Check-in date cannot be in the past."
    if check_out <= check_in:
        return False, "Check-out date must be strictly after check-in date."

    nights = (check_out - check_in).days
    if nights > 30:
        return False, "Maximum reservation duration is 30 consecutive nights."

    return True, (check_in, check_out, nights)

def validate_guest_count(count, max_allowed=10):
    try:
        val = int(count)
        if val <= 0:
            return False, "Guest count must be at least 1."
        if val > max_allowed:
            return False, f"Guest count exceeds maximum allowed of {max_allowed}."
        return True, val
    except (ValueError, TypeError):
        return False, "Guest count must be a valid integer."

def validate_feedback(rating, comments):
    try:
        r = int(rating)
        if r < 1 or r > 5:
            return False, "Rating must be an integer between 1 and 5."
    except (ValueError, TypeError):
        return False, "Rating must be a numerical score."
    
    if comments and len(comments) > 1000:
        return False, "Comments cannot exceed 1000 characters."
    return True, None
