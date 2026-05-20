import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, getdate

class VehicleBookingOrder(Document):

    def validate(self):
        self.validate_dates()
        self.validate_passenger_count()
        self.calculate_fare()

    def validate_dates(self):
        from frappe.utils import get_datetime
        if self.pickup_datetime and get_datetime(self.pickup_datetime) < get_datetime(now_datetime()):
            frappe.throw("Pickup date/time cannot be in the past")
        if self.expected_drop_datetime and self.pickup_datetime:
            if get_datetime(self.expected_drop_datetime) <= get_datetime(self.pickup_datetime):
                frappe.throw("Expected drop time must be after pickup time")

    def validate_passenger_count(self):
        if self.vehicle and self.no_of_passengers:
            vehicle = frappe.get_doc("Vehicle", self.vehicle)
            category = frappe.get_doc("Vehicle Category", vehicle.vehicle_category)
            if self.no_of_passengers > category.max_passengers:
                frappe.throw(f"This vehicle can carry max {category.max_passengers} passengers")

    def calculate_fare(self):
        if not self.vehicle_category:
            return
        category = frappe.get_doc("Vehicle Category", self.vehicle_category)
        self.base_fare = flt(category.base_fare)
        if self.estimated_distance and category.per_km_charge:
            self.distance_charge = flt(self.estimated_distance) * flt(category.per_km_charge)
        else:
            self.distance_charge = 0
        subtotal = self.base_fare + flt(self.distance_charge) + flt(self.extra_charges) - flt(self.discount_amount)
        self.tax_amount = flt(subtotal * 0.05)  # 5% GST
        self.total_fare = subtotal + self.tax_amount

    def before_submit(self):
        if self.booking_status not in ("Confirmed", "Driver Assigned"):
            self.booking_status = "Confirmed"
        if not self.vehicle:
            frappe.throw("Please assign a vehicle before confirming booking")
        # Mark vehicle as booked
        frappe.db.set_value("Vehicle", self.vehicle, "status", "Booked")

    def on_cancel(self):
        self.booking_status = "Cancelled"
        if self.vehicle:
            frappe.db.set_value("Vehicle", self.vehicle, "status", "Available")
        if self.driver:
            frappe.db.set_value("Driver", self.driver, "status", "Available")

    @frappe.whitelist()
    def assign_driver(self, driver):
        self.driver = driver
        self.booking_status = "Driver Assigned"
        frappe.db.set_value("Driver", driver, "status", "On Trip")
        self.save()
        frappe.msgprint(f"Driver assigned successfully")

    @frappe.whitelist()
    def start_trip(self):
        self.booking_status = "In Transit"
        self.actual_pickup_time = now_datetime()
        self.save()

    @frappe.whitelist()
    def complete_trip(self, actual_distance=None, feedback=None, rating=None):
        self.booking_status = "Completed"
        self.actual_drop_time = now_datetime()
        if actual_distance:
            self.actual_distance = actual_distance
        if feedback:
            self.customer_feedback = feedback
        if rating:
            self.customer_rating = int(rating)
            # Update driver rating
            if self.driver:
                driver_doc = frappe.get_doc("Driver", self.driver)
                driver_doc.update_rating(int(rating))
        # Free up vehicle and driver
        if self.vehicle:
            frappe.db.set_value("Vehicle", self.vehicle, "status", "Available")
        if self.driver:
            frappe.db.set_value("Driver", self.driver, "status", "Available")
        self.save()
        frappe.msgprint("Trip completed successfully!")

    @frappe.whitelist()
    def record_payment(self, amount, method):
        self.paid_amount = flt(self.paid_amount) + flt(amount)
        self.payment_method = method
        if self.paid_amount >= self.total_fare:
            self.payment_status = "Paid"
        elif self.paid_amount > 0:
            self.payment_status = "Partially Paid"
        self.save()
        # Create Payment Entry in ERPNext
        self.create_payment_entry(amount, method)

    def create_payment_entry(self, amount, method):
        try:
            company = frappe.defaults.get_defaults().get("company")
            if not company:
                return
            pe = frappe.new_doc("Payment Entry")
            pe.payment_type = "Receive"
            pe.party_type = "Customer"
            pe.party = self.customer
            pe.party_name = self.customer_name
            pe.paid_amount = flt(amount)
            pe.received_amount = flt(amount)
            pe.reference_no = self.name
            pe.reference_date = getdate()
            pe.company = company
            pe.mode_of_payment = method
            pe.remarks = f"Payment for Vehicle Booking {self.name}"
            pe.insert(ignore_permissions=True)
            frappe.msgprint(f"Payment Entry {pe.name} created")
        except Exception as e:
            frappe.log_error(str(e), "Payment Entry Creation Failed")
