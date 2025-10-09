import frappe

def get_filtered_attachments_for_items(item_codes):
    
    if not item_codes:
        return {}

    attachments = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Item",
            "attached_to_name": ["in", item_codes],
        },
        fields=["attached_to_name", "file_url", "file_name", "is_private"]
    )

    attachment_map = {}

    for att in attachments:
        item_code = att["attached_to_name"]
        file_name = (att.get("file_name") or "").lower()
        file_url_name = (att.get("file_url", "").split("/")[-1] or "").lower()
        item_code_lower = item_code.lower()

        
        if (
            file_name.startswith(item_code_lower)
            or file_name.startswith(f"{item_code_lower}-")
            or file_url_name.startswith(item_code_lower)
            or file_url_name.startswith(f"{item_code_lower}-")
        ):
            attachment_map.setdefault(item_code, []).append(att)

    return attachment_map


@frappe.whitelist()
def get_item_attachments(item_name):
    return frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Item",
            "attached_to_name": item_name
        },
        fields=["file_url"]
    )


@frappe.whitelist()
def get_items_in_group(group_name, limit=None):
    items = frappe.get_all(
        "Item",
        filters={
            "item_group": group_name,
            "custom_is_this_a_website_item": 1
        },
        fields=[
            "name",
            "item_name",
            "item_group",
            "gst_hsn_code",
            "description"
        ],
        limit=limit if limit else None
    )

    for item in items:
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item["name"], "price_list": "Standard Selling"},
            "price_list_rate"
        )
        item["item_price"] = price or 0

    item_codes = [x["name"] for x in items]
    gst_map = {}
    tax_template_map = {}

    if item_codes:
        
        tax_rows = frappe.get_all(
            "Item Tax",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "item_tax_template"]
        )

        for tr in tax_rows:
            if tr.get("item_tax_template"):
                gst_rate = frappe.db.get_value(
                    "Item Tax Template", tr["item_tax_template"], "gst_rate"
                )
                gst_map[tr["parent"]] = gst_rate
                tax_template_map[tr["parent"]] = tr["item_tax_template"]

        
        discount_map = {}
        pricing_rules = frappe.get_all(
            "Pricing Rule",
            filters={"is_fixed_discount": 1},
            fields=["name", "discount_percentage"]
        )

        if pricing_rules:
            for rule in pricing_rules:
                rule_doc = frappe.get_doc("Pricing Rule", rule["name"])
                for d in rule_doc.items:
                    if d.item_code in item_codes:
                        discount_map[d.item_code] = rule["discount_percentage"]

        
        attachment_map = get_filtered_attachments_for_items(item_codes)

        for item in items:
            item["attachments"] = [a["file_url"] for a in attachment_map.get(item["name"], [])]
            item["gst_rate"] = gst_map.get(item["name"])
            item["item_tax_template_id"] = tax_template_map.get(item["name"])
            item["discount_percentage"] = discount_map.get(item["name"])

    else:
        for item in items:
            attachments = get_item_attachments(item["name"])
            item["attachments"] = [a["file_url"] for a in attachments]
            item["gst_rate"] = None
            item["item_tax_template_id"] = None
            item["discount_percentage"] = None

    return items


def build_group_tree(group_name, limit=None):
    items = get_items_in_group(group_name, limit)

    children = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": group_name},
        pluck="name"
    )

    if not children:
        return items

    result = {}
    if items:
        result["_items"] = items

    for child in children:
        result[child] = build_group_tree(child, limit)

    return result


@frappe.whitelist()
def get_full_item_group_tree(limit: int = None):
    root = "All Item Groups"
    limit = int(limit) if limit else None
    return {root: build_group_tree(root, limit)}