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

    # --- fetch gst_rate from Item Tax Template
    item_codes = [x["name"] for x in items]
    if item_codes:
        tax_rows = frappe.get_all(
            "Item Tax",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "item_tax_template"]
        )

        gst_map = {}
        for tr in tax_rows:
            if tr.get("item_tax_template"):
                gst_rate = frappe.db.get_value("Item Tax Template", tr["item_tax_template"], "gst_rate")
                gst_map[tr["parent"]] = gst_rate

        # merge into items
        for item in items:
            attachments = get_item_attachments(item["name"])
            item["attachments"] = [a["file_url"] for a in attachments]
            item["gst_rate"] = gst_map.get(item["name"])  # ✅ added field
    else:
        for item in items:
            attachments = get_item_attachments(item["name"])
            item["attachments"] = [a["file_url"] for a in attachments]
            item["gst_rate"] = None

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

