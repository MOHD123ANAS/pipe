import frappe

@frappe.whitelist(allow_guest=True)
def get_all_items_with_attachments():
    """
    Fetch all items along with their attachments
    """
    # 1. Get all items (you can add filters if needed)
    items = frappe.get_all(
        "Item",
        fields=["name", "item_code", "item_name", "stock_uom", "disabled"]
    )

    result = []

    # 2. For each item, get attachments
    for item in items:
        files = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Item", "attached_to_name": item["name"]},
            fields=["file_url", "file_name", "is_private"]
        )
        result.append({
            **item,
            "attachments": files
        })

    return result
