# CI-18 clean: uses a config object instead of many positional parameters
from dataclasses import dataclass


@dataclass
class OrderRequest:
    customer_id: str
    product_id: str
    quantity: int
    price: float
    discount: float
    shipping_address: str


def process_order(request: OrderRequest) -> dict:
    total = request.price * request.quantity * (1 - request.discount)
    return {"customer": request.customer_id, "total": total}
