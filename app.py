import os
import functools
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from services.auth_service import AuthService
from services.booking_service import BookingService
from services.admin_service import AdminService
from services.report_service import ReportService
from services import semantic_service
from db.connection import db

app = Flask(__name__)
app.config.from_object(Config)

# -----------------------------------------------------------------------------
# AUTHENTICATION & ROLE DECORATORS
# -----------------------------------------------------------------------------
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Authentication required. Please log in."}), 401
            return redirect(url_for("login_page", next=request.url))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Authentication required."}), 401
            return redirect(url_for("login_page", next=request.url))
        if session.get("role") != "ADMIN":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Forbidden. Administrator access required."}), 403
            return render_template("login.html", error="Administrator access required for this module."), 403
        return view(**kwargs)
    return wrapped_view

def _owns_booking_or_admin(booking):
    """
    True if the signed-in user owns this booking, or is an administrator.

    Booking records come back with Oracle-lowercased or SQLite-cased keys, so
    the customer id is read defensively.
    """
    if "user_id" not in session:
        return False
    if session.get("role") == "ADMIN":
        return True

    owner_id = booking.get("customer_id", booking.get("Customer_ID"))
    try:
        return int(owner_id) == int(session["user_id"])
    except (TypeError, ValueError):
        return False

# Context processor for templates
@app.context_processor
def inject_global_template_vars():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
            "role": session.get("role")
        } if "user_id" in session else None,
        "is_admin": session.get("role") == "ADMIN",
        "is_oracle_active": db.is_oracle_active()
    }

# -----------------------------------------------------------------------------
# FRONTEND PAGE ROUTES
# -----------------------------------------------------------------------------
@app.route("/")
def index_page():
    room_types = BookingService.get_room_types()
    testimonials = BookingService.get_testimonials()
    services = BookingService.get_services()
    return render_template("index.html", room_types=room_types, testimonials=testimonials, services=services)

@app.route("/rooms")
def rooms_page():
    room_types = BookingService.get_room_types()
    return render_template("rooms.html", room_types=room_types)

@app.route("/booking")
def booking_page():
    room_types = BookingService.get_room_types()
    services = BookingService.get_services()
    return render_template("booking.html", room_types=room_types, services=services)

@app.route("/my-bookings")
@login_required
def my_bookings_page():
    return render_template("my-bookings.html")

@app.route("/invoice/<int:booking_id>")
@login_required
def invoice_page(booking_id):
    booking = BookingService.get_booking_details(booking_id)
    if not booking:
        return render_template("base.html", error_message=f"Invoice for booking #{booking_id} was not found."), 404

    # An invoice carries the guest's name, email, phone and spend - it must
    # only ever be shown to that guest or to staff. Without this check the
    # booking id in the URL is all anyone needs to read another guest's folio.
    if not _owns_booking_or_admin(booking):
        return render_template("base.html", error_message="You do not have access to this invoice."), 403

    return render_template("invoice.html", booking=booking)

@app.route("/login")
def login_page():
    if "user_id" in session:
        if session.get("role") == "ADMIN":
            return redirect(url_for("admin_dashboard_page"))
        return redirect(url_for("my_bookings_page"))
    return render_template("login.html")

@app.route("/register")
def register_page():
    if "user_id" in session:
        return redirect(url_for("my_bookings_page"))
    return render_template("register.html")

@app.route("/smart-search")
def smart_search_page():
    """Guest-facing concierge search: find a room, read relevant reviews."""
    return render_template("smart-search.html")

# -----------------------------------------------------------------------------
# ADMIN PORTAL PAGE ROUTES
# -----------------------------------------------------------------------------
@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard_page():
    return render_template("admin-dashboard.html")

@app.route("/admin/rooms")
@admin_required
def admin_rooms_page():
    return render_template("admin-rooms.html")

@app.route("/admin/bookings")
@admin_required
def admin_bookings_page():
    return render_template("admin-bookings.html")

@app.route("/admin/customers")
@admin_required
def admin_customers_page():
    return render_template("admin-customers.html")

@app.route("/admin/services")
@admin_required
def admin_services_page():
    return render_template("admin-services.html")

