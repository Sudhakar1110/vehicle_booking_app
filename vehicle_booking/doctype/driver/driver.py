import frappe
from frappe.model.document import Document

class Driver(Document):
    def validate(self):
        if self.rating and (self.rating < 1 or self.rating > 5):
            frappe.throw("Rating must be between 1 and 5")
        if self.mobile_number:
            import re
            if not re.match(r'^\+?[\d\s\-]{10,15}$', self.mobile_number):
                frappe.throw("Please enter a valid mobile number")

    def update_rating(self, new_rating):
        if self.total_trips:
            self.rating = ((self.rating * self.total_trips) + new_rating) / (self.total_trips + 1)
        else:
            self.rating = new_rating
        self.total_trips = (self.total_trips or 0) + 1
        self.save(ignore_permissions=True)
