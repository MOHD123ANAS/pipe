import frappe

@frappe.whitelist()
def get_all_supplier_addresses():
    """
    Return all addresses linked to any Supplier (is_partner=1)
    in a single JSON response.
    """
    addresses = frappe.db.sql("""
        SELECT 
            a.name,
            a.address_title,
            a.gstin,
            a.address_line1,
            a.address_line2,
            a.city,
            a.state,
            a.country,
            a.pincode,
            a.is_partner,
            dl.link_name AS supplier_name
        FROM `tabAddress` a
        JOIN `tabDynamic Link` dl ON dl.parent = a.name
        WHERE dl.link_doctype = 'Supplier'
          AND a.is_partner = 1
    """, as_dict=True)

    return addresses
