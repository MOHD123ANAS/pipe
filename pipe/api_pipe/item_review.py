import frappe

@frappe.whitelist()
def get_item_reviews(
    name=None,
    item=None,
    customer=None,
    limit_start=0,
    limit_page_length=20,
    child_limit_start=0,
    child_limit_length=None
):
    filters = {}
    if name:
        filters["name"] = name
    if item:
        filters["item"] = item

    limit_start = int(limit_start)
    limit_page_length = int(limit_page_length)
    child_limit_start = int(child_limit_start)
    child_limit_length = int(child_limit_length) if child_limit_length else None

    
    reviews = frappe.get_all(
        "Item Review",
        filters=filters,
        fields=["name", "item", "product_rating", "total_reviews", "total_feedback"],
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by="modified desc"
    )

    final_reviews = []

    for r in reviews:
        r["product_rating"] = round(r["product_rating"] * 5, 1)

        doc = frappe.get_doc("Item Review", r["name"])

        
        all_child_reviews = []
        for row in doc.get("reviews"):
            if customer and row.customer != customer:
                continue

            all_child_reviews.append({
                "customer": row.customer,
                "customer_name": row.customer_name,
                "rating": round(row.rating * 5, 1),
                "feedback": row.feedback
            })

        
        if child_limit_length:
            all_child_reviews = all_child_reviews[child_limit_start:child_limit_start + child_limit_length]

        
        if customer:
            if all_child_reviews:
                r["reviews"] = all_child_reviews
                final_reviews.append(r)
        else:
            r["reviews"] = all_child_reviews
            final_reviews.append(r)

    total_count = len(final_reviews)

    return {
        "reviews": final_reviews,
        "total_count": total_count,
        "limit_start": limit_start,
        "limit_page_length": limit_page_length,
        "child_limit_start": child_limit_start,
        "child_limit_length": child_limit_length
    }
