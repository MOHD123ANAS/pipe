import frappe

def get_item_prices(item_names, price_list="Standard Selling"):
    prices = frappe.get_all(
        "Item Price",
        filters={"item_code": ["in", item_names], "price_list": price_list},
        fields=["item_code", "price_list_rate"]
    )
    return {p["item_code"]: p["price_list_rate"] for p in prices}

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

        
        item_names = [item["name"] for item in items]
        prices_map = get_item_prices(item_names, price_list="Standard Selling")

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
            item["attachments"] = attachments
            items_data.append(item)

        result[pg.name] = items_data

    return result
