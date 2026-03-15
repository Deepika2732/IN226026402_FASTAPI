from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- Data Models ---
products = {
    1: {"name": "Wireless Mouse", "price": 499, "in_stock": True},
    2: {"name": "Notebook", "price": 99, "in_stock": True},
    3: {"name": "USB Hub", "price": 599, "in_stock": False}, # Out of stock for Q3
}

cart = []
orders = []

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

# --- Endpoints ---

@app.get("/cart")
def get_cart():
    if not cart:
        return {"message": "Cart is empty", "items": [], "item_count": 0, "grand_total": 0}
    
    grand_total = sum(item["subtotal"] for item in cart)
    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products[product_id]
    
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # Check if item already in cart (Q4 Logic)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * product["price"]
            return {"message": "Cart updated", "cart_item": item}

    # Add new item
    new_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": quantity * product["price"]
    }
    cart.append(new_item)
    return {"message": "Added to cart", "cart_item": new_item}

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    global cart
    initial_len = len(cart)
    cart = [item for item in cart if item["product_id"] != product_id]
    if len(cart) == initial_len:
        raise HTTPException(status_code=404, detail="Item not in cart")
    return {"message": "Item removed from cart"}

@app.post("/cart/checkout")
def checkout(details: CheckoutRequest):
    global cart
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items first")

    # Process each cart item into the orders list
    for item in cart:
        new_order = {
            "order_id": len(orders) + 1,
            "customer_name": details.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"]
        }
        orders.append(new_order)
    
    cart = [] # Clear cart after checkout
    return {"message": "Order placed successfully", "orders_placed": len(cart)}

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}