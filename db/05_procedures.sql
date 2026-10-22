-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 05: PL/SQL STORED PROCEDURES
-- Database: Oracle Database 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Stored Procedures, Error Handling & Transactions
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TRANSACTION DESIGN (applies to every procedure in this file)
-- The procedures below do NOT issue COMMIT themselves. Each one sets a SAVEPOINT
-- and, on error, rolls back only its own work (ROLLBACK TO <savepoint>) before
-- re-raising. The CALLER owns the transaction and decides when to COMMIT.
-- This lets the application run SP_CREATE_BOOKING + SP_ADD_BOOKING_SERVICE +
-- SP_GENERATE_INVOICE + SP_RECORD_PAYMENT as ONE atomic unit: either the whole
-- reservation is saved, or nothing is.
-- (When testing in SQL Developer, type COMMIT; after calling a procedure.)
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 1. PROCEDURE: SP_CREATE_BOOKING
-- Validates dates, locks the room row, verifies overlap, inserts booking
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
    SAVEPOINT sp_create_booking_start;

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

    -- 2. Verify Room Existence and Status, and LOCK the room row.
    -- FOR UPDATE makes concurrent bookings for the same room queue up here:
    -- the second session waits until the first one commits or rolls back, so
    -- its overlap check below sees the first booking. Without this lock two
    -- simultaneous requests could both see "0 overlaps" and both insert
    -- (a classic lost-update / race condition).
    BEGIN
        SELECT r.Status, r.Price_Per_Night, rt.Max_Occupancy
        INTO v_room_status, v_price_per_night, v_max_occupancy
        FROM ROOM r
        INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
        WHERE r.Room_ID = p_room_id
        FOR UPDATE OF r.Status;
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
    -- No COMMIT here: the caller commits (see TRANSACTION DESIGN above).
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO sp_create_booking_start;
        RAISE;
END SP_CREATE_BOOKING;
/

-- ----------------------------------------------------------------------------
-- 2. PROCEDURE: SP_GENERATE_INVOICE
-- Generates official tax invoice (12% tax) for a booking.
-- Payment_Status is derived from the COMPLETED payments actually received:
--   paid >= total -> 'PAID', paid > 0 -> 'PARTIAL', otherwise 'PENDING'
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
    v_amount_paid    NUMBER(10, 2) := 0;
    v_pay_status     VARCHAR2(20);
BEGIN
    SAVEPOINT sp_generate_invoice_start;

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

    -- 4. Derive payment status from completed payments
    SELECT NVL(SUM(Amount), 0)
    INTO v_amount_paid
    FROM PAYMENT
    WHERE Booking_ID = p_booking_id
      AND Status = 'COMPLETED';

    IF v_amount_paid >= v_final_amount THEN
        v_pay_status := 'PAID';
    ELSIF v_amount_paid > 0 THEN
        v_pay_status := 'PARTIAL';
    ELSE
        v_pay_status := 'PENDING';
    END IF;

    -- 5. Check if Invoice already exists (Enforce 1:1)
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
            Payment_Status = v_pay_status,
            Invoice_Date   = SYSDATE
        WHERE Booking_ID = p_booking_id;
    ELSE
        INSERT INTO INVOICE (
            Booking_ID, Invoice_Date, Room_Charge,
            Service_Charge, Tax_Amount, Total_Amount, Payment_Status
        ) VALUES (
            p_booking_id, SYSDATE, v_room_charge,
            v_service_charge, v_tax_amount, v_final_amount, v_pay_status
        ) RETURNING Invoice_ID INTO p_invoice_id;
    END IF;
    -- No COMMIT here: the caller commits.
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO sp_generate_invoice_start;
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
    SAVEPOINT sp_cancel_booking_start;

    BEGIN
        SELECT Customer_ID, Status, Check_In_Date, Room_ID
        INTO v_owner_id, v_status, v_check_in, v_room_id
        FROM BOOKING
        WHERE Booking_ID = p_booking_id
        FOR UPDATE;
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
    -- No COMMIT here: the caller commits.
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO sp_cancel_booking_start;
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
    v_dummy          NUMBER;
BEGIN
    SAVEPOINT sp_add_service_start;

    IF p_quantity IS NULL OR p_quantity <= 0 THEN
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

    -- Regenerate Invoice (runs inside the SAME transaction; it no longer commits)
    SP_GENERATE_INVOICE(p_booking_id, v_dummy);
    -- No COMMIT here: the caller commits.
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO sp_add_service_start;
        RAISE;
END SP_ADD_BOOKING_SERVICE;
/

-- ----------------------------------------------------------------------------
-- 5. PROCEDURE: SP_RECORD_PAYMENT
-- Logs a payment for a booking and refreshes the invoice payment status.
-- If p_amount is NULL, the full outstanding invoice balance is charged.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_RECORD_PAYMENT (
    p_booking_id    IN  NUMBER,
    p_payment_mode  IN  VARCHAR2,
    p_amount        IN  NUMBER DEFAULT NULL,
    p_payment_id    OUT NUMBER
) AS
    v_invoice_total  NUMBER(10, 2);
    v_already_paid   NUMBER(10, 2);
    v_amount         NUMBER(10, 2);
    v_booking_status VARCHAR2(20);
    v_dummy          NUMBER;
BEGIN
    SAVEPOINT sp_record_payment_start;

    BEGIN
        SELECT Status INTO v_booking_status
        FROM BOOKING WHERE Booking_ID = p_booking_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20040, 'Booking not found.');
    END;

    IF v_booking_status = 'CANCELLED' THEN
        RAISE_APPLICATION_ERROR(-20041, 'Cannot take payment for a cancelled booking.');
    END IF;

    -- Make sure the invoice exists and is up to date before charging
    SP_GENERATE_INVOICE(p_booking_id, v_dummy);

    SELECT Total_Amount INTO v_invoice_total
    FROM INVOICE WHERE Booking_ID = p_booking_id;

    SELECT NVL(SUM(Amount), 0) INTO v_already_paid
    FROM PAYMENT
    WHERE Booking_ID = p_booking_id AND Status = 'COMPLETED';

    v_amount := NVL(p_amount, v_invoice_total - v_already_paid);

    IF v_amount <= 0 THEN
        RAISE_APPLICATION_ERROR(-20042, 'Nothing to pay: invoice is already settled.');
    END IF;

    INSERT INTO PAYMENT (Booking_ID, Payment_Date, Amount, Payment_Mode, Status)
    VALUES (p_booking_id, SYSDATE, v_amount, p_payment_mode, 'COMPLETED')
    RETURNING Payment_ID INTO p_payment_id;

    -- Recompute PAID / PARTIAL / PENDING from all completed payments
    SP_GENERATE_INVOICE(p_booking_id, v_dummy);
    -- No COMMIT here: the caller commits.
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO sp_record_payment_start;
        RAISE;
END SP_RECORD_PAYMENT;
/
