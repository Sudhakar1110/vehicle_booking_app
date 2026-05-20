import frappe
from frappe.model.document import Document
from frappe.utils import today

class Vehicle(Document):
    def validate(self):
        self.validate_license_plate()
        self.check_expiry_alerts()

    def validate_license_plate(self):
        self.license_plate = self.license_plate.strip().upper()

    def check_expiry_alerts(self):
        from frappe.utils import getdate, add_days
        today_date = getdate(today())
        if self.insurance_expiry and getdate(self.insurance_expiry) < add_days(today_date, 30):
            frappe.msgprint(f"Insurance for {self.vehicle_name} expires soon: {self.insurance_expiry}", alert=True, indicator="orange")
        if self.pollution_expiry and getdate(self.pollution_expiry) < add_days(today_date, 30):
            frappe.msgprint(f"Pollution certificate for {self.vehicle_name} expires soon: {self.pollution_expiry}", alert=True, indicator="orange")

    def on_update(self):
        frappe.cache().delete_key("available_vehicles")
