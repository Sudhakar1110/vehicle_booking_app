import frappe

def boot_session(bootinfo):
    bootinfo.vehicle_booking_config = {
        "app_name": "Vehicle Booking",
        "version": "1.0.0",
    }
