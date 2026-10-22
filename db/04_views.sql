-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 04: DATABASE VIEWS FOR REPORTING & ANALYTICS
-- Database: Oracle Database 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Views for Operational Logic & Decision Support
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. VIEW: VW_AVAILABLE_ROOMS
-- High-performance view exposing room inventory and room type attributes
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_AVAILABLE_ROOMS AS
SELECT 
    r.Room_ID,
    r.Room_Number,
    r.Floor,
    r.Price_Per_Night,
    r.Status AS Room_Status,
    rt.RoomType_ID,
    rt.Type_Name,
    rt.Description AS RoomType_Description,
    rt.Base_Price,
    rt.Max_Occupancy,
    rt.Amenities,
    rt.Image_URL
FROM ROOM r
INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID;

-- ----------------------------------------------------------------------------
-- 2. VIEW: VW_CUSTOMER_BOOKING_HISTORY
-- Comprehensive multi-table view linking customer reservations, rooms, and payments
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_CUSTOMER_BOOKING_HISTORY AS
SELECT 
    b.Booking_ID,
    b.Customer_ID,
    c.Name AS Customer_Name,
    c.Email AS Customer_Email,
    c.Phone AS Customer_Phone,
    b.Room_ID,
    r.Room_Number,
    rt.Type_Name AS Room_Type,
    b.Booking_Date,
    b.Check_In_Date,
    b.Check_Out_Date,
    (b.Check_Out_Date - b.Check_In_Date) AS Total_Nights,
    b.No_Of_Guests,
    b.Total_Amount AS Booking_Total,
    b.Status AS Booking_Status,
    p.Payment_ID,
    p.Amount AS Paid_Amount,
    p.Payment_Mode,
    p.Status AS Payment_Status,
    i.Invoice_ID,
    i.Total_Amount AS Invoice_Total,
    i.Payment_Status AS Invoice_Status
FROM BOOKING b
INNER JOIN CUSTOMER c ON b.Customer_ID = c.Customer_ID
INNER JOIN ROOM r ON b.Room_ID = r.Room_ID
INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
LEFT JOIN PAYMENT p ON b.Booking_ID = p.Booking_ID
LEFT JOIN INVOICE i ON b.Booking_ID = i.Booking_ID;

-- ----------------------------------------------------------------------------
-- 3. VIEW: VW_MONTHLY_REVENUE_REPORT
-- Revenue summary aggregated by Year, Month, and Room Type
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_MONTHLY_REVENUE_REPORT AS
SELECT 
    TO_CHAR(b.Check_In_Date, 'YYYY-MM') AS Booking_Month,
    rt.Type_Name AS Room_Type,
    COUNT(b.Booking_ID) AS Total_Bookings,
    NVL(SUM(b.Total_Amount), 0) AS Gross_Room_Revenue,
    NVL(SUM(p.Paid_Amount), 0) AS Total_Collections
FROM BOOKING b
INNER JOIN ROOM r ON b.Room_ID = r.Room_ID
INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
-- Pre-aggregate payments per booking so a booking with 2+ payments is not
-- counted twice in COUNT(b.Booking_ID) and SUM(b.Total_Amount)
LEFT JOIN (
    SELECT Booking_ID, SUM(Amount) AS Paid_Amount
    FROM PAYMENT
    WHERE Status = 'COMPLETED'
    GROUP BY Booking_ID
) p ON b.Booking_ID = p.Booking_ID
WHERE b.Status != 'CANCELLED'
GROUP BY TO_CHAR(b.Check_In_Date, 'YYYY-MM'), rt.Type_Name;

-- ----------------------------------------------------------------------------
-- 4. VIEW: VW_SERVICE_UTILIZATION
-- Tracks ancillary service sales volume and revenue contribution
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_SERVICE_UTILIZATION AS
SELECT 
    s.Service_ID,
    s.Service_Name,
    s.Category,
    s.Price AS Unit_Price,
    COUNT(bs.BookingService_ID) AS Times_Ordered,
    NVL(SUM(bs.Quantity), 0) AS Total_Units_Sold,
    NVL(SUM(bs.Service_Amount), 0) AS Total_Service_Revenue
FROM SERVICE s
LEFT JOIN BOOKING_SERVICE bs ON s.Service_ID = bs.Service_ID
GROUP BY s.Service_ID, s.Service_Name, s.Category, s.Price;

-- ----------------------------------------------------------------------------
-- 5. VIEW: VW_ROOM_OCCUPANCY_SUMMARY
-- Real-time inventory status metrics per room category
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_ROOM_OCCUPANCY_SUMMARY AS
SELECT 
    rt.Type_Name,
    COUNT(r.Room_ID) AS Total_Rooms,
    SUM(CASE WHEN r.Status = 'AVAILABLE' THEN 1 ELSE 0 END) AS Available_Rooms,
    SUM(CASE WHEN r.Status = 'OCCUPIED' THEN 1 ELSE 0 END) AS Occupied_Rooms,
    SUM(CASE WHEN r.Status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS Maintenance_Rooms,
    ROUND(
        (SUM(CASE WHEN r.Status = 'OCCUPIED' THEN 1 ELSE 0 END) * 100.0) / 
        NULLIF(COUNT(r.Room_ID), 0), 2
    ) AS Occupancy_Rate_Pct
FROM ROOM_TYPE rt
LEFT JOIN ROOM r ON rt.RoomType_ID = r.RoomType_ID
GROUP BY rt.Type_Name;

COMMIT;
