"""
End-to-End Automated Integration Test Suite
Validates:
1. User Registration & Authentication
2. Room Availability Query
3. Successful Booking via SP_CREATE_BOOKING
4. Overlap Prevention (Double Booking Rejection)
5. Date Constraint Validation (Check-out <= Check-in rejection)
6. Service Attachment via BOOKING_SERVICE
7. Invoice Computation (12% tax) via SP_GENERATE_INVOICE
8. Safe Booking Cancellation via SP_CANCEL_BOOKING
9. Admin Dashboard & Analytical Reports
"""
import sys
import os
import unittest
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db.connection import db
from services.auth_service import AuthService
from services.booking_service import BookingService
from services.report_service import ReportService
from services.admin_service import AdminService

class TestHotelReservationSystem(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_user_authentication(self):
        print("\n[TEST 1] Testing User Authentication & Hash Verification...")
        # Test admin login
        ok, user = AuthService.authenticate_user("admin@grandluxe.com", "admin123")
        self.assertTrue(ok, "Admin authentication failed.")
        self.assertEqual(user["role"], "ADMIN")

        # Test customer login
        ok, cust = AuthService.authenticate_user("alice@example.com", "password123")
        self.assertTrue(ok, "Customer authentication failed.")
        self.assertEqual(cust["role"], "CUSTOMER")
        print("  User Authentication Passed.")

    def test_02_room_search_availability(self):
        print("\n[TEST 2] Testing Room Search & Availability Filter...")
        cin = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        cout = (date.today() + timedelta(days=33)).strftime("%Y-%m-%d")

        ok, res = BookingService.search_available_rooms(cin, cout, guests=2)
        self.assertTrue(ok)
        self.assertEqual(res["nights"], 3)
        self.assertGreater(len(res["rooms"]), 0)
        print(f"  Found {len(res['rooms'])} available rooms for 3 nights.")

    def test_03_create_booking_and_invoice(self):
        print("\n[TEST 3] Testing Booking Creation & Automatic Invoice Generation...")
        cin = (date.today() + timedelta(days=40)).strftime("%Y-%m-%d")
        cout = (date.today() + timedelta(days=43)).strftime("%Y-%m-%d")

        # Room 102 (Classic Heritage, $180/night)
        ok, booking_id = BookingService.create_booking(
            customer_id=2, # Alice
            room_id=2,
            check_in_str=cin,
            check_out_str=cout,
            no_of_guests=2
        )
        self.assertTrue(ok, f"Booking creation failed: {booking_id}")
        self.assertIsNotNone(booking_id)

        # Verify Booking details & Invoice
        details = BookingService.get_booking_details(booking_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["status"] if "status" in details else details["Booking_Status"], "CONFIRMED")
        
        # 3 nights * $180 = $540
        total = details["total_amount"] if "total_amount" in details else details["Total_Amount"]
        self.assertEqual(float(total), 540.0)

        # Verify Invoice (12% tax on $540 = $64.80 -> $604.80)
        inv = details["invoice"]
        self.assertIsNotNone(inv)
        inv_total = inv["total_amount"] if "total_amount" in inv else inv["Total_Amount"]
        self.assertEqual(float(inv_total), 604.80)
        print(f"  Booking #{booking_id} created with verified Invoice Total: ${inv_total}")

        # Store for subsequent overlap test
        self.__class__.created_booking_id = booking_id
        self.__class__.test_cin = cin
        self.__class__.test_cout = cout

    def test_04_overlap_prevention(self):
        print("\n[TEST 4] Testing Overlapping Booking Prevention (Double Booking)...")
        # Attempt to create conflicting booking for Room 102 (Room_ID = 2) during identical dates
        cin = self.__class__.test_cin
        cout = self.__class__.test_cout

        ok, err = BookingService.create_booking(
            customer_id=3, # Brian
            room_id=2,     # Same room!
            check_in_str=cin,
            check_out_str=cout,
            no_of_guests=1
        )
        self.assertFalse(ok, "Overlap prevention failed! A conflicting booking was permitted.")
        self.assertIn("conflicting reservation", err.lower())
        print(f"  Overlap successfully rejected with error: '{err}'")

    def test_05_date_integrity_constraints(self):
        print("\n[TEST 5] Testing Date Order Integrity (Check-out <= Check-in)...")
        cin = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        cout_invalid = (date.today() + timedelta(days=8)).strftime("%Y-%m-%d")

        ok, err = BookingService.create_booking(
            customer_id=2,
            room_id=1,
            check_in_str=cin,
            check_out_str=cout_invalid,
            no_of_guests=1
        )
        self.assertFalse(ok, "Invalid reverse date range was incorrectly accepted.")
        self.assertIn("later than check-in", err.lower())
        print(f"  Invalid date range correctly rejected with message: '{err}'")

    def test_06_add_service_to_booking(self):
        print("\n[TEST 6] Testing Ancillary Service Attachment (M:N via BOOKING_SERVICE)...")
        booking_id = self.__class__.created_booking_id
        # Add Service 1: Limousine ($85.00)
        ok, msg = BookingService.add_booking_service(booking_id, service_id=1, quantity=1)
        self.assertTrue(ok, f"Failed to attach service: {msg}")

        # Verify updated invoice: Room ($540) + Service ($85) = $625. Tax = 12% of 625 = $75. Total = $700.00
        details = BookingService.get_booking_details(booking_id)
        inv = details["invoice"]
        inv_total = inv["total_amount"] if "total_amount" in inv else inv["Total_Amount"]
        self.assertEqual(float(inv_total), 700.00)
        print(f"  Service attached successfully. Updated Invoice Total: ${inv_total}")

    def test_07_cancel_booking(self):
        print("\n[TEST 7] Testing Booking Cancellation (SP_CANCEL_BOOKING)...")
        booking_id = self.__class__.created_booking_id
        # Cancel booking as customer 2
        ok, msg = BookingService.cancel_booking(booking_id, customer_id=2)
        self.assertTrue(ok, f"Cancellation failed: {msg}")

        # Verify status is CANCELLED
        details = BookingService.get_booking_details(booking_id)
        status = details["status"] if "status" in details else details["Booking_Status"]
        self.assertEqual(status, "CANCELLED")
        print(f"  Booking status updated to CANCELLED (Historical row preserved).")

    def test_08_admin_dashboard_reports(self):
        print("\n[TEST 8] Testing Analytical Reports & KPIs...")
        summary = ReportService.get_dashboard_summary()
        self.assertGreater(summary["rooms"]["total_rooms"], 0)
        self.assertGreater(summary["total_collected"], 0)

        rev_report = ReportService.get_revenue_by_month()
        self.assertGreater(len(rev_report), 0)

        popular_rooms = ReportService.get_most_booked_room_types()
        self.assertGreater(len(popular_rooms), 0)
        print("  All Analytical KPI queries and view queries executed successfully.")

if __name__ == "__main__":
    unittest.main()
