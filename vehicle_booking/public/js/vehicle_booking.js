frappe.provide('vehicle_booking');
vehicle_booking.utils = {
    format_status: function(status) {
        const colors = { 'Draft': 'grey', 'Confirmed': 'blue', 'In Transit': 'orange', 'Completed': 'green', 'Cancelled': 'red' };
        return colors[status] || 'grey';
    }
};
