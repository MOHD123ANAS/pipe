import frappe

def get_item_prices(item_names, price_list="Standard Selling"):
    prices = frappe.get_all(
        "Item Price",
        filters={"item_code": ["in", item_names], "price_list": price_list},
        fields=["item_code", "price_list_rate"]
    )
    return {p["item_code"]: p["price_list_rate"] for p in prices}

def filter_item_attachments(item_name, attachments):
    
    filtered = []
    for a in attachments:
        file_url = a.get("file_url", "")
        file_name = a.get("file_name", "")
        if file_url.lower().startswith(f"/files/{item_name.lower()}") or file_name.lower().startswith(item_name.lower()):
            filtered.append(a)
    return filtered

@frappe.whitelist()
def get_items_by_parent_groups(limit=None):
    result = {}
    limit = int(limit) if limit else None

    parent_groups = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": "All Item Groups"},
        fields=["name"]
    )

    discount_map = {}
    pricing_rules = frappe.get_all(
        "Pricing Rule",
        filters={"is_fixed_discount": 1},
        fields=["name", "discount_percentage"]
    )
    for rule in pricing_rules:
        rule_doc = frappe.get_doc("Pricing Rule", rule["name"])
        for d in rule_doc.items:
            existing = discount_map.get(d.item_code, 0)
            discount_map[d.item_code] = max(existing, rule["discount_percentage"])

    for pg in parent_groups:
        items_data = []
        items = frappe.get_all(
            "Item",
            filters=[
                ["item_group", "descendants of (inclusive)", pg.name],
                ["custom_is_this_a_website_item", "=", 1]
            ],
            fields=[
                "name",
                "item_name",
                "item_group",
                "stock_uom",
                "standard_rate",
                "gst_hsn_code",
                "description"
            ],
            limit_page_length=limit
        )

        item_names = [item["name"] for item in items]
        prices_map = get_item_prices(item_names, price_list="Standard Selling")

        gst_map = {}
        tax_template_map = {}
        if item_names:
            tax_rows = frappe.get_all(
                "Item Tax",
                filters={"parent": ["in", item_names]},
                fields=["parent", "item_tax_template"]
            )
            for tr in tax_rows:
                if tr.get("item_tax_template"):
                    gst_rate = frappe.db.get_value(
                        "Item Tax Template", tr["item_tax_template"], "gst_rate"
                    )
                    gst_map[tr["parent"]] = gst_rate
                    tax_template_map[tr["parent"]] = tr["item_tax_template"]

        for item in items:
            item["standard_rate"] = prices_map.get(item["name"], 0)

            attachments = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Item",
                    "attached_to_name": item["name"]
                },
                fields=["file_url", "file_name"]
            )

            
            filtered_attachments = filter_item_attachments(item["name"], attachments)
            item["attachments"] = filtered_attachments

            item["gst_rate"] = gst_map.get(item["name"])
            item["item_tax_template_id"] = tax_template_map.get(item["name"])
            item["discount_percentage"] = discount_map.get(item["name"]) or None

            items_data.append(item)

        result[pg.name] = items_data

    return result
