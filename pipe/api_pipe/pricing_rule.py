import frappe

def get_item_attachments(item_names):
    files = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "Item", "attached_to_name": ["in", item_names]},
        fields=["attached_to_name", "file_url"]
    )
    attachments_map = {}
    for f in files:
        attachments_map.setdefault(f["attached_to_name"], []).append(f["file_url"])
    return attachments_map

def get_item_prices(item_names, price_list="Standard Selling"):
    prices = frappe.get_all(
        "Item Price",
        filters={"item_code": ["in", item_names], "price_list": price_list},
        fields=["item_code", "price_list_rate"]
    )
    return {p["item_code"]: p["price_list_rate"] for p in prices}

def get_item_gst_rates(item_names):
    gst_map = {}
    item_tax_template_map = {}

    for item_code in item_names:
        item_doc = frappe.get_doc("Item", item_code)

        gst_rate = None
        item_tax_template_id = None

        if item_doc.taxes:  
            tax_template = item_doc.taxes[0].item_tax_template
            if tax_template:
                gst_rate = frappe.db.get_value("Item Tax Template", tax_template, "gst_rate")
                item_tax_template_id = tax_template

        gst_map[item_code] = gst_rate or 0
        item_tax_template_map[item_code] = item_tax_template_id

    return gst_map, item_tax_template_map

@frappe.whitelist()
def items_for_fixed_discount(price_list="Standard Selling", item_code=None):
    all_items = []

    pricing_rules = frappe.get_all(
        "Pricing Rule",
        filters={"is_fixed_discount": 1},
        fields=["name", "discount_percentage"]
    )

    for rule in pricing_rules:
        pricing_rule_doc = frappe.get_doc("Pricing Rule", rule["name"])
        child_items = [d.item_code for d in pricing_rule_doc.items]

        if not child_items:
            continue

        if item_code:
            child_items = [code for code in child_items if code == item_code]

        if not child_items:
            continue

        item_docs = frappe.get_all(
            "Item",
            filters={"name": ["in", child_items]},
            fields=[
                "name",
                "item_name",
                "item_group",
                "gst_hsn_code",
                "description"
            ]
        )

        prices_map = get_item_prices(child_items, price_list)
        attachments_map = get_item_attachments(child_items)
        gst_map, item_tax_template_map = get_item_gst_rates(child_items) 

        for item in item_docs:
            all_items.append({
                "name": item["name"],
                "item_name": item["item_name"],
                "standard_rate as item_price": prices_map.get(item["name"], 0),
                "item_group": item["item_group"],
                "gst_hsn_code": item["gst_hsn_code"],
                "description": item["description"],
                "attachments": attachments_map.get(item["name"], []),
                "discount_percentage": rule.get("discount_percentage", 0),
                "gst_rate": gst_map.get(item["name"], 0),
                "item_tax_template_id": item_tax_template_map.get(item["name"])
            })

    return all_items
