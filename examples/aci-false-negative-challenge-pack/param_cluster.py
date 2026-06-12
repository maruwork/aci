# CI-18 fixture: function with 5+ positional parameters
def process_order(customer_id, product_id, quantity, price, discount, shipping_address):
    total = price * quantity * (1 - discount)
    return {"customer": customer_id, "product": product_id, "total": total, "ship_to": shipping_address}
