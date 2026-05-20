# Vehicle Booking App

A complete Online Vehicle Booking Application built on **Frappe Framework** and **ERPNext v15**.

## Features
- Vehicle management (categories, fleet)
- Driver management
- Online booking portal (customer-facing)
- Booking order lifecycle (Draft → Confirmed → In Transit → Completed)
- Payment integration via ERPNext Payment Entry
- Reports & dashboards

## Installation

```bash
# From your bench directory
bench get-app https://github.com/yourorg/vehicle_booking
bench --site yoursite.com install-app vehicle_booking
bench --site yoursite.com migrate
```

## Requirements
- Frappe v15
- ERPNext v15
- Python 3.10+

## License
MIT
