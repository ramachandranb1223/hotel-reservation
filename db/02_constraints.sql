-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 02: EXPLICIT CONSTRAINTS & PERFORMANCE INDEXES
-- Database: Oracle Database 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Constraint Verification & Indexing
-- ============================================================================

-- B-tree Indexes for High-Traffic Foreign Keys & Queries
CREATE INDEX IDX_ROOM_ROOMTYPE ON ROOM (RoomType_ID);
CREATE INDEX IDX_BOOKING_CUSTOMER ON BOOKING (Customer_ID);
CREATE INDEX IDX_BOOKING_ROOM ON BOOKING (Room_ID);
CREATE INDEX IDX_BOOKING_DATES ON BOOKING (Check_In_Date, Check_Out_Date);
CREATE INDEX IDX_PAYMENT_BOOKING ON PAYMENT (Booking_ID);
CREATE INDEX IDX_BS_BOOKING ON BOOKING_SERVICE (Booking_ID);
CREATE INDEX IDX_BS_SERVICE ON BOOKING_SERVICE (Service_ID);
CREATE INDEX IDX_FEEDBACK_CUSTOMER ON FEEDBACK (Customer_ID);

-- Additional Business Integrity Verification
-- (Ensures constraints are enabled and validated in Oracle Data Dictionary)
ALTER TABLE BOOKING ENABLE CONSTRAINT CHK_BOOKING_DATES;
ALTER TABLE FEEDBACK ENABLE CONSTRAINT CHK_FEEDBACK_RATING;

COMMIT;
