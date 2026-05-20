frappe.query_reports["Vehicle Booking Summary"] = {
    filters: [
        {
            fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", default: frappe.datetime.get_today() },
        {
            fieldname: "booking_status", label: __("Status"), fieldtype: "Select",
            options: "\nDraft\nConfirmed\nDriver Assigned\nIn Transit\nCompleted\nCancelled"
        },
        { fieldname: "vehicle_category", label: __("Vehicle Category"), fieldtype: "Link", options: "Vehicle Category" }
    ]
};
