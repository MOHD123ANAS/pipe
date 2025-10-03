import frappe
@frappe.whitelist()
def create_sales_order_with_taxes(doc):
    import json
    doc = frappe.parse_json(doc)
    so = frappe.get_doc(doc)
    
    so.insert(ignore_permissions=True)
    so.apply_default_taxes_and_charges()
    so.calculate_taxes_and_totals()
    so.save()
    
    return so.as_dict()
