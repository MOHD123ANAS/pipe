import frappe

@frappe.whitelist()
def counting_sales_order():
    count = frappe.db.count("Sales Order")
    return count