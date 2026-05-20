import frappe
from frappe import _
from frappe.utils import flt, now_datetime, add_days, today


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user) or "Vehicle Booking Manager" in frappe.get_roles(user):
        return None
    return f"""(`tabVehicle Booking Order`.owner = '{user}' or `tabVehicle Booking Order`.customer_email = '{user}')"""


def on_booking_submit(doc, method):
    send_confirmation_email(doc)
    frappe.publish_realtime("new_booking", {"booking": doc.name}, user="Administrator")


def on_booking_cancel(doc, method):
    send_cancellation_email(doc)


def send_confirmation_email(doc):
    if not doc.customer_email:
        return
    try:
        frappe.sendmail(
            recipients=[doc.customer_email],
            subject=f"Booking Confirmed - {doc.name}",
            message=f"""
            <h2>Your Vehicle Booking is Confirmed!</h2>
            <p>Dear {doc.customer_name},</p>
            <p>Your booking <strong>{doc.name}</strong> has been confirmed.</p>
            <table border="1" cellpadding="8" style="border-collapse:collapse;">
                <tr><td><strong>Pickup Location</strong></td><td>{doc.pickup_location}</td></tr>
                <tr><td><strong>Drop Location</strong></td><td>{doc.drop_location}</td></tr>
                <tr><td><strong>Pickup Date & Time</strong></td><td>{doc.pickup_datetime}</td></tr>
                <tr><td><strong>Total Fare</strong></td><td>₹ {doc.total_fare}</td></tr>
            </table>
            <p>Thank you for choosing us!</p>
            """
        )
    except Exception as e:
        frappe.log_error(str(e), "Booking Confirmation Email Failed")


def send_cancellation_email(doc):
    if not doc.customer_email:
        return
    try:
        frappe.sendmail(
            recipients=[doc.customer_email],
            subject=f"Booking Cancelled - {doc.name}",
            message=f"""
            <h2>Booking Cancelled</h2>
            <p>Dear {doc.customer_name},</p>
            <p>Your booking <strong>{doc.name}</strong> has been cancelled.</p>
            <p>Reason: {doc.cancellation_reason or 'Not specified'}</p>
            <p>If you have any questions, please contact us.</p>
            """
        )
    except Exception as e:
        frappe.log_error(str(e), "Booking Cancellation Email Failed")


def send_booking_reminders():
    """Send reminder emails 24 hours before pickup"""
    from frappe.utils import add_hours, get_datetime
    reminder_time = add_hours(now_datetime(), 24)
    bookings = frappe.get_all(
        "Vehicle Booking Order",
        filters={
            "booking_status": ["in", ["Confirmed", "Driver Assigned"]],
            "pickup_datetime": ["between", [now_datetime(), reminder_time]],
            "customer_email": ["!=", ""]
        },
        fields=["name", "customer_name", "customer_email", "pickup_datetime", "pickup_location", "total_fare"]
    )
    for booking in bookings:
        try:
            frappe.sendmail(
                recipients=[booking.customer_email],
                subject=f"Reminder: Your trip tomorrow - {booking.name}",
                message=f"""
                <p>Dear {booking.customer_name},</p>
                <p>This is a reminder for your upcoming trip tomorrow.</p>
                <p><strong>Pickup:</strong> {booking.pickup_location} at {booking.pickup_datetime}</p>
                """
            )
        except Exception:
            pass


def auto_complete_bookings():
    """Auto-complete bookings that have passed drop time"""
    from frappe.utils import get_datetime
    bookings = frappe.get_all(
        "Vehicle Booking Order",
        filters={
            "booking_status": "In Transit",
            "expected_drop_datetime": ["<", now_datetime()]
        },
        fields=["name"]
    )
    for b in bookings:
        try:
            doc = frappe.get_doc("Vehicle Booking Order", b.name)
            doc.complete_trip()
        except Exception as e:
            frappe.log_error(str(e), f"Auto Complete Failed: {b.name}")


def check_vehicle_availability():
    """Hourly check to update vehicle statuses"""
    pass  # Can be extended for GPS/IoT integration


