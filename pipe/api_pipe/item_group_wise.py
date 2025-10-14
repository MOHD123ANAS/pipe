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


def get_item_price_from_price_list(item_name, price_list="Standard Selling"):
    price = frappe.get_all(
        "Item Price",
        filters={
            "item_code": item_name,
            "price_list": price_list
        },
        fields=["price_list_rate"],
        limit=1
    )
    return price[0]["price_list_rate"] if price else 0


def get_gst_rate(item_name):
    tax_row = frappe.get_all(
        "Item Tax",
        filters={"parent": item_name},
        fields=["item_tax_template"],
        limit=1
    )
    if tax_row and tax_row[0].get("item_tax_template"):
        return frappe.db.get_value("Item Tax Template", tax_row[0]["item_tax_template"], "gst_rate")
    return None


def get_item_tax_template_id(item_name):
    tax_row = frappe.get_all(
        "Item Tax",
        filters={"parent": item_name},
        fields=["item_tax_template"],
        limit=1
    )
    return tax_row[0]["item_tax_template"] if tax_row and tax_row[0].get("item_tax_template") else None


def get_fixed_discount_map():
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
    return discount_map


def get_items_in_group(group_name, limit=None, price_list="Standard Selling", discount_map=None):
    items = frappe.get_all(
        "Item",
        filters={
            "item_group": group_name,
            "custom_is_this_a_website_item": 1
        },
        fields=[
            "name",
            "item_name",
            "standard_rate as item_price",
            "item_group",
            "gst_hsn_code",
            "description"
        ],
        limit=limit if limit else None
    )

    item_codes = [x["name"] for x in items]
    attachment_map = get_filtered_attachments_for_items(item_codes)

    for item in items:
        item["item_price"] = get_item_price_from_price_list(item["name"], price_list)
        item["attachments"] = [a["file_url"] for a in attachment_map.get(item["name"], [])]
        item["gst_rate"] = get_gst_rate(item["name"])
        item["item_tax_template_id"] = get_item_tax_template_id(item["name"])
        item["discount_percentage"] = discount_map.get(item["name"]) if discount_map else None

        
        item["tags"] = frappe.get_all(
            "Tag Link",
            filters={
                "document_type": "Item",
                "document_name": item["name"]
            },
            fields=["tag"],
            pluck="tag"
        )

    return items


def get_items_recursive(group_name, limit=None, price_list="Standard Selling", discount_map=None):
    items = get_items_in_group(group_name, limit, price_list, discount_map)

    children = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": group_name},
        pluck="name"
    )

    for child in children:
        child_items = get_items_recursive(child, limit, price_list, discount_map)
        items.extend(child_items)

    return items


@frappe.whitelist()
def get_items_by_group(parent_group=None, child_group=None, tag=None, limit: int = None, price_list="Standard Selling"):
    
    limit = int(limit) if limit else None
    discount_map = get_fixed_discount_map()

    
    if tag:
        tagged_item_names = frappe.get_all(
            "Tag Link",
            filters={
                "document_type": "Item",
                "tag": tag
            },
            pluck="document_name"
        )

        if not tagged_item_names:
            return []

        
        items = frappe.get_all(
            "Item",
            filters={
                "name": ["in", tagged_item_names],
                "custom_is_this_a_website_item": 1
            },
            fields=[
                "name",
                "item_name",
                "standard_rate as item_price",
                "item_group",
                "gst_hsn_code",
                "description"
            ],
            limit=limit if limit else None
        )

        item_codes = [x["name"] for x in items]
        attachment_map = get_filtered_attachments_for_items(item_codes)

        for item in items:
            item["item_price"] = get_item_price_from_price_list(item["name"], price_list)
            item["attachments"] = [a["file_url"] for a in attachment_map.get(item["name"], [])]
            item["gst_rate"] = get_gst_rate(item["name"])
            item["item_tax_template_id"] = get_item_tax_template_id(item["name"])
            item["discount_percentage"] = discount_map.get(item["name"]) if discount_map else None
            item["tags"] = frappe.get_all(
                "Tag Link",
                filters={
                    "document_type": "Item",
                    "document_name": item["name"]
                },
                fields=["tag"],
                pluck="tag"
            )

        return items

    
    if parent_group and child_group:
        return get_items_in_group(child_group, limit, price_list, discount_map)

    if parent_group:
        return get_items_recursive(parent_group, limit, price_list, discount_map)

    return get_items_recursive("All Item Groups", limit, price_list, discount_map)
