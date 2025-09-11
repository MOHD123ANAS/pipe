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
            "standard_rate as item_price",
            "item_group",
            "gst_hsn_code",
            "description"
        ],
        limit=limit if limit else None
    )

    for item in items:
        attachments = get_item_attachments(item["name"])
        item["attachments"] = [a["file_url"] for a in attachments]

    return items


def get_items_recursive(group_name, limit=None):
    
    items = get_items_in_group(group_name, limit)

    children = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": group_name},
        pluck="name"
    )

    for child in children:
        child_items = get_items_recursive(child, limit)
        items.extend(child_items)

    return items


@frappe.whitelist()
def get_items_by_group(parent_group=None, child_group=None, limit: int = None):
    
    limit = int(limit) if limit else None

    
    if parent_group and child_group:
        return get_items_in_group(child_group, limit)

    
    if parent_group:
        return get_items_recursive(parent_group, limit)

    
    return get_items_recursive("All Item Groups", limit)