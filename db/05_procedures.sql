-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 05: PL/SQL STORED PROCEDURES
-- Database: Oracle Database 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Stored Procedures, Error Handling & Transactions
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PROCEDURE: SP_CREATE_BOOKING
-- Atomically validates dates, verifies overlap, inserts booking, and calculates total
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_CREATE_BOOKING (
    p_customer_id   IN  NUMBER,
    p_room_id       IN  NUMBER,
    p_check_in      IN  DATE,
    p_check_out     IN  DATE,
    p_no_of_guests  IN  NUMBER,
    p_booking_id    OUT NUMBER
) AS
    v_room_count       NUMBER;
    v_overlap_count    NUMBER;
    v_max_occupancy    NUMBER;
    v_room_status      VARCHAR2(20);
    v_price_per_night  NUMBER(10, 2);
    v_total_amount     NUMBER(10, 2);
BEGIN
    -- 1. Validate Input Dates
    IF p_check_in IS NULL OR p_check_out IS NULL THEN
        RAISE_APPLICATION_ERROR(-20001, 'Check-in and check-out dates are mandatory.');
    END IF;

    IF p_check_out <= p_check_in THEN
        RAISE_APPLICATION_ERROR(-20002, 'Check-out date must be strictly later than check-in date.');
    END IF;

    IF TRUNC(p_check_in) < TRUNC(SYSDATE) THEN
        RAISE_APPLICATION_ERROR(-20003, 'Check-in date cannot be in the past.');
    END IF;

    IF p_no_of_guests IS NULL OR p_no_of_guests <= 0 THEN
        RAISE_APPLICATION_ERROR(-20004, 'Number of guests must be at least 1.');
    END IF;

    -- 2. Verify Room Existence and Status
    BEGIN
        SELECT r.Status, r.Price_Per_Night, rt.Max_Occupancy
        INTO v_room_status, v_price_per_night, v_max_occupancy
        FROM ROOM r
        INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
        WHERE r.Room_ID = p_room_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20005, 'Selected room does not exist in inventory.');
    END;

    IF v_room_status = 'MAINTENANCE' THEN
        RAISE_APPLICATION_ERROR(-20006, 'Selected room is currently undergoing maintenance.');
    END IF;

    IF p_no_of_guests > v_max_occupancy THEN
        RAISE_APPLICATION_ERROR(-20007, 'Guest count exceeds maximum room occupancy of ' || v_max_occupancy || '.');
    END IF;

    -- 3. Overlap Check: Reject conflicting active reservations for the same room
    SELECT COUNT(*)
    INTO v_overlap_count
    FROM BOOKING
    WHERE Room_ID = p_room_id
      AND Status IN ('CONFIRMED', 'CHECKED_IN')
      AND Check_In_Date < p_check_out
      AND Check_Out_Date > p_check_in;

    IF v_overlap_count > 0 THEN
        RAISE_APPLICATION_ERROR(-20008, 'Room is not available for the selected dates due to a conflicting reservation.');
    END IF;

    -- 4. Calculate Base Amount (Nights * Rate)
    v_total_amount := (TRUNC(p_check_out) - TRUNC(p_check_in)) * v_price_per_night;

    -- 5. Insert Booking Record
    INSERT INTO BOOKING (
        Customer_ID, Room_ID, Booking_Date, No_Of_Guests,
        Check_In_Date, Check_Out_Date, Total_Amount, Status
    ) VALUES (
        p_customer_id, p_room_id, SYSDATE, p_no_of_guests,
        TRUNC(p_check_in), TRUNC(p_check_out), v_total_amount, 'CONFIRMED'
    ) RETURNING Booking_ID INTO p_booking_id;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_CREATE_BOOKING;
/

-- ----------------------------------------------------------------------------
-- 2. PROCEDURE: SP_GENERATE_INVOICE
-- Generates official tax invoice (12% tax) for a booking
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_GENERATE_INVOICE (
    p_booking_id   IN  NUMBER,
    p_invoice_id   OUT NUMBER
) AS
    v_room_charge    NUMBER(10, 2) := 0;
    v_service_charge NUMBER(10, 2) := 0;
    v_subtotal       NUMBER(10, 2) := 0;
    v_tax_amount     NUMBER(10, 2) := 0;
    v_final_amount   NUMBER(10, 2) := 0;
    v_existing_inv   NUMBER := 0;
BEGIN
    -- 1. Fetch Room Stay Charge
    BEGIN
        SELECT Total_Amount
        INTO v_room_charge
        FROM BOOKING
        WHERE Booking_ID = p_booking_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20010, 'Booking ID ' || p_booking_id || ' not found.');
    END;

    -- 2. Calculate Services Total
    SELECT NVL(SUM(Service_Amount), 0)
    INTO v_service_charge
    FROM BOOKING_SERVICE
    WHERE Booking_ID = p_booking_id;

    -- 3. Calculate Tax (12% standard GST/Hospitality tax)
    v_subtotal := v_room_charge + v_service_charge;
    v_tax_amount := ROUND(v_subtotal * 0.12, 2);
    v_final_amount := v_subtotal + v_tax_amount;

    -- 4. Check if Invoice already exists (Enforce 1:1)
    SELECT COUNT(*), NVL(MAX(Invoice_ID), 0)
    INTO v_existing_inv, p_invoice_id
    FROM INVOICE
    WHERE Booking_ID = p_booking_id;

    IF v_existing_inv > 0 THEN
        UPDATE INVOICE
        SET Room_Charge    = v_room_charge,
            Service_Charge = v_service_charge,
            Tax_Amount     = v_tax_amount,
            Total_Amount   = v_final_amount,
            Invoice_Date   = SYSDATE
        WHERE Booking_ID = p_booking_id;
    ELSE
        INSERT INTO INVOICE (
            Booking_ID, Invoice_Date, Room_Charge,
            Service_Charge, Tax_Amount, Total_Amount, Payment_Status
        ) VALUES (
            p_booking_id, SYSDATE, v_room_charge,
            v_service_charge, v_tax_amount, v_final_amount, 'PAID'
        ) RETURNING Invoice_ID INTO p_invoice_id;
    END IF;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_GENERATE_INVOICE;
/

-- ----------------------------------------------------------------------------
-- 3. PROCEDURE: SP_CANCEL_BOOKING
-- Safely cancels a booking preserving historical data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_CANCEL_BOOKING (
    p_booking_id    IN  NUMBER,
    p_customer_id   IN  NUMBER,
    p_result        OUT VARCHAR2
) AS
    v_owner_id      NUMBER;
    v_status        VARCHAR2(20);
    v_check_in      DATE;
    v_room_id       NUMBER;
BEGIN
    BEGIN
        SELECT Customer_ID, Status, Check_In_Date, Room_ID
        INTO v_owner_id, v_status, v_check_in, v_room_id
        FROM BOOKING
        WHERE Booking_ID = p_booking_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20020, 'Booking record not found.');
    END;

    -- Permission check (Customer must own booking, or p_customer_id = 0 for Admin)
    IF p_customer_id != 0 AND v_owner_id != p_customer_id THEN
        RAISE_APPLICATION_ERROR(-20021, 'Unauthorized: You can only cancel your own bookings.');
    END IF;

    IF v_status = 'CANCELLED' THEN
        RAISE_APPLICATION_ERROR(-20022, 'This booking has already been cancelled.');
    END IF;

    IF v_status = 'CHECKED_OUT' THEN
        RAISE_APPLICATION_ERROR(-20023, 'Completed stays cannot be cancelled.');
    END IF;

    -- Update booking status to CANCELLED (Never delete historical records!)
    UPDATE BOOKING
    SET Status = 'CANCELLED'
    WHERE Booking_ID = p_booking_id;

    -- Update payment status if exists
    UPDATE PAYMENT
    SET Status = 'REFUNDED'
    WHERE Booking_ID = p_booking_id;

    p_result := 'Booking #' || p_booking_id || ' successfully cancelled.';
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_CANCEL_BOOKING;
/

-- ----------------------------------------------------------------------------
-- 4. PROCEDURE: SP_ADD_BOOKING_SERVICE
-- Attaches an ancillary service to a booking and updates the grand total
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_ADD_BOOKING_SERVICE (
    p_booking_id   IN  NUMBER,
    p_service_id   IN  NUMBER,
    p_quantity     IN  NUMBER,
    p_subtotal     OUT NUMBER
) AS
    v_unit_price     NUMBER(10, 2);
    v_line_total     NUMBER(10, 2);
    v_booking_status VARCHAR2(20);
BEGIN
    IF p_quantity <= 0 THEN
        RAISE_APPLICATION_ERROR(-20030, 'Quantity must be greater than zero.');
    END IF;

    -- Verify Booking
    BEGIN
        SELECT Status
        INTO v_booking_status
        FROM BOOKING
        WHERE Booking_ID = p_booking_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20031, 'Booking not found.');
    END;

    IF v_booking_status = 'CANCELLED' THEN
        RAISE_APPLICATION_ERROR(-20032, 'Cannot add services to a cancelled booking.');
    END IF;

    -- Verify Service & Get Price
    BEGIN
        SELECT Price
        INTO v_unit_price
        FROM SERVICE
        WHERE Service_ID = p_service_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20033, 'Service not found.');
    END;

    v_line_total := v_unit_price * p_quantity;
    p_subtotal := v_line_total;

    -- Insert into junction table
    INSERT INTO BOOKING_SERVICE (
        Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date
    ) VALUES (
        p_booking_id, p_service_id, p_quantity, v_line_total, SYSDATE
    );

    -- Regenerate Invoice
    DECLARE
        v_dummy NUMBER;
    BEGIN
        SP_GENERATE_INVOICE(p_booking_id, v_dummy);
    END;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END SP_ADD_BOOKING_SERVICE;
/
