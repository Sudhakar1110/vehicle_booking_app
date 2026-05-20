app_name = "vehicle_booking"
app_title = "Vehicle Booking"
app_publisher = "Your Company"
app_description = "Online Vehicle Booking Application"
app_email = "info@yourcompany.com"
app_license = "MIT"
app_version = "1.0.0"

# Required Apps
required_apps = ["erpnext"]

# Includes in <head>
app_include_css = ["/assets/vehicle_booking/css/vehicle_booking.css"]
app_include_js = ["/assets/vehicle_booking/js/vehicle_booking.js"]

# Web Include
web_include_css = ["/assets/vehicle_booking/css/portal.css"]
web_include_js = ["/assets/vehicle_booking/js/portal.js"]

# Website Route Rules
website_route_rules = [
    {"from_route": "/vehicle-booking/<path:name>", "to_route": "vehicle_booking_detail"},
]

# Document Events
doc_events = {
    "Vehicle Booking Order": {
        "on_submit": "vehicle_booking.api.booking.on_booking_submit",
        "on_cancel": "vehicle_booking.api.booking.on_booking_cancel",
    }
}

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "vehicle_booking.api.booking.send_booking_reminders",
        "vehicle_booking.api.booking.auto_complete_bookings",
    ],
    "hourly": [
        "vehicle_booking.api.booking.check_vehicle_availability",
    ],
}

# Permissions
permission_query_conditions = {
    "Vehicle Booking Order": "vehicle_booking.api.booking.get_permission_query_conditions",
}

# Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["dt", "in", ["Customer", "Vehicle Booking Order"]]]
    },
    {"doctype": "Vehicle Category"},
]

# Boot Session
boot_session = "vehicle_booking.api.boot.boot_session"
