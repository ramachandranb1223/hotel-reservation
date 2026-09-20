-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 07: PL/SQL DATABASE TRIGGERS
-- Database: Oracle Database 11g / 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Triggers for Business Rule Automation & Integrity
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TRIGGER: TRG_ENFORCE_DATE_INTEGRITY
-- Ensures check_out > check_in and validates check-in is not before booking date
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER TRG_ENFORCE_DATE_INTEGRITY
BEFORE INSERT OR UPDATE ON BOOKING
FOR EACH ROW
BEGIN
    IF :NEW.Check_Out_Date <= :NEW.Check_In_Date THEN
        RAISE_APPLICATION_ERROR(-20050, 'Trigger Error: Check-out date must be strictly after check-in date.');
    END IF;

    IF :NEW.Check_In_Date < TRUNC(:NEW.Booking_Date) THEN
        RAISE_APPLICATION_ERROR(-20051, 'Trigger Error: Check-in date cannot precede the booking date.');
    END IF;
END;
/

-- ----------------------------------------------------------------------------
-- 2. TRIGGER: TRG_SYNC_ROOM_STATUS
-- Automatically updates physical room status based on booking lifecycle events
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER TRG_SYNC_ROOM_STATUS
AFTER INSERT OR UPDATE OF Status ON BOOKING
FOR EACH ROW
BEGIN
    -- If guest checks in, mark room as OCCUPIED
    IF :NEW.Status = 'CHECKED_IN' THEN
        UPDATE ROOM
        SET Status = 'OCCUPIED'
        WHERE Room_ID = :NEW.Room_ID;
        
    -- If guest checks out or cancels, revert room to AVAILABLE if not in maintenance
    ELSIF :NEW.Status IN ('CHECKED_OUT', 'CANCELLED') THEN
        UPDATE ROOM
        SET Status = 'AVAILABLE'
        WHERE Room_ID = :NEW.Room_ID
          AND Status = 'OCCUPIED';
    END IF;
END;
/

-- ----------------------------------------------------------------------------
-- 3. TRIGGER: TRG_AUTO_UPDATE_INVOICE_STATUS
-- Synchronizes invoice payment status when a completed payment is logged
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TRIGGER TRG_AUTO_UPDATE_INVOICE_STATUS
AFTER INSERT OR UPDATE ON PAYMENT
FOR EACH ROW
BEGIN
    IF :NEW.Status = 'COMPLETED' THEN
        UPDATE INVOICE
        SET Payment_Status = 'PAID'
        WHERE Booking_ID = :NEW.Booking_ID;
    END IF;
END;
/
