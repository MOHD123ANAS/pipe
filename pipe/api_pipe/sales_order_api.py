import frappe
from frappe import _
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from erpnext.controllers.accounts_controller import get_taxes_and_charges

@frappe.whitelist()
def sales_o(**kwargs):
    data = frappe._dict(kwargs)
    doc = frappe.new_doc("Sales Order")

    
    doc.customer = data.get("customer")
    doc.company = data.get("company") or frappe.defaults.get_user_default("Company")
    doc.transaction_date = frappe.utils.nowdate()
    doc.delivery_date = data.get("delivery_date") or frappe.utils.add_days(frappe.utils.nowdate(), 2)
    doc.currency = data.get("currency", "INR")
    doc.selling_price_list = data.get("selling_price_list", "Standard Selling")
    doc.tax_category = data.get("tax_category") or "In-State"
    doc.taxes_and_charges = data.get("taxes_and_charges")
    doc.disable_rounded_total = 1
    doc.supplier=data.get("supplier")
    doc.mode_of_payment=data.get("mode_of_payment")

    
    doc.shipping_address_name = data.get("shipping_address_name")
    doc.dispatch_address_name = data.get("dispatch_address_name")

    
    items = data.get("items")
    if not items:
        frappe.throw(_("At least one item is required"))

    for item in items:
        doc.append("items", {
            "item_code": item.get("item_code"),
            "qty": item.get("qty", 1),
            "rate": item.get("rate"),
            "delivered_by_supplier": item.get("delivered_by_supplier", 0),
            "supplier": item.get("supplier"),
            "item_tax_template": item.get("item_tax_template")
        })

    
    customer_gst_category = frappe.db.get_value("Customer", doc.customer, "gst_category")
    if customer_gst_category == "Unregistered":
        doc.gst_treatment = "Unregistered"
    elif customer_gst_category == "Registered Regular":
        doc.gst_treatment = "Registered Regular"
    else:
        doc.gst_treatment = customer_gst_category or "Unregistered"

    
    if doc.taxes_and_charges:
        taxes_list = get_taxes_and_charges(
            master_doctype="Sales Taxes and Charges Template",
            master_name=doc.taxes_and_charges
        )
        if isinstance(taxes_list, dict) and taxes_list.get("taxes"):
            for tax in taxes_list["taxes"]:
                doc.append("taxes", tax)

    
    doc.run_method("set_missing_values")
    calculate_taxes_and_totals(doc)

    
    doc.insert(ignore_permissions=True)

    
    full_doc = frappe.get_doc("Sales Order", doc.name)
    return full_doc.as_dict()