@app.route("/admin/reports")
@admin_required
def admin_reports_page():
    return render_template("admin-reports.html")

@app.route("/admin/search-insights")
@admin_required
def admin_search_insights_page():
    """Internal tool: compares relational and vector search on the same query."""
    return render_template("admin-search-insights.html")

# -----------------------------------------------------------------------------
# REST API: AUTHENTICATION
# -----------------------------------------------------------------------------
@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    ok, result = AuthService.register_customer(
        name=data.get("name"),
        phone=data.get("phone"),
        email=data.get("email"),
        password=data.get("password"),
        address=data.get("address", ""),
        dob=data.get("dob")
    )
    if not ok:
        return jsonify({"success": False, "error": result}), 400
    
    # Auto-login newly registered customer
    session["user_id"] = result.get("customer_id") or result.get("Customer_ID")
    session["user_name"] = result.get("name") or result.get("Name")
    session["user_email"] = result.get("email") or result.get("Email")
    session["role"] = result.get("role") or result.get("Role") or "CUSTOMER"
    
    return jsonify({"success": True, "message": "Account created successfully.", "user": result}), 201

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    ok, result = AuthService.authenticate_user(email, password)
    if not ok:
        return jsonify({"success": False, "error": result}), 401

    session["user_id"] = result["customer_id"]
    session["user_name"] = result["name"]
    session["user_email"] = result["email"]
    session["role"] = result["role"]

    return jsonify({"success": True, "message": "Logged in successfully.", "user": result})

@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    if request.method == "GET":
        return redirect(url_for("index_page"))
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/auth/me", methods=["GET"])
def api_me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})
    user = AuthService.get_user_by_id(session["user_id"])
    return jsonify({"authenticated": True, "user": user})

# -----------------------------------------------------------------------------
# REST API: ROOMS & AVAILABILITY
# -----------------------------------------------------------------------------
@app.route("/api/rooms", methods=["GET"])
def api_get_rooms():
    rtid = request.args.get("room_type_id")
    status = request.args.get("status")
    floor = request.args.get("floor")
    max_price = request.args.get("max_price")
    rooms = BookingService.get_all_rooms(room_type_id=rtid, status=status, floor=floor, max_price=max_price)
    return jsonify({"success": True, "count": len(rooms), "rooms": rooms})

@app.route("/api/rooms/available", methods=["GET"])
def api_search_available_rooms():
    check_in = request.args.get("check_in")
    check_out = request.args.get("check_out")
    guests = request.args.get("guests", 1)
    rtid = request.args.get("room_type_id")

    if not check_in or not check_out:
        return jsonify({"success": False, "error": "check_in and check_out query parameters are mandatory."}), 400

    ok, result = BookingService.search_available_rooms(
        check_in_str=check_in,
        check_out_str=check_out,
        guests=guests,
        room_type_id=rtid
    )
    if not ok:
        return jsonify({"success": False, "error": result}), 400

    return jsonify({"success": True, "data": result})

@app.route("/api/room-types", methods=["GET"])
def api_room_types():
    types = BookingService.get_room_types()
    return jsonify({"success": True, "room_types": types})

# -----------------------------------------------------------------------------
# REST API: BOOKINGS & INVOICES
# -----------------------------------------------------------------------------
@app.route("/api/bookings", methods=["POST"])
@login_required
def api_create_booking():
    data = request.get_json() or {}

    # Identity comes from the signed-in session ONLY. Taking customer_id from
    # the request body (as this used to) let any caller book, and be billed,
    # as any other customer simply by changing a number in the JSON.
    customer_id = session["user_id"]

    room_id = data.get("room_id")
    check_in = data.get("check_in")
    check_out = data.get("check_out")
    no_of_guests = data.get("no_of_guests", 1)
    selected_services = data.get("services", [])
    payment_mode = data.get("payment_mode", "CREDIT_CARD")

    if not room_id or not check_in or not check_out:
        return jsonify({"success": False, "error": "room_id, check_in, and check_out are required."}), 400

    if not isinstance(selected_services, list):
        selected_services = []

    # Booking + services + invoice + payment run as ONE database transaction
    ok, res = BookingService.create_full_booking(
        customer_id=customer_id,
        room_id=room_id,
        check_in_str=check_in,
        check_out_str=check_out,
        no_of_guests=no_of_guests,
        services=selected_services,
        payment_mode=payment_mode
    )
    if not ok:
        return jsonify({"success": False, "error": res}), 400

    booking_id = res

    return jsonify({
        "success": True,
        "message": f"Reservation #{booking_id} confirmed successfully!",
        "booking_id": booking_id,
        "invoice_url": f"/invoice/{booking_id}"
    }), 201

