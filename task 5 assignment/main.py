from fastapi import FastAPI, Query, HTTPException
from typing import Optional

app = FastAPI()

# --- Sample Data ---
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics"},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery"},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics"},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery"},
]

orders = []

# --- Existing Endpoints (Q1, Q2, Q3) ---

@app.get("/products/search")
def search_products(keyword: str):
    results = [p for p in products if keyword.lower() in p['name'].lower()]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {"keyword": keyword, "total_found": len(results), "products": results}

@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}
    
    reverse = (order == "desc")
    sorted_list = sorted(products, key=lambda p: p[sort_by], reverse=reverse)
    return {"sort_by": sort_by, "order": order, "products": sorted_list}

@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    paged_products = products[start : start + limit]
    total_pages = -(-len(products) // limit)
    return {"page": page, "limit": limit, "total_pages": total_pages, "products": paged_products}

# --- New Endpoints (Q4, Q5, Q6 & Bonus) ---

# Q4: Search Orders by Customer Name
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    results = [
        o for o in orders
        if customer_name.lower() in o['customer_name'].lower()
    ]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}

# Q5: Sort Products by Category (A-Z) then Price (Low-High)
@app.get("/products/sort-by-category")
def sort_by_category():
    # Sorts first by category, then by price within that category
    result = sorted(products, key=lambda p: (p['category'], p['price']))
    return {"products": result, "total": len(result)}

# Q6: Master Browse (Search + Sort + Paginate)
@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):
    # 1. Search/Filter
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower()]

    # 2. Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # 3. Paginate
    total = len(result)
    start = (page - 1) * limit
    paged = result[start : start + limit]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit) if limit > 0 else 0,
        "products": paged,
    }

# Bonus: Paginate the Orders List
@app.get("/orders/page")
def get_orders_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20),
):
    start = (page - 1) * limit
    total_pages = -(-len(orders) // limit) if orders else 0
    return {
        "page": page,
        "limit": limit,
        "total": len(orders),
        "total_pages": total_pages,
        "orders": orders[start : start + limit],
    }

# To make Q4 and Bonus easier to test, here is the existing POST order logic
@app.post("/orders")
def create_order(customer_name: str, product_id: int):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_order = {
        "order_id": len(orders) + 1,
        "customer_name": customer_name,
        "product": product
    }
    orders.append(new_order)
    return {"message": "Order placed successfully", "order": new_order}

# Q1-Q3 Requirement: Existing product detail endpoint
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return {"error": "Product not found"}
    return product