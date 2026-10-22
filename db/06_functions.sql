-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 06: PL/SQL STORED FUNCTIONS
-- Database: Oracle Database 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Stored Functions with Deterministic Logic
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. FUNCTION: FN_CALCULATE_BOOKING_AMOUNT
-- Computes the total monetary obligation for a room stay + optional services
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION FN_CALCULATE_BOOKING_AMOUNT (
    p_room_id       IN NUMBER,
    p_check_in      IN DATE,
    p_check_out     IN DATE,
    p_booking_id    IN NUMBER DEFAULT NULL
) RETURN NUMBER IS
    v_nights         NUMBER;
    v_price_per_night NUMBER(10, 2) := 0;
    v_room_cost      NUMBER(10, 2) := 0;
    v_service_cost   NUMBER(10, 2) := 0;
    v_grand_total    NUMBER(10, 2) := 0;
BEGIN
    -- Validate dates
    IF p_check_out <= p_check_in THEN
        RETURN 0;
    END IF;

    v_nights := TRUNC(p_check_out) - TRUNC(p_check_in);

    -- Fetch room rate
    BEGIN
        SELECT Price_Per_Night
        INTO v_price_per_night
        FROM ROOM
        WHERE Room_ID = p_room_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
    END;

    v_room_cost := v_nights * v_price_per_night;

    -- Include any existing services if booking ID provided
    IF p_booking_id IS NOT NULL THEN
        SELECT NVL(SUM(Service_Amount), 0)
        INTO v_service_cost
        FROM BOOKING_SERVICE
        WHERE Booking_ID = p_booking_id;
    END IF;

    v_grand_total := v_room_cost + v_service_cost;
    RETURN v_grand_total;
END FN_CALCULATE_BOOKING_AMOUNT;
/

-- ----------------------------------------------------------------------------
-- 2. FUNCTION: FN_IS_ROOM_AVAILABLE
-- Checks if a room has any overlapping active reservations
-- Returns: 1 (Available), 0 (Unavailable)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION FN_IS_ROOM_AVAILABLE (
    p_room_id       IN NUMBER,
    p_check_in      IN DATE,
    p_check_out     IN DATE
) RETURN NUMBER IS
    v_conflict_count NUMBER := 0;
    v_room_status    VARCHAR2(20);
BEGIN
    -- Verify room is not in maintenance
    BEGIN
        SELECT Status INTO v_room_status FROM ROOM WHERE Room_ID = p_room_id;
        IF v_room_status = 'MAINTENANCE' THEN
            RETURN 0;
        END IF;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
    END;

    -- Check date range overlap with active reservations
    SELECT COUNT(*)
    INTO v_conflict_count
    FROM BOOKING
    WHERE Room_ID = p_room_id
      AND Status IN ('CONFIRMED', 'CHECKED_IN')
      AND Check_In_Date < p_check_out
      AND Check_Out_Date > p_check_in;

    IF v_conflict_count = 0 THEN
        RETURN 1; -- Available
    ELSE
        RETURN 0; -- Booked / Unavailable
    END IF;
END FN_IS_ROOM_AVAILABLE;
/

-- ----------------------------------------------------------------------------
-- 3. FUNCTION: FN_GET_CUSTOMER_TOTAL_SPENT
-- Aggregates total completed payments across all bookings for a customer
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION FN_GET_CUSTOMER_TOTAL_SPENT (
    p_customer_id IN NUMBER
) RETURN NUMBER IS
    v_total_spent NUMBER(10, 2) := 0;
BEGIN
    SELECT NVL(SUM(p.Amount), 0)
    INTO v_total_spent
    FROM PAYMENT p
    INNER JOIN BOOKING b ON p.Booking_ID = b.Booking_ID
    WHERE b.Customer_ID = p_customer_id
      AND p.Status = 'COMPLETED';

    RETURN v_total_spent;
END FN_GET_CUSTOMER_TOTAL_SPENT;
/
