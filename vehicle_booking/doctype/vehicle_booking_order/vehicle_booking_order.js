frappe.ui.form.on('Vehicle Booking Order', {
    refresh: function(frm) {
        frm.trigger('add_custom_buttons');
        frm.trigger('set_status_indicator');
    },

    add_custom_buttons: function(frm) {
        if (frm.doc.docstatus === 1) {
            if (frm.doc.booking_status === 'Confirmed') {
                frm.add_custom_button(__('Assign Driver'), function() {
                    frm.trigger('assign_driver_dialog');
                }, __('Actions'));
            }
            if (frm.doc.booking_status === 'Driver Assigned') {
                frm.add_custom_button(__('Start Trip'), function() {
                    frappe.confirm('Start the trip now?', function() {
                        frm.call('start_trip').then(() => frm.reload_doc());
                    });
                }, __('Actions'));
            }
            if (frm.doc.booking_status === 'In Transit') {
                frm.add_custom_button(__('Complete Trip'), function() {
                    frm.trigger('complete_trip_dialog');
                }, __('Actions'));
            }
            if (frm.doc.payment_status !== 'Paid') {
                frm.add_custom_button(__('Record Payment'), function() {
                    frm.trigger('payment_dialog');
                }, __('Actions'));
            }
        }
    },

    assign_driver_dialog: function(frm) {
        let d = new frappe.ui.Dialog({
            title: 'Assign Driver',
            fields: [{
                label: 'Driver', fieldname: 'driver',
                fieldtype: 'Link', options: 'Driver', reqd: 1,
                get_query: function() {
                    return { filters: { status: 'Available' } };
                }
            }],
            primary_action_label: 'Assign',
            primary_action(values) {
                frm.call('assign_driver', { driver: values.driver })
                    .then(() => { frm.reload_doc(); d.hide(); });
            }
        });
        d.show();
    },

    complete_trip_dialog: function(frm) {
        let d = new frappe.ui.Dialog({
            title: 'Complete Trip',
            fields: [
                { label: 'Actual Distance (KM)', fieldname: 'actual_distance', fieldtype: 'Float' },
                { label: 'Customer Rating (1-5)', fieldname: 'rating', fieldtype: 'Int' },
                { label: 'Customer Feedback', fieldname: 'feedback', fieldtype: 'Small Text' }
            ],
            primary_action_label: 'Complete',
            primary_action(values) {
                frm.call('complete_trip', values).then(() => { frm.reload_doc(); d.hide(); });
            }
        });
        d.show();
    },

    payment_dialog: function(frm) {
        let d = new frappe.ui.Dialog({
            title: 'Record Payment',
            fields: [
                { label: 'Amount', fieldname: 'amount', fieldtype: 'Currency', reqd: 1,
                  default: flt(frm.doc.total_fare) - flt(frm.doc.paid_amount) },
                { label: 'Payment Method', fieldname: 'method', fieldtype: 'Select',
                  options: 'Cash\nCard\nUPI\nNet Banking\nWallet', reqd: 1 }
            ],
            primary_action_label: 'Record',
            primary_action(values) {
                frm.call('record_payment', values).then(() => { frm.reload_doc(); d.hide(); });
            }
        });
        d.show();
    },

    vehicle_category: function(frm) {
        if (frm.doc.vehicle_category) {
            frm.trigger('calculate_fare');
            frm.set_query('vehicle', function() {
                return {
                    filters: { vehicle_category: frm.doc.vehicle_category, status: 'Available' }
                };
            });
        }
    },

    estimated_distance: function(frm) { frm.trigger('calculate_fare'); },
    extra_charges: function(frm) { frm.trigger('calculate_fare'); },
    discount_amount: function(frm) { frm.trigger('calculate_fare'); },

    calculate_fare: function(frm) {
        if (!frm.doc.vehicle_category) return;
        frappe.db.get_doc('Vehicle Category', frm.doc.vehicle_category).then(cat => {
            let base = cat.base_fare || 0;
            let dist_charge = (frm.doc.estimated_distance || 0) * (cat.per_km_charge || 0);
            let subtotal = base + dist_charge + (frm.doc.extra_charges || 0) - (frm.doc.discount_amount || 0);
            let tax = subtotal * 0.05;
            frm.set_value('base_fare', base);
            frm.set_value('distance_charge', dist_charge);
            frm.set_value('tax_amount', tax);
            frm.set_value('total_fare', subtotal + tax);
        });
    },

    set_status_indicator: function(frm) {
        const colors = {
            'Draft': 'grey', 'Confirmed': 'blue', 'Driver Assigned': 'orange',
            'In Transit': 'yellow', 'Completed': 'green', 'Cancelled': 'red'
        };
        frm.page.set_indicator(frm.doc.booking_status, colors[frm.doc.booking_status] || 'grey');
    }
});
