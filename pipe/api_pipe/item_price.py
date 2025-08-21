import frappe

@frappe.whitelist()
def get_website_items_with_price():
    debug_logs = []

    try:
        debug_logs.append("Step 1: API called successfully.")

        
        debug_logs.append("Step 2: Running SQL query...")
        data = frappe.db.sql("""
            SELECT DISTINCT
                ip.item_code,
                i.item_name,
                ip.price_list,
                ip.price_list_rate,
                i.custom_is_this_a_website_item,
                i.disabled,
                i.description,
                i.stock_uom,
                i.brand,
                i.custom_min_qty,
                i.item_group
            FROM
                `tabItem Price` ip
            INNER JOIN
                `tabItem` i ON ip.item_code = i.name
            WHERE
                ip.price_list = 'Standard Selling'
                AND IFNULL(i.custom_is_this_a_website_item, 0) = 1
        """, as_dict=1)

        debug_logs.append(f"Step 3: Query executed. Records fetched = {len(data)}")

        
        for row in data:
            files = frappe.get_all(
                "File",
                filters={"attached_to_doctype": "Item", "attached_to_name": row["item_code"]},
                fields=["file_url", "file_name", "is_private"]
            )
            row["attachments"] = files

        
        frappe.response["message"] = {
            "status": "success",
            "data": data
        }

        debug_logs.append("Step 4: Response prepared successfully.")

    except Exception as e:
        frappe.log_error(f"Error in get_website_items_with_price: {str(e)}", "Custom API Error")
        frappe.response["message"] = {
            "status": "error",
            "error": str(e)
        }
        debug_logs.append(f"Step X: Error occurred -> {str(e)}")

    
    frappe.log_error("\n".join(debug_logs), "DEBUG LOGS - get_website_items_with_price")

    return frappe.response["message"]
