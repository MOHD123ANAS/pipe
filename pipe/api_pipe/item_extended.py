import frappe
from collections import defaultdict

@frappe.whitelist()
def get_item_details():
    try:
        filters = {}
        if frappe.form_dict.get("item_code"):
            filters["name"] = frappe.form_dict.get("item_code")
        if frappe.form_dict.get("brand"):
            filters["brand"] = frappe.form_dict.get("brand")
        if frappe.form_dict.get("item_group"):
            filters["item_group"] = frappe.form_dict.get("item_group")

        filters["custom_is_this_a_website_item"] = 1

        items = frappe.get_all(
            "Item",
            filters=filters,
            fields=[
                "name as item_code",
                "item_name",
                "brand",
                "item_group",
                "description",
                "stock_uom",
                "custom_min_qty",
                "disabled",
                "custom_is_this_a_website_item"
            ]
        )

        if not items:
            return {"status": "success", "data": []}

        item_codes = [x["item_code"] for x in items]

        # ---- Product Details ----
        prod_details = frappe.get_all(
            "Product Details",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "parameter", "value", "category"]
        )

        prod_map = {}
        for pd in prod_details:
            parent = pd["parent"]
            prod_map.setdefault(parent, defaultdict(list))
            prod_map[parent][pd.get("category", "Other")].append({
                "parameter": pd.get("parameter"),
                "value": pd.get("value")
            })

        # ---- Attachments ----
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Item", "attached_to_name": ["in", item_codes]},
            fields=["attached_to_name", "file_url", "file_name", "is_private"]
        )

        attachment_map = {}
        for att in attachments:
            item_code = att["attached_to_name"]
            file_name = (att["file_name"] or "").lower()
            file_url_name = (att["file_url"].split("/")[-1] or "").lower()
            item_code_lower = item_code.lower()

            # ✅ Include attachments whose name starts with item code or item code followed by '-'
            if (
                file_name.startswith(item_code_lower)
                or file_name.startswith(f"{item_code_lower}-")
                or file_url_name.startswith(item_code_lower)
                or file_url_name.startswith(f"{item_code_lower}-")
            ):
                attachment_map.setdefault(item_code, []).append(att)

        # ---- Price List ----
        price_list = "Standard Selling"
        prices = frappe.get_all(
            "Item Price",
            filters={"price_list": price_list, "item_code": ["in", item_codes]},
            fields=["item_code", "price_list_rate"]
        )
        price_map = {p["item_code"]: p["price_list_rate"] for p in prices}

        # ---- Item Group Hierarchy ----
        group_map = {}
        for row in items:
            ig = row.get("item_group")
            parent_group, child_group = None, ig
            if ig:
                parent_group = frappe.db.get_value("Item Group", ig, "parent_item_group")
            group_map[ig] = {
                "parent_category": parent_group,
                "child_category": child_group
            }

        # ---- Merge Data ----
        for row in items:
            row["product_details"] = prod_map.get(row["item_code"], {})
            row["attachments"] = attachment_map.get(row["item_code"], [])
            row["selling_price"] = price_map.get(row["item_code"])
            row["categories"] = group_map.get(row["item_group"], {})

        return {"status": "success", "data": items}

    except Exception as e:
        frappe.log_error(f"Error in get_item_details: {str(e)}", "Custom API Error")
        return {"status": "error", "error": str(e)}
