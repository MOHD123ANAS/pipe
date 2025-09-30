import frappe

@frappe.whitelist()
def get_sales_orders_with_items():
    debug_logs = []
    results = []

    try:
        debug_logs.append("Step 1: API called successfully.")

        
        debug_logs.append("Step 2: Fetching all Sales Orders...")
        sales_orders = frappe.get_all(
            "Sales Order",
            fields=[
                "name", "customer", "customer_name", "order_type",
                "transaction_date", "delivery_date",
                "reserve_stock", "status", "set_warehouse"
            ],
            order_by="transaction_date desc"
        )

        debug_logs.append(f"Step 3: {len(sales_orders)} Sales Orders fetched.")

        
        for idx, so in enumerate(sales_orders, start=1):
            debug_logs.append(f"Step 4.{idx}: Fetching items for Sales Order {so.name}...")
            
            items = frappe.get_all(
                "Sales Order Item",
                filters={"parent": so.name},
                fields=["item_code", "item_name", "qty", "rate", "amount", "warehouse", "uom", "gst_hsn_code"]
            )

            debug_logs.append(f"Step 4.{idx}: {len(items)} items found for {so.name}.")
            so["items"] = items
            results.append(so)

        debug_logs.append("Step 5: All Sales Orders processed successfully.")

    except Exception as e:
        frappe.log_error(f"Error in get_sales_orders_with_items: {str(e)}", "Custom API Error")
        debug_logs.append(f"Step X: Error occurred -> {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    
    frappe.log_error("\n".join(debug_logs), "DEBUG LOGS - get_sales_orders_with_items")

    return {
        "status": "success",
        "data": results
    }