@app.route("/api/bookings/<int:booking_id>", methods=["GET"])
@login_required
def api_get_booking(booking_id):
    booking = BookingService.get_booking_details(booking_id)
    if not booking:
        return jsonify({"success": False, "error": "Booking not found."}), 404
    if not _owns_booking_or_admin(booking):
        return jsonify({"success": False, "error": "Forbidden."}), 403
    return jsonify({"success": True, "booking": booking})

@app.route("/api/my-bookings", methods=["GET"])
@login_required
def api_my_bookings():
    bookings = BookingService.get_customer_bookings(session["user_id"])
    return jsonify({"success": True, "bookings": bookings})

@app.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def api_cancel_booking(booking_id):
    # Customer can only cancel their own, Admin can cancel any (pass 0 for admin override)
    caller_id = 0 if session.get("role") == "ADMIN" else session["user_id"]
    ok, msg = BookingService.cancel_booking(booking_id, caller_id)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/bookings/<int:booking_id>/services", methods=["POST"])
@login_required
def api_add_service(booking_id):
    data = request.get_json() or {}
    srv_id = data.get("service_id")
    qty = data.get("quantity", 1)
    if not srv_id:
        return jsonify({"success": False, "error": "service_id is required."}), 400

    # Adding a service bills the booking, so only its owner (or staff) may do it
    booking = BookingService.get_booking_details(booking_id)
    if not booking:
        return jsonify({"success": False, "error": "Booking not found."}), 404
    if not _owns_booking_or_admin(booking):
        return jsonify({"success": False, "error": "Forbidden."}), 403
    ok, msg = BookingService.add_booking_service(booking_id, srv_id, qty)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/payments", methods=["POST"])
@login_required
def api_record_payment():
    data = request.get_json() or {}
    bid = data.get("booking_id")
    amt = data.get("amount")
    mode = data.get("payment_mode", "CREDIT_CARD")
    if not bid or amt is None:
        return jsonify({"success": False, "error": "booking_id and amount are required."}), 400

    # This endpoint writes a financial record; it previously required no login
    # at all, so anyone could post payments against any booking.
    booking = BookingService.get_booking_details(bid)
    if not booking:
        return jsonify({"success": False, "error": "Booking not found."}), 404
    if not _owns_booking_or_admin(booking):
        return jsonify({"success": False, "error": "Forbidden."}), 403

    ok, msg = BookingService.record_payment(bid, amt, mode)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/invoices/<int:booking_id>", methods=["GET"])
@login_required
def api_get_invoice(booking_id):
    booking = BookingService.get_booking_details(booking_id)
    if not booking or not booking.get("invoice"):
        return jsonify({"success": False, "error": "Invoice not found."}), 404
    if not _owns_booking_or_admin(booking):
        return jsonify({"success": False, "error": "Forbidden."}), 403
    return jsonify({"success": True, "invoice": booking["invoice"], "booking": booking})

# -----------------------------------------------------------------------------
# REST API: SERVICES & REVIEWS
# -----------------------------------------------------------------------------
@app.route("/api/services", methods=["GET"])
def api_get_services():
    services = BookingService.get_services()
    return jsonify({"success": True, "services": services})

@app.route("/api/feedback", methods=["POST"])
@login_required
def api_submit_feedback():
    data = request.get_json() or {}

    # Identity from the session only - accepting customer_id from the body
    # allowed reviews to be posted in another guest's name.
    cid = session["user_id"]
    
    bid = data.get("booking_id")
    rating = data.get("rating")
    comments = data.get("comments")
    
    ok, msg = BookingService.submit_feedback(cid, bid, rating, comments)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/testimonials", methods=["GET"])