@frappe.whitelist(allow_guest=True)
def get_available_vehicles(pickup_datetime, vehicle_category=None):
    """Get vehicles available for a given time slot"""
    filters = {"status": "Available"}
    if vehicle_category:
        filters["vehicle_category"] = vehicle_category
    vehicles = frappe.get_all(
        "Vehicle",
        filters=filters,
        fields=["name", "vehicle_name", "license_plate", "make", "model",
                "year", "color", "vehicle_category", "vehicle_image"]
    )
    return vehicles


@frappe.whitelist(allow_guest=True)
def get_vehicle_categories():
    """Get all active vehicle categories for portal"""
    categories = frappe.get_all(
        "Vehicle Category",
        filters={"is_active": 1},
        fields=["name", "category_name", "description", "image", "base_fare",
                "per_km_charge", "max_passengers", "ac_available", "features"]
    )
    return categories


@frappe.whitelist(allow_guest=True)
def estimate_fare(vehicle_category, distance=0, extra_charges=0):
    """Estimate fare for a booking"""
    if not vehicle_category:
        return {}
    cat = frappe.get_doc("Vehicle Category", vehicle_category)
    base = flt(cat.base_fare)
    dist_charge = flt(distance) * flt(cat.per_km_charge)
    subtotal = base + dist_charge + flt(extra_charges)
    tax = subtotal * 0.05
    return {
        "base_fare": base,
        "distance_charge": dist_charge,
        "tax_amount": tax,
        "total_fare": subtotal + tax
    }


@frappe.whitelist(allow_guest=True)
def create_booking(customer_name, customer_mobile, customer_email,
                   pickup_location, drop_location, pickup_datetime,
                   vehicle_category, no_of_passengers=1,
                   trip_type="One Way", estimated_distance=0, special_requirements=""):
    """Create a new vehicle booking from portal"""
    try:
        # Find or create customer
        customer = None
        if customer_email:
            existing = frappe.db.get_value("Customer", {"email_id": customer_email}, "name")
            if existing:
                customer = existing
            elif frappe.db.exists("Contact", {"email_id": customer_email}):
                contact = frappe.get_doc("Contact", {"email_id": customer_email})
                if contact.links:
                    for link in contact.links:
                        if link.link_doctype == "Customer":
                            customer = link.link_name
                            break

        doc = frappe.new_doc("Vehicle Booking Order")
        doc.customer = customer
        doc.customer_name = customer_name
        doc.customer_mobile = customer_mobile
        doc.customer_email = customer_email
        doc.pickup_location = pickup_location
        doc.drop_location = drop_location
        doc.pickup_datetime = pickup_datetime
        doc.vehicle_category = vehicle_category
        doc.no_of_passengers = int(no_of_passengers)
        doc.trip_type = trip_type
        doc.estimated_distance = flt(estimated_distance)
        doc.special_requirements = special_requirements
        doc.booking_date = today()
        doc.booking_status = "Draft"
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "booking_id": doc.name, "total_fare": doc.total_fare}
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Booking Creation Failed")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_booking_status(booking_id):
    """Track booking status from portal"""
    if not frappe.db.exists("Vehicle Booking Order", booking_id):
        return {"error": "Booking not found"}
    doc = frappe.get_doc("Vehicle Booking Order", booking_id)
    return {
        "booking_id": doc.name,
        "status": doc.booking_status,
        "payment_status": doc.payment_status,
        "driver_name": doc.driver_name,
        "driver_mobile": doc.driver_mobile,
        "vehicle": doc.vehicle,
        "total_fare": doc.total_fare,
        "paid_amount": doc.paid_amount
    }


@frappe.whitelist(allow_guest=True)
def submit_feedback(booking_id, rating, feedback):
    """Submit feedback for a completed booking"""
    doc = frappe.get_doc("Vehicle Booking Order", booking_id)
    if doc.booking_status != "Completed":
        return {"success": False, "error": "Feedback can only be submitted for completed bookings"}
    doc.customer_rating = int(rating)
    doc.customer_feedback = feedback
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True}
