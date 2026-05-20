import frappe
from frappe.model.document import Document

class VehicleCategory(Document):
    def validate(self):
        if self.base_fare < 0:
            frappe.throw("Base Fare cannot be negative")
        if self.per_km_charge < 0:
            frappe.throw("Per KM Charge cannot be negative")
