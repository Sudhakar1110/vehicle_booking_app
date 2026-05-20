import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {"label": _("Booking ID"), "fieldname": "name", "fieldtype": "Link", "options": "Vehicle Booking Order", "width": 160},
        {"label": _("Customer"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Vehicle"), "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 130},
        {"label": _("Category"), "fieldname": "vehicle_category", "fieldtype": "Link", "options": "Vehicle Category", "width": 130},
        {"label": _("Driver"), "fieldname": "driver_name", "fieldtype": "Data", "width": 120},
        {"label": _("Pickup"), "fieldname": "pickup_location", "fieldtype": "Data", "width": 150},
        {"label": _("Drop"), "fieldname": "drop_location", "fieldtype": "Data", "width": 150},
        {"label": _("Pickup Date"), "fieldname": "pickup_datetime", "fieldtype": "Datetime", "width": 140},
        {"label": _("Status"), "fieldname": "booking_status", "fieldtype": "Data", "width": 120},
        {"label": _("Total Fare"), "fieldname": "total_fare", "fieldtype": "Currency", "width": 120},
        {"label": _("Payment"), "fieldname": "payment_status", "fieldtype": "Data", "width": 110},
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    return frappe.db.sql(f"""
        SELECT
            name, customer_name, vehicle, vehicle_category, driver_name,
            pickup_location, drop_location, pickup_datetime,
            booking_status, total_fare, payment_status
        FROM `tabVehicle Booking Order`
        WHERE docstatus < 2 {conditions}
        ORDER BY creation DESC
        LIMIT 500
    """, filters, as_dict=True)


def get_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += " AND DATE(pickup_datetime) >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND DATE(pickup_datetime) <= %(to_date)s"
    if filters.get("booking_status"):
        conditions += " AND booking_status = %(booking_status)s"
    if filters.get("vehicle_category"):
        conditions += " AND vehicle_category = %(vehicle_category)s"
    return conditions


def get_chart(data):
    status_counts = {}
    for row in data:
        s = row.get("booking_status", "Unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    return {
        "data": {
            "labels": list(status_counts.keys()),
            "datasets": [{"values": list(status_counts.values())}]
        },
        "type": "donut",
        "title": "Bookings by Status"
    }
