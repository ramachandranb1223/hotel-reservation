-- ============================================================================
-- SMART HOTEL RESERVATION AND BOOKING MANAGEMENT SYSTEM
-- SCRIPT 03: REALISTIC SAMPLE DATA INSERTION (EXPLICIT IDENTIFIERS)
-- Database: Oracle Database 11g / 19c / 21c / 23ai / Express Edition (XE)
-- DA2 Course Requirement: Realistic Sample Data with Zero Overlap Violations
-- ============================================================================

SET DEFINE OFF;

-- ----------------------------------------------------------------------------
-- 1. INSERT CUSTOMERS & ADMINS (12 Records)
-- Passwords:
-- Admin: admin123
-- Customers: password123
-- ----------------------------------------------------------------------------
INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (1, 'Grand Luxe Admin', '+1-555-0100', 'admin@grandluxe.com', 
        'scrypt:32768:8:1$IgOTtmTfEOdrrsm5$adad85a5256f9e7e04433b250713dfa9e279eb917a85ff7036d395b30e6a07f3b77352357bcf19c27266f09d712389109a81400dba34fed5d4dc9fff2db0bea6', 
        'ADMIN', 'Grand Luxe Tower, Penthouse Level, NY', TO_DATE('1985-05-15', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (2, 'Alice Montgomery', '+1-555-0101', 'alice@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '742 Evergreen Terrace, Springfield, OR', TO_DATE('1992-04-12', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (3, 'Brian O''Connor', '+1-555-0102', 'brian@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '1327 Ocean Drive, Miami Beach, FL', TO_DATE('1988-11-23', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (4, 'Catherine Zhao', '+1-555-0103', 'catherine@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '88 Financial Plaza, San Francisco, CA', TO_DATE('1995-02-18', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (5, 'David Miller', '+1-555-0104', 'david@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '452 Michigan Ave, Chicago, IL', TO_DATE('1983-09-05', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (6, 'Elena Rostova', '+1-555-0105', 'elena@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '19 Kensington Palace Gardens, London, UK', TO_DATE('1990-07-30', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (7, 'Franklin Harris', '+1-555-0106', 'franklin@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '302 Beacon St, Boston, MA', TO_DATE('1979-12-14', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (8, 'Grace Hopper', '+1-555-0107', 'grace@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '512 Arlington Rd, Arlington, VA', TO_DATE('1991-03-22', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (9, 'Hassan Al-Mansoor', '+1-555-0108', 'hassan@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', 'Sheikh Zayed Rd, Dubai, UAE', TO_DATE('1987-08-19', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (10, 'Isabella Rossi', '+1-555-0109', 'isabella@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', 'Via del Corso 44, Rome, Italy', TO_DATE('1994-10-09', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (11, 'James Wilson', '+1-555-0110', 'james@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '601 Congress Ave, Austin, TX', TO_DATE('1986-06-11', 'YYYY-MM-DD'));

INSERT INTO CUSTOMER (Customer_ID, Name, Phone, Email, Password_Hash, Role, Address, Date_Of_Birth)
VALUES (12, 'Kavita Sharma', '+1-555-0111', 'kavita@example.com', 
        'scrypt:32768:8:1$otrvqtMEHEsS3RSc$befdf7a4ab3fb290f64de6f17155f6e234cb67986534572fe60378f02feae383d035c8a8d8656ac83ddf0348d447c5b7cd26fb673364c15e6145e77f98cbd454', 
        'CUSTOMER', '14 Marine Drive, Mumbai, India', TO_DATE('1993-01-25', 'YYYY-MM-DD'));

-- ----------------------------------------------------------------------------
-- 2. INSERT ROOM TYPES (5 Distinct Luxury Types)
-- ----------------------------------------------------------------------------
INSERT INTO ROOM_TYPE (RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
VALUES (1, 'Deluxe Suite', 
        'Spacious luxury suite with king-size bed, private marble balcony, rain shower, and skyline city views.', 
        250.00, 2, 'King Bed, Balcony, Wi-Fi 6, Smart TV, Mini Bar, Espresso Maker', 
        'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b');

INSERT INTO ROOM_TYPE (RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
VALUES (2, 'Executive Business Room', 
        'Designed for high-productivity business travelers with ergonomic executive desk, printer, and quiet acoustic insulation.', 
        320.00, 2, 'Ergonomic Desk, High-Speed LAN, Conference Access, King Bed, Lounge Access', 
        'https://images.unsplash.com/photo-1590490360182-c33d57733427');

INSERT INTO ROOM_TYPE (RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
VALUES (3, 'Presidential Ocean Suite', 
        'Opulent top-floor oceanfront suite with wraparound terrace, private whirlpool jacuzzi, and dedicated butler service.', 
        650.00, 4, 'Panoramic Ocean View, Jacuzzi, Butler Service, Dining Room, 2 King Beds, Wine Cellar', 
        'https://images.unsplash.com/photo-1631049307264-da0ec9d70304');

INSERT INTO ROOM_TYPE (RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
VALUES (4, 'Royal Garden Villa', 
        'Private detached garden bungalow featuring a personal heated plunge pool, lush tropical surroundings, and sun deck.', 
        520.00, 3, 'Private Plunge Pool, Garden Patio, Outdoor Shower, King Bed + Daybed, Butler', 
        'https://images.unsplash.com/photo-1566665797739-1674de7a421a');

INSERT INTO ROOM_TYPE (RoomType_ID, Type_Name, Description, Base_Price, Max_Occupancy, Amenities, Image_URL)
VALUES (5, 'Classic Heritage Room', 
        'Timeless elegance crafted with handcrafted walnut wood, plush bedding, and artisanal amenities for a cozy retreat.', 
        180.00, 2, 'Queen Bed, Rain Shower, Wi-Fi, Coffee Station, 55-inch OLED TV', 
        'https://images.unsplash.com/photo-1618773928121-c32242e63f39');

-- ----------------------------------------------------------------------------
-- 3. INSERT ROOMS (20 Inventory Rooms Across 4 Floors)
-- ----------------------------------------------------------------------------
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (1, '101', 1, 5, 180.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (2, '102', 1, 5, 180.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (3, '103', 1, 5, 190.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (4, '104', 1, 1, 250.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (5, '105', 1, 1, 250.00, 'AVAILABLE');

INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (6, '201', 2, 1, 260.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (7, '202', 2, 1, 260.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (8, '203', 2, 2, 320.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (9, '204', 2, 2, 320.00, 'OCCUPIED');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (10, '205', 2, 2, 330.00, 'AVAILABLE');

INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (11, '301', 3, 2, 330.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (12, '302', 3, 4, 520.00, 'OCCUPIED');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (13, '303', 3, 4, 520.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (14, '304', 3, 4, 540.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (15, '305', 3, 4, 540.00, 'MAINTENANCE');

INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (16, '401', 4, 3, 650.00, 'OCCUPIED');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (17, '402', 4, 3, 650.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (18, '403', 4, 3, 680.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (19, '404', 4, 3, 680.00, 'AVAILABLE');
INSERT INTO ROOM (Room_ID, Room_Number, Floor, RoomType_ID, Price_Per_Night, Status) VALUES (20, '405', 4, 3, 700.00, 'AVAILABLE');

-- ----------------------------------------------------------------------------
-- 4. INSERT SERVICES (8 Distinct Hospitality Offerings)
-- ----------------------------------------------------------------------------
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (1, 'Airport VIP Limousine Transfer', 'TRANSPORT', 85.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (2, 'Aromatherapy Full Body Spa (60 min)', 'SPA', 120.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (3, 'Champagne Candlelight Beach Dinner', 'DINING', 175.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (4, 'Artisanal Champagne & Caviar Breakfast', 'DINING', 45.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (5, 'Executive Valet Laundry & Dry Cleaning', 'LAUNDRY', 35.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (6, 'Private Sunset Catamaran Yacht Tour', 'EXPERIENCE', 220.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (7, 'In-Room Wellness Yoga & Meditation Session', 'WELLNESS', 60.00);
INSERT INTO SERVICE (Service_ID, Service_Name, Category, Price) VALUES (8, 'Ultra High-Speed Dedicated VPN Router', 'BUSINESS', 25.00);

-- ----------------------------------------------------------------------------
-- 5. INSERT EMPLOYEES (8 Staff Members)
-- ----------------------------------------------------------------------------
INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (101, 'Arthur Pendelton', 'General Manager', '+1-555-0201', 'gm@grandluxe.com', 9500.00, TO_DATE('2021-03-01', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (102, 'Seraphina Laurent', 'Head Concierge', '+1-555-0202', 'concierge@grandluxe.com', 6200.00, TO_DATE('2022-01-15', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (103, 'Marcus Sterling', 'Executive Chef', '+1-555-0203', 'chef@grandluxe.com', 7800.00, TO_DATE('2021-06-10', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (104, 'Chloe Davenport', 'Spa & Wellness Director', '+1-555-0204', 'spa@grandluxe.com', 5400.00, TO_DATE('2023-02-20', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (105, 'Vikram Malhotra', 'Operations & Front Desk Lead', '+1-555-0205', 'frontdesk@grandluxe.com', 4800.00, TO_DATE('2022-08-01', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (106, 'Maria Santos', 'Executive Housekeeper', '+1-555-0206', 'housekeeping@grandluxe.com', 4200.00, TO_DATE('2022-11-05', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (107, 'Jonathan Vance', 'Chief Security Officer', '+1-555-0207', 'security@grandluxe.com', 4900.00, TO_DATE('2023-04-12', 'YYYY-MM-DD'));

INSERT INTO EMPLOYEE (Employee_ID, Name, Designation, Phone, Email, Salary, Hire_Date)
VALUES (108, 'Nadia Petrova', 'Guest Relations Specialist', '+1-555-0208', 'guestrelations@grandluxe.com', 4100.00, TO_DATE('2024-01-10', 'YYYY-MM-DD'));

-- ----------------------------------------------------------------------------
-- 6. INSERT BOOKINGS (21 Realistic Non-Overlapping Bookings, ID 1001-1021)
-- ----------------------------------------------------------------------------
INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1001, 2, 1, TO_DATE('2026-08-01', 'YYYY-MM-DD'), 2, TO_DATE('2026-08-10', 'YYYY-MM-DD'), TO_DATE('2026-08-13', 'YYYY-MM-DD'), 540.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1002, 3, 1, TO_DATE('2026-08-15', 'YYYY-MM-DD'), 1, TO_DATE('2026-08-20', 'YYYY-MM-DD'), TO_DATE('2026-08-23', 'YYYY-MM-DD'), 540.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1003, 4, 2, TO_DATE('2026-08-05', 'YYYY-MM-DD'), 2, TO_DATE('2026-08-12', 'YYYY-MM-DD'), TO_DATE('2026-08-15', 'YYYY-MM-DD'), 540.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1004, 5, 4, TO_DATE('2026-08-10', 'YYYY-MM-DD'), 2, TO_DATE('2026-08-18', 'YYYY-MM-DD'), TO_DATE('2026-08-22', 'YYYY-MM-DD'), 1000.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1005, 6, 6, TO_DATE('2026-08-12', 'YYYY-MM-DD'), 2, TO_DATE('2026-08-25', 'YYYY-MM-DD'), TO_DATE('2026-08-29', 'YYYY-MM-DD'), 1040.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1006, 7, 8, TO_DATE('2026-08-20', 'YYYY-MM-DD'), 1, TO_DATE('2026-08-28', 'YYYY-MM-DD'), TO_DATE('2026-08-31', 'YYYY-MM-DD'), 960.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1007, 8, 13, TO_DATE('2026-08-22', 'YYYY-MM-DD'), 3, TO_DATE('2026-09-01', 'YYYY-MM-DD'), TO_DATE('2026-09-04', 'YYYY-MM-DD'), 1560.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1008, 9, 17, TO_DATE('2026-08-25', 'YYYY-MM-DD'), 2, TO_DATE('2026-09-05', 'YYYY-MM-DD'), TO_DATE('2026-09-08', 'YYYY-MM-DD'), 1950.00, 'CHECKED_OUT');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1009, 10, 5, TO_DATE('2026-08-28', 'YYYY-MM-DD'), 2, TO_DATE('2026-09-10', 'YYYY-MM-DD'), TO_DATE('2026-09-14', 'YYYY-MM-DD'), 1000.00, 'CANCELLED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1010, 2, 9, TO_DATE('2026-09-15', 'YYYY-MM-DD'), 2, TO_DATE('2026-09-18', 'YYYY-MM-DD'), TO_DATE('2026-09-22', 'YYYY-MM-DD'), 1280.00, 'CHECKED_IN');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1011, 4, 12, TO_DATE('2026-09-16', 'YYYY-MM-DD'), 2, TO_DATE('2026-09-19', 'YYYY-MM-DD'), TO_DATE('2026-09-23', 'YYYY-MM-DD'), 2080.00, 'CHECKED_IN');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1012, 6, 16, TO_DATE('2026-09-14', 'YYYY-MM-DD'), 3, TO_DATE('2026-09-17', 'YYYY-MM-DD'), TO_DATE('2026-09-21', 'YYYY-MM-DD'), 2600.00, 'CHECKED_IN');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1013, 7, 1, TO_DATE('2026-09-18', 'YYYY-MM-DD'), 2, TO_DATE('2026-09-25', 'YYYY-MM-DD'), TO_DATE('2026-09-28', 'YYYY-MM-DD'), 540.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1014, 8, 3, TO_DATE('2026-09-18', 'YYYY-MM-DD'), 1, TO_DATE('2026-09-26', 'YYYY-MM-DD'), TO_DATE('2026-09-30', 'YYYY-MM-DD'), 760.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1015, 11, 4, TO_DATE('2026-09-19', 'YYYY-MM-DD'), 2, TO_DATE('2026-10-01', 'YYYY-MM-DD'), TO_DATE('2026-10-05', 'YYYY-MM-DD'), 1000.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1016, 12, 6, TO_DATE('2026-09-19', 'YYYY-MM-DD'), 2, TO_DATE('2026-10-02', 'YYYY-MM-DD'), TO_DATE('2026-10-06', 'YYYY-MM-DD'), 1040.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1017, 3, 7, TO_DATE('2026-09-19', 'YYYY-MM-DD'), 2, TO_DATE('2026-10-04', 'YYYY-MM-DD'), TO_DATE('2026-10-08', 'YYYY-MM-DD'), 1040.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1018, 5, 11, TO_DATE('2026-09-20', 'YYYY-MM-DD'), 2, TO_DATE('2026-10-05', 'YYYY-MM-DD'), TO_DATE('2026-10-09', 'YYYY-MM-DD'), 1320.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1019, 9, 13, TO_DATE('2026-09-20', 'YYYY-MM-DD'), 3, TO_DATE('2026-10-10', 'YYYY-MM-DD'), TO_DATE('2026-10-14', 'YYYY-MM-DD'), 2080.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1020, 10, 18, TO_DATE('2026-09-20', 'YYYY-MM-DD'), 2, TO_DATE('2026-10-12', 'YYYY-MM-DD'), TO_DATE('2026-10-16', 'YYYY-MM-DD'), 2720.00, 'CONFIRMED');

INSERT INTO BOOKING (Booking_ID, Customer_ID, Room_ID, Booking_Date, No_Of_Guests, Check_In_Date, Check_Out_Date, Total_Amount, Status)
VALUES (1021, 11, 10, TO_DATE('2026-09-17', 'YYYY-MM-DD'), 1, TO_DATE('2026-10-15', 'YYYY-MM-DD'), TO_DATE('2026-10-18', 'YYYY-MM-DD'), 990.00, 'CANCELLED');

-- ----------------------------------------------------------------------------
-- 7. INSERT BOOKING SERVICES (Junction Records)
-- ----------------------------------------------------------------------------
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (1, 1001, 1, 1, 85.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (2, 1001, 4, 3, 135.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (3, 1004, 2, 2, 240.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (4, 1005, 3, 1, 175.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (5, 1007, 6, 1, 220.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (6, 1008, 1, 1, 85.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (7, 1008, 2, 1, 120.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (8, 1010, 4, 2, 90.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (9, 1010, 5, 2, 70.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (10, 1011, 2, 2, 240.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (11, 1011, 7, 2, 120.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (12, 1012, 3, 1, 175.00, SYSDATE);
INSERT INTO BOOKING_SERVICE (BookingService_ID, Booking_ID, Service_ID, Quantity, Service_Amount, Service_Date) VALUES (13, 1012, 6, 1, 220.00, SYSDATE);

-- ----------------------------------------------------------------------------
-- 8. INSERT PAYMENTS (ID 5001-5020)
-- ----------------------------------------------------------------------------
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5001, 1001, SYSDATE, 760.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5002, 1002, SYSDATE, 540.00, 'UPI', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5003, 1003, SYSDATE, 540.00, 'NET_BANKING', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5004, 1004, SYSDATE, 1240.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5005, 1005, SYSDATE, 1215.00, 'DEBIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5006, 1006, SYSDATE, 960.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5007, 1007, SYSDATE, 1780.00, 'NET_BANKING', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5008, 1008, SYSDATE, 2155.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5009, 1010, SYSDATE, 1440.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5010, 1011, SYSDATE, 2440.00, 'UPI', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5011, 1012, SYSDATE, 2995.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5012, 1013, SYSDATE, 540.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5013, 1014, SYSDATE, 760.00, 'UPI', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5014, 1015, SYSDATE, 1000.00, 'NET_BANKING', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5015, 1016, SYSDATE, 1040.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5016, 1017, SYSDATE, 1040.00, 'DEBIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5017, 1018, SYSDATE, 1320.00, 'CREDIT_CARD', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5018, 1019, SYSDATE, 2080.00, 'NET_BANKING', 'COMPLETED');
INSERT INTO PAYMENT (Payment_ID, Booking_ID, Payment_Date, Amount, Payment_Mode, Status) VALUES (5019, 1020, SYSDATE, 2720.00, 'CREDIT_CARD', 'COMPLETED');

-- ----------------------------------------------------------------------------
-- 9. INSERT INVOICES (ID 9001-9020)
-- ----------------------------------------------------------------------------
INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9001, 1001, 540.00, 220.00, 91.20, 851.20, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9002, 1002, 540.00, 0.00, 64.80, 604.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9003, 1003, 540.00, 0.00, 64.80, 604.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9004, 1004, 1000.00, 240.00, 148.80, 1388.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9005, 1005, 1040.00, 175.00, 145.80, 1360.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9006, 1006, 960.00, 0.00, 115.20, 1075.20, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9007, 1007, 1560.00, 220.00, 213.60, 1993.60, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9008, 1008, 1950.00, 205.00, 258.60, 2413.60, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9009, 1010, 1280.00, 160.00, 172.80, 1612.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9010, 1011, 2080.00, 360.00, 292.80, 2732.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9011, 1012, 2600.00, 395.00, 359.40, 3354.40, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9012, 1013, 540.00, 0.00, 64.80, 604.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9013, 1014, 760.00, 0.00, 91.20, 851.20, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9014, 1015, 1000.00, 0.00, 120.00, 1120.00, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9015, 1016, 1040.00, 0.00, 124.80, 1164.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9016, 1017, 1040.00, 0.00, 124.80, 1164.80, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9017, 1018, 1320.00, 0.00, 158.40, 1478.40, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9018, 1019, 2080.00, 0.00, 249.60, 2329.60, 'PAID');

INSERT INTO INVOICE (Invoice_ID, Booking_ID, Room_Charge, Service_Charge, Tax_Amount, Total_Amount, Payment_Status)
VALUES (9019, 1020, 2720.00, 0.00, 326.40, 3046.40, 'PAID');

-- ----------------------------------------------------------------------------
-- 10. INSERT FEEDBACK (ID 1-10)
-- ----------------------------------------------------------------------------
INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (1, 2, 1001, SYSDATE, 5, 'Exceptional experience! The limousine transfer and breakfast on the balcony made our anniversary unforgettable.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (2, 3, 1002, SYSDATE, 5, 'Impeccable cleanliness and courteous concierge team. The room acoustics were phenomenal for remote meetings.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (3, 4, 1003, SYSDATE, 4, 'Very comfortable bed and smooth check-in process. Room service breakfast was warm and delicious.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (4, 5, 1004, SYSDATE, 5, 'The full body aromatherapy spa was world class. One of the best luxury hotel experiences I have ever had in the country.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (5, 6, 1005, SYSDATE, 5, 'The beach dinner was magical! Chef Marcus personally checked on our dietary preferences. 10/10 recommendation.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (6, 7, 1006, SYSDATE, 4, 'Great business amenities. Ergonomic chair and fast Wi-Fi helped me close a crucial merger during my stay.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (7, 8, 1007, SYSDATE, 5, 'The private sunset yacht tour was the highlight of our vacation. Stunning villa and serene heated pool.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (8, 9, 1008, SYSDATE, 5, 'Presidential suite views are breathtaking. The dedicated butler service made us feel like royalty.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (9, 10, NULL, SYSDATE, 4, 'Smooth cancellation process when my flights got rescheduled. Excellent customer care team.');

INSERT INTO FEEDBACK (Feedback_ID, Customer_ID, Booking_ID, Feedback_Date, Rating, Comments)
VALUES (10, 11, NULL, SYSDATE, 5, 'Grand Luxe sets the benchmark for modern hospitality. Can''t wait for our next stay in October!');

COMMIT;