def api_testimonials():
    tests = BookingService.get_testimonials()
    return jsonify({"success": True, "testimonials": tests})

# -----------------------------------------------------------------------------
# REST API: GUEST SEARCH
# Backed by the Chroma index built by build_vector_index.py. Guest-facing
# responses deliberately expose no index internals or scoring.
# -----------------------------------------------------------------------------
SEARCH_UNAVAILABLE = "Search is temporarily unavailable."

@app.route("/api/semantic/reviews", methods=["GET"])
def api_semantic_reviews():
    """Finds guest reviews relevant to a question."""
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"success": False, "error": "A search term is required."}), 400

    limit = min(int(request.args.get("limit", 5)), 20)
    try:
        results = semantic_service.search_reviews(query, n_results=limit)
    except Exception:
        app.logger.exception("Review search failed")
        return jsonify({"success": False, "error": SEARCH_UNAVAILABLE}), 503

    return jsonify({"success": True, "query": query, "results": results})

@app.route("/api/semantic/rooms", methods=["GET"])
def api_semantic_rooms():
    """Matches a free-text description of an ideal stay to room categories."""
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"success": False, "error": "A search term is required."}), 400

    limit = min(int(request.args.get("limit", 3)), 10)
    max_price = request.args.get("max_price")
    try:
        matches = semantic_service.search_room_types(
            query, n_results=limit,
            max_price=float(max_price) if max_price else None
        )
    except Exception:
        app.logger.exception("Room match failed")
        return jsonify({"success": False, "error": SEARCH_UNAVAILABLE}), 503

    return jsonify({"success": True, "query": query, "matches": matches})

# -----------------------------------------------------------------------------
# REST API: SEARCH ADMINISTRATION (staff only)
# -----------------------------------------------------------------------------
@app.route("/api/admin/search/status", methods=["GET"])
@admin_required
def api_admin_search_status():
    return jsonify({"success": True, "status": semantic_service.index_status()})

@app.route("/api/admin/search/compare", methods=["GET"])
@admin_required
def api_admin_search_compare():
    """
    Runs one query two ways - relational LIKE and vector similarity - and
    returns both result sets for internal comparison.
    """
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"success": False, "error": "A search term is required."}), 400

    limit = min(int(request.args.get("limit", 5)), 20)
    try:
        semantic = semantic_service.search_reviews(query, n_results=limit)
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc)}), 503
    except Exception:
        return jsonify({
            "success": False,
            "error": "Vector index not built. Run: python build_vector_index.py"
        }), 503

    return jsonify({
        "success": True,
        "query": query,
        "semantic_results": semantic,
        "keyword_results": semantic_service.keyword_search_reviews(query, n_results=limit),
    })

@app.route("/api/admin/search/rebuild", methods=["POST"])
@admin_required
def api_admin_search_rebuild():
    """Rebuilds the search index from current Oracle data."""
    try:
        counts = semantic_service.rebuild_all()
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    return jsonify({
        "success": True,
        "message": f"Search index rebuilt: {sum(counts.values())} documents.",
        "counts": counts,
    })

# -----------------------------------------------------------------------------
# REST API: ADMIN OPERATIONS
# -----------------------------------------------------------------------------
@app.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def api_admin_dashboard():
    summary = ReportService.get_dashboard_summary()
    recent_bookings = AdminService.get_all_bookings()[:6]
    return jsonify({"success": True, "summary": summary, "recent_bookings": recent_bookings})

@app.route("/api/admin/room-types", methods=["GET", "POST"])
@admin_required
def api_admin_room_types():
    if request.method == "POST":
        data = request.get_json() or {}
        ok, msg = AdminService.create_room_type(
            name=data.get("type_name"),
            description=data.get("description"),
            base_price=data.get("base_price"),
            max_occupancy=data.get("max_occupancy"),
            amenities=data.get("amenities", ""),
            image_url=data.get("image_url")
        )
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "message": msg}), 201
    types = AdminService.get_all_room_types()
    return jsonify({"success": True, "room_types": types})

