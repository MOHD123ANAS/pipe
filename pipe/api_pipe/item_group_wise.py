import frappe

def get_item_attachments(item_name):
    return frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Item",
            "attached_to_name": item_name
        },
        fields=["file_url"]
    )

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
    """Fetch gst_rate from Item Tax Template for given Item"""
    tax_row = frappe.get_all(
        "Item Tax",
        filters={"parent": item_name},
        fields=["item_tax_template"],
        limit=1
    )
    if tax_row and tax_row[0].get("item_tax_template"):
        return frappe.db.get_value("Item Tax Template", tax_row[0]["item_tax_template"], "gst_rate")
    return None

def get_items_in_group(group_name, limit=None, price_list="Standard Selling"):
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

    for item in items:
        # price
        item["item_price"] = get_item_price_from_price_list(item["name"], price_list)

        # attachments
        attachments = get_item_attachments(item["name"])
        item["attachments"] = [a["file_url"] for a in attachments]

        # gst_rate
        item["gst_rate"] = get_gst_rate(item["name"])

    return items

def get_items_recursive(group_name, limit=None, price_list="Standard Selling"):
    items = get_items_in_group(group_name, limit, price_list)

    children = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": group_name},
        pluck="name"
    )

    for child in children:
        child_items = get_items_recursive(child, limit, price_list)
        items.extend(child_items)

    return items

@frappe.whitelist()
def get_items_by_group(parent_group=None, child_group=None, limit: int = None, price_list="Standard Selling"):
    limit = int(limit) if limit else None

    if parent_group and child_group:
        return get_items_in_group(child_group, limit, price_list)

    if parent_group:
        return get_items_recursive(parent_group, limit, price_list)

    return get_items_recursive("All Item Groups", limit, price_list)