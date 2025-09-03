import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def create_customer_with_address(data: dict = None):

    import json

    if isinstance(data, str):
        data = json.loads(data)

    customer_data = data.get("customer")
    address_data = data.get("address")

    if not customer_data:
        frappe.throw(_("Customer data is required"))
    if not address_data:
        frappe.throw(_("Address data is required"))

    try:
        
        customer = frappe.get_doc({
            "doctype": "Customer",
            **customer_data
        })
        customer.insert(ignore_permissions=True)

        
        address = frappe.get_doc({
            "doctype": "Address",
            **address_data,
            "links": [
                {
                    "link_doctype": "Customer",
                    "link_name": customer.name
                }
            ]
        })
        address.insert(ignore_permissions=True)

        frappe.db.commit()

        return {
            "customer": customer.as_dict(),
            "address": address.as_dict()
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.throw(("Error creating customer and address: {0}").format(str(e)))