@app.route("/api/admin/room-types/<int:rtid>", methods=["PUT", "DELETE"])
@admin_required
def api_admin_room_type_detail(rtid):
    if request.method == "DELETE":
        ok, msg = AdminService.delete_room_type(rtid)
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "message": msg})
    
    data = request.get_json() or {}
    ok, msg = AdminService.update_room_type(
        rtid=rtid,
        name=data.get("type_name"),
        description=data.get("description"),
        base_price=data.get("base_price"),
        max_occupancy=data.get("max_occupancy"),
        amenities=data.get("amenities", ""),
        image_url=data.get("image_url")
    )
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/admin/rooms", methods=["GET", "POST"])
@admin_required
def api_admin_rooms():
    if request.method == "POST":
        data = request.get_json() or {}
        ok, msg = AdminService.create_room(
            room_number=data.get("room_number"),
            floor=data.get("floor"),
            room_type_id=data.get("room_type_id"),
            price_per_night=data.get("price_per_night"),
            status=data.get("status", "AVAILABLE")
        )
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "message": msg}), 201
    rooms = BookingService.get_all_rooms()
    return jsonify({"success": True, "rooms": rooms})

@app.route("/api/admin/rooms/<int:rid>", methods=["PUT", "DELETE"])
@admin_required
def api_admin_room_detail(rid):
    if request.method == "DELETE":
        ok, msg = AdminService.delete_room(rid)
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "message": msg})

    data = request.get_json() or {}
    ok, msg = AdminService.update_room(
        room_id=rid,
        room_number=data.get("room_number"),
        floor=data.get("floor"),
        room_type_id=data.get("room_type_id"),
        price_per_night=data.get("price_per_night"),
        status=data.get("status")
    )
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/admin/bookings", methods=["GET"])
@admin_required
def api_admin_bookings():
    status = request.args.get("status")
    bookings = AdminService.get_all_bookings(status=status)
    return jsonify({"success": True, "bookings": bookings})

@app.route("/api/admin/bookings/<int:bid>/status", methods=["PUT"])
@admin_required
def api_admin_update_booking_status(bid):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"success": False, "error": "status is required."}), 400
    ok, msg = AdminService.update_booking_status(bid, new_status)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/admin/customers", methods=["GET"])
@admin_required
def api_admin_customers():
    customers = AdminService.get_all_customers()
    return jsonify({"success": True, "customers": customers})

@app.route("/api/admin/employees", methods=["GET", "POST"])
@admin_required
def api_admin_employees():
    if request.method == "POST":
        data = request.get_json() or {}
        ok, msg = AdminService.create_employee(
            name=data.get("name"),
            designation=data.get("designation"),
            phone=data.get("phone"),
            email=data.get("email"),
            salary=data.get("salary")
        )
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "message": msg}), 201
    employees = AdminService.get_all_employees()
    return jsonify({"success": True, "employees": employees})

@app.route("/api/admin/services", methods=["POST"])
@admin_required
def api_admin_create_service():
    data = request.get_json() or {}
    ok, msg = AdminService.create_service(
        name=data.get("service_name"),
        category=data.get("category"),
        price=data.get("price")
    )
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg}), 201

@app.route("/api/admin/services/<int:sid>", methods=["DELETE"])
@admin_required
def api_admin_delete_service(sid):
    ok, msg = AdminService.delete_service(sid)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})

@app.route("/api/admin/reports/<report_type>", methods=["GET"])
@admin_required
def api_admin_reports(report_type):
    if report_type == "monthly-revenue":
        data = ReportService.get_revenue_by_month()
    elif report_type == "popular-rooms":
        data = ReportService.get_most_booked_room_types()
    elif report_type == "service-usage":
        data = ReportService.get_service_usage()
    elif report_type == "top-customers":
        data = ReportService.get_top_customers()
    elif report_type == "occupancy-rates":
        data = ReportService.get_room_occupancy_rates()
    else:
        return jsonify({"success": False, "error": f"Unknown report type '{report_type}'."}), 404
    return jsonify({"success": True, "report_type": report_type, "data": data})

# -----------------------------------------------------------------------------
# ERROR HANDLERS
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404
    return render_template("base.html", error_message="The page you requested does not exist."), 404

@app.errorhandler(500)
def handle_500(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500
    return render_template("base.html", error_message="An internal server error occurred."), 500

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
