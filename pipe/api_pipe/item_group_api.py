import frappe

@frappe.whitelist()
def get_items_by_parent_groups(limit=None):
    
    result = {}
    limit = int(limit) if limit else None

    
    parent_groups = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": "All Item Groups"},
        fields=["name"]
    )

    
    for pg in parent_groups:
        items_data = []
        items = frappe.get_all(
            "Item",
            filters=[
                ["item_group", "descendants of (inclusive)", pg.name],
                ["custom_is_this_a_website_item", "=", 1]
            ],
            fields=["name", "item_name", "item_group", "stock_uom", "standard_rate", "gst_hsn_code", "description"],
            limit_page_length=limit 
        )

        for item in items:
            
            attachments = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Item",
                    "attached_to_name": item["name"]
                },
                fields=["file_url", "file_name"]
            )
            item["attachments"] = attachments
            items_data.append(item)

        result[pg.name] = items_data

    return result
