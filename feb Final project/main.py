from fastapi import FastAPI, HTTPException, Query, status, Response
from pydantic import BaseModel, Field
from typing import Optional, List
import math

app = FastAPI(title="QuickBite Food Delivery API")

# --- DATA MODELS (InMemory Database) ---
menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 250, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Cheese Burger", "price": 150, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Iced Coffee", "price": 80, "category": "Drink", "is_available": True},
    {"id": 4, "name": "Chocolate Brownie", "price": 120, "category": "Dessert", "is_available": False},
    {"id": 5, "name": "Pepperoni Pizza", "price": 350, "category": "Pizza", "is_available": True},
    {"id": 6, "name": "Coke", "price": 40, "category": "Drink", "is_available": True},
]

orders = []
order_counter = 1
cart = []

# --- PYDANTIC MODELS ---

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"  # Default value

class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# --- HELPER FUNCTIONS (Day 3) ---

def find_menu_item(item_id: int):
    return next((item for item in menu if item["id"] == item_id), None)

def calculate_bill(price: int, quantity: int, order_type: str = "delivery"):
    total = price * quantity
    if order_type.lower() == "delivery":
        total += 30
    return total

# --- DAY 1: BASIC GET ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}

@app.get("/menu/summary") # Fixed route before /{id}
def get_menu_summary():
    available = [i for i in menu if i["is_available"]]
    categories = list(set(i["category"] for i in menu))
    return {
        "total_items": len(menu),
        "available_count": len(available),
        "unavailable_count": len(menu) - len(available),
        "categories": categories
    }

@app.get("/menu")
def get_all_menu():
    return {"menu": menu, "total": len(menu)}

@app.get("/menu/{item_id}")
def get_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    return item

@app.get("/orders")
def get_all_orders():
    return {"orders": orders, "total_orders": len(orders)}

# --- DAY 2 & 3: POST & FILTERING ---

@app.post("/orders")
def place_order(request: OrderRequest):
    item = find_menu_item(request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item currently unavailable")
    
    total_price = calculate_bill(item["price"], request.quantity, request.order_type)
    
    global order_counter
    new_order = {
        "order_id": order_counter,
        "customer": request.customer_name,
        "item": item["name"],
        "total_bill": total_price,
        "status": "Confirmed"
    }
    orders.append(new_order)
    order_counter += 1
    return new_order

@app.get("/menu/filter")
def filter_menu(
    category: Optional[str] = None, 
    max_price: Optional[int] = None, 
    is_available: Optional[bool] = None
):
    filtered = menu
    if category is not None:
        filtered = [i for i in filtered if i["category"].lower() == category.lower()]
    if max_price is not None:
        filtered = [i for i in filtered if i["price"] <= max_price]
    if is_available is not None:
        filtered = [i for i in filtered if i["is_available"] == is_available]
    
    return {"results": filtered, "count": len(filtered)}

# --- DAY 4: CRUD OPERATIONS ---

@app.post("/menu", status_code=status.HTTP_201_CREATED)
def add_menu_item(item: NewMenuItem):
    if any(i["name"].lower() == item.name.lower() for i in menu):
        raise HTTPException(status_code=400, detail="Item already exists")
    
    new_id = max(i["id"] for i in menu) + 1
    new_data = {"id": new_id, **item.dict()}
    menu.append(new_data)
    return new_data

@app.put("/menu/{item_id}")
def update_menu_item(item_id: int, price: Optional[int] = None, is_available: Optional[bool] = None):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if price is not None: item["price"] = price
    if is_available is not None: item["is_available"] = is_available
    return item

@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    menu.remove(item)
    return {"message": f"Successfully deleted {item['name']}"}

# --- DAY 5: CART & WORKFLOW ---

@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)
    if not item or not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item unavailable or doesn't exist")
    
    for cart_item in cart:
        if cart_item["id"] == item_id:
            cart_item["quantity"] += quantity
            return {"message": "Quantity updated", "cart": cart}
            
    cart.append({"id": item["id"], "name": item["name"], "price": item["price"], "quantity": quantity})
    return {"message": "Added to cart", "cart": cart}

@app.get("/cart")
def view_cart():
    grand_total = sum(i["price"] * i["quantity"] for i in cart)
    return {"items": cart, "grand_total": grand_total}

@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):
    global cart
    cart = [i for i in cart if i["id"] != item_id]
    return {"message": "Item removed from cart"}

@app.post("/cart/checkout", status_code=201)
def checkout(request: CheckoutRequest):
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    global order_counter
    placed_orders = []
    grand_total = 0
    
    for item in cart:
        bill = item["price"] * item["quantity"]
        order = {
            "order_id": order_counter,
            "customer": request.customer_name,
            "item": item["name"],
            "total": bill,
            "address": request.delivery_address
        }
        orders.append(order)
        placed_orders.append(order)
        grand_total += bill
        order_counter += 1
    
    cart.clear()
    return {"placed_orders": placed_orders, "grand_total": grand_total}

# --- DAY 6: SEARCH, SORT, PAGINATION ---

@app.get("/menu/search")
def search_menu(keyword: str):
    results = [i for i in menu if keyword.lower() in i["name"].lower() or keyword.lower() in i["category"].lower()]
    if not results:
        return {"message": f"No items found for '{keyword}'"}
    return {"results": results, "total_found": len(results)}

@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    
    reverse = True if order == "desc" else False
    sorted_menu = sorted(menu, key=lambda x: x[sort_by], reverse=reverse)
    return {"sorted_by": sort_by, "order": order, "results": sorted_menu}

@app.get("/menu/page")
def paginate_menu(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(menu) / limit)
    return {
        "page": page,
        "limit": limit,
        "total": len(menu),
        "total_pages": total_pages,
        "items": menu[start:end]
    }

@app.get("/menu/browse")
def browse_menu(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    # Filter
    data = menu
    if keyword:
        data = [i for i in data if keyword.lower() in i["name"].lower()]
    
    # Sort
    rev = (order == "desc")
    data = sorted(data, key=lambda x: x.get(sort_by, "price"), reverse=rev)
    
    # Paginate
    start = (page - 1) * limit
    return {
        "metadata": {"page": page, "total": len(data)},
        "items": data[start : start + limit]
    }