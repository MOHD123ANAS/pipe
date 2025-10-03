import frappe

@frappe.whitelist()
def create_sales_order_with_taxes(doc):
    """
    Create Sales Order in one call with taxes & totals calculated.
    Expects flat JSON body (no `doc` wrapper).
    Example:
    {
        "customer": "CUST-2025-00022",
        "delivery_date": "2025-10-04",
        "shipping_address_name": "CUST-2025-00022-Shipping",
        "dispatch_address_name": "SUP-2025-00005-Billing",
        "disable_rounded_total": 1,
        "taxes_and_charges": "Output GST In-state - PGEPL",
        "supplier": "SUP-2025-00005",
        "tax_category": "In-State",
        "items": [
            {
                "item_code": "STO-ITEM-2025-00200",
                "qty": 1,
                "delivered_by_supplier": 1,
                "supplier": "SUP-2025-00005"
            }
        ]
    }
    """

    # Parse JSON into Python dict
    data = frappe.parse_json(doc)

    # Ensure doctype
    data["doctype"] = "Sales Order"

    # Fallbacks for mandatory fields (if not passed from frontend)
    if "company" not in data:
        data["company"] = frappe.defaults.get_user_default("Company")
    if "currency" not in data:
        data["currency"] = frappe.defaults.get_global_default("currency") or "INR"
    if "selling_price_list" not in data:
        data["selling_price_list"] = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"

    # Create doc
    so = frappe.get_doc(data)

    # Insert record
    so.insert(ignore_permissions=True)

    # Apply default tax template (if set on doc)
    if hasattr(so, "apply_default_taxes_and_charges"):
        so.apply_default_taxes_and_charges()

    # Recalculate totals after tax
    so.calculate_taxes_and_totals()

    # Save updated SO
    so.save()

    # Return dict (so it works well with API call)
    return so.as_dict()
