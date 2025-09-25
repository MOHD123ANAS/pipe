import frappe
from collections import defaultdict

@frappe.whitelist()
def get_suppliers_with_addresses(filter_category=None):

    
    suppliers = frappe.get_all(
        "Supplier",
        filters={"is_partner": 1},
        fields=["name", "supplier_name", "partner_name"]
    )

    
    addresses = frappe.db.sql("""
        SELECT 
            a.name AS address_name,
            a.address_title,
            a.gstin,
            a.address_line1,
            a.address_line2,
            a.city,
            a.state,
            a.country,
            a.pincode,
            dl.link_name AS supplier_name
        FROM `tabAddress` a
        JOIN `tabDynamic Link` dl ON dl.parent = a.name
        WHERE dl.link_doctype = 'Supplier'
          AND a.is_partner = 1
    """, as_dict=True)

    
    address_map = defaultdict(list)
    for addr in addresses:
        supplier_name = addr["supplier_name"]
        address_map[supplier_name].append(addr)

    result = []

    for s in suppliers:
        doc = frappe.get_doc("Supplier", s["name"])
        supplier_categories = [row.item_group for row in doc.get("supplier_product_category")]

        
        if filter_category and filter_category not in supplier_categories:
            continue 

        s["supplier_product_category"] = supplier_categories
        s["addresses"] = address_map.get(s["name"], [])
        result.append(s)

    return result
