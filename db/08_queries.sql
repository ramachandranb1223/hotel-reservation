-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 08: DEMONSTRATION SQL QUERIES & VIVA REPORTS
-- Database: Oracle Database 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Joins, Aggregates, Group By, Having, Subqueries, EXISTS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: INNER JOIN WITH WHERE AND ORDER BY
-- List all active confirmed bookings with customer and room details
-- ----------------------------------------------------------------------------
SELECT 
    b.Booking_ID,
    c.Name AS Guest_Name,
    c.Phone,
    r.Room_Number,
    rt.Type_Name,
    b.Check_In_Date,
    b.Check_Out_Date,
    b.Total_Amount
FROM BOOKING b
INNER JOIN CUSTOMER c ON b.Customer_ID = c.Customer_ID
INNER JOIN ROOM r ON b.Room_ID = r.Room_ID
INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
WHERE b.Status = 'CONFIRMED'
ORDER BY b.Check_In_Date ASC;

-- ----------------------------------------------------------------------------
-- QUERY 2: LEFT OUTER JOIN & AGGREGATES
-- Show total revenue generated per room type, including room types with 0 bookings
-- ----------------------------------------------------------------------------
SELECT 
    rt.Type_Name,
    rt.Base_Price,
    COUNT(b.Booking_ID) AS Total_Bookings,
    NVL(SUM(b.Total_Amount), 0) AS Total_Revenue,
    NVL(AVG(b.Total_Amount), 0) AS Average_Booking_Value
FROM ROOM_TYPE rt
LEFT JOIN ROOM r ON rt.RoomType_ID = r.RoomType_ID
LEFT JOIN BOOKING b ON r.Room_ID = b.Room_ID AND b.Status != 'CANCELLED'
GROUP BY rt.Type_Name, rt.Base_Price
ORDER BY Total_Revenue DESC;

-- ----------------------------------------------------------------------------
-- QUERY 3: GROUP BY WITH HAVING CLAUSE
-- Find high-value VIP customers who have spent more than $1,500 across all stays
-- ----------------------------------------------------------------------------
SELECT 
    c.Customer_ID,
    c.Name AS Customer_Name,
    c.Email,
    COUNT(b.Booking_ID) AS Total_Reservations,
    SUM(p.Amount) AS Total_Expenditure
FROM CUSTOMER c
INNER JOIN BOOKING b ON c.Customer_ID = b.Customer_ID
INNER JOIN PAYMENT p ON b.Booking_ID = p.Booking_ID
WHERE p.Status = 'COMPLETED'
GROUP BY c.Customer_ID, c.Name, c.Email
HAVING SUM(p.Amount) > 1500.00
ORDER BY Total_Expenditure DESC;

-- ----------------------------------------------------------------------------
-- QUERY 4: SUBQUERY (SCALAR & COMPARISON)
-- Find all rooms whose nightly price is higher than the average room price
-- ----------------------------------------------------------------------------
SELECT 
    r.Room_ID,
    r.Room_Number,
    rt.Type_Name,
    r.Price_Per_Night,
    ROUND((SELECT AVG(Price_Per_Night) FROM ROOM), 2) AS Average_Hotel_Rate
FROM ROOM r
INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
WHERE r.Price_Per_Night > (SELECT AVG(Price_Per_Night) FROM ROOM)
ORDER BY r.Price_Per_Night DESC;

-- ----------------------------------------------------------------------------
-- QUERY 5: CORRELATED SUBQUERY WITH NOT EXISTS
-- Find customers who registered but have never made any room reservation
-- ----------------------------------------------------------------------------
SELECT 
    c.Customer_ID,
    c.Name,
    c.Email,
    c.Created_At
FROM CUSTOMER c
WHERE c.Role = 'CUSTOMER'
  AND NOT EXISTS (
      SELECT 1 
      FROM BOOKING b 
      WHERE b.Customer_ID = c.Customer_ID
  );

-- ----------------------------------------------------------------------------
-- QUERY 6: CORRELATED SUBQUERY WITH EXISTS
-- Find all rooms that currently have at least one active checked-in guest
-- ----------------------------------------------------------------------------
SELECT 
    r.Room_ID,
    r.Room_Number,
    r.Floor,
    rt.Type_Name
FROM ROOM r
INNER JOIN ROOM_TYPE rt ON r.RoomType_ID = rt.RoomType_ID
WHERE EXISTS (
    SELECT 1 
    FROM BOOKING b 
    WHERE b.Room_ID = r.Room_ID 
      AND b.Status = 'CHECKED_IN'
);

-- ----------------------------------------------------------------------------
-- QUERY 7: MULTI-TABLE AGGREGATION - ANCILLARY SERVICE USAGE SUMMARY
-- Breakdown of extra services ordered by guests with revenue contribution
-- ----------------------------------------------------------------------------
SELECT 
    s.Category,
    s.Service_Name,
    s.Price AS Unit_Cost,
    COUNT(bs.BookingService_ID) AS Order_Count,
    SUM(bs.Quantity) AS Total_Units_Consumed,
    SUM(bs.Service_Amount) AS Total_Revenue_USD
FROM SERVICE s
INNER JOIN BOOKING_SERVICE bs ON s.Service_ID = bs.Service_ID
GROUP BY s.Category, s.Service_Name, s.Price
ORDER BY Total_Revenue_USD DESC;

-- ----------------------------------------------------------------------------
-- QUERY 8: PAYMENT METHOD DISTRIBUTION
-- Aggregate collection summary grouped by payment channel
-- ----------------------------------------------------------------------------
SELECT 
    Payment_Mode,
    COUNT(Payment_ID) AS Total_Transactions,
    SUM(Amount) AS Total_Collected,
    ROUND((SUM(Amount) * 100.0) / (SELECT SUM(Amount) FROM PAYMENT WHERE Status = 'COMPLETED'), 2) AS Pct_Of_Revenue
FROM PAYMENT
WHERE Status = 'COMPLETED'
GROUP BY Payment_Mode
ORDER BY Total_Collected DESC;

-- ----------------------------------------------------------------------------
-- QUERY 9: VIEW DEMONSTRATION - MONTHLY REVENUE & COLLECTIONS
-- Demonstrates querying the pre-compiled analytical view VW_MONTHLY_REVENUE_REPORT
-- ----------------------------------------------------------------------------
SELECT * 
FROM VW_MONTHLY_REVENUE_REPORT
ORDER BY Booking_Month DESC, Gross_Room_Revenue DESC;

-- ----------------------------------------------------------------------------
-- QUERY 10: VIEW DEMONSTRATION - ROOM OCCUPANCY KPI
-- Real-time inventory occupancy percentage from VW_ROOM_OCCUPANCY_SUMMARY
-- ----------------------------------------------------------------------------
SELECT * 
FROM VW_ROOM_OCCUPANCY_SUMMARY
ORDER BY Occupancy_Rate_Pct DESC;
