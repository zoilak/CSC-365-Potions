from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Tuple
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"  

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):

    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """    
    conditions = []
    params = {}

    sql_log= """
                    SELECT cart_line_items.id AS entry_id,
                        cart_line_items.cart_id, 
                        cart.customer_name AS customer_name,
                        cart_line_items.created_at AS timestamp, 
                        cart_line_items.item_quantity AS potion_amount, 
                        potion_types.cost AS potion_cost,
                        cart_line_items.item_quantity,
                        CONCAT(cart_line_items.item_quantity, ' ', cart_line_items.sku) AS item_sku, 
                        cart_line_items.item_quantity * potion_types.cost AS total
                    FROM cart_line_items
                    JOIN cart ON cart.id = cart_line_items.cart_id
                    JOIN potion_types ON cart_line_items.sku = potion_types.sku
                    """
    
    #Search for cart line items by customer name and/or potion sku.
    if customer_name:
        conditions.append("customer_name ILIKE :customer_name_param") #ILIKE performs parameter matching
        params["customer_name_param"] = f"%{customer_name}%"

    if potion_sku:
        conditions.append("potion_types.sku ILIKE :potion_name_param")
        params["potion_name_param"] = f"%{potion_sku}%"
    
    #after checking customer name and potion sku
    if conditions:
        sql_log += " WHERE " + " AND ".join(conditions)
    
    #sorting
    sql_log+=  " " + "ORDER BY " + sort_col + " " + sort_order.upper() + " "    

    #max pages check
    # Pagination set up
    if search_page:
        search_page = int(search_page)
    else:
        search_page = 0
    
    offset = search_page * 5
    params["offset"] = offset

    sql_log +="LIMIT 5 OFFSET :offset"

    with db.engine.begin() as connection:
        rows = connection.execute(sqlalchemy.text(sql_log),params).fetchall()
        
        count_query = """
            SELECT COUNT(*)
            FROM cart_line_items
            JOIN cart ON cart_line_items.cart_id = cart.id
            JOIN potion_types ON cart_line_items.sku = potion_types.sku
        """

        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)

        total_count = connection.execute(sqlalchemy.text(count_query), params).scalar()
        
        
    # Determine previous and next pages
    if offset + 5 < total_count:
        next_page = str(search_page + 1)
    
    else:
        next_page = ""
     
    if search_page > 0: 
        previous_page = str(search_page - 1)
    else:
        
        previous_page = ""
    
    final_list = []
        
    for item in rows:
        final_list.append({
            "line_item_id": item.entry_id,
            "item_sku": item.item_sku,
            "customer_name": item.customer_name,
            "line_item_total": item.total,
            "timestamp": item.timestamp,
        })
    
        
    return {
        "previous": previous_page,
        "next": next_page,
        "results": final_list
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int


@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    # for person in customers:
    #     if person.level <= 5:
    #         return 


#local data for cart storage
# carts: Dict = {}  # cart_id: [[item_sku, quantity]]


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    # cart_id = len(carts) +1
    # carts[cart_id] = []
    # return {"cart_id": cart_id}
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text( # type: ignore
                                            """
                                            INSERT INTO cart (customer_name)
                                            VALUES (:customer_name)
                                            RETURNING id
                                         
                                            """
                                            ) , [{"customer_name" : new_cart.customer_name}]).scalar()
    return{"cart_id": result}

class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Set the quantity for a specific item in the cart.
    If the item exists, it updates the quantity; otherwise, it adds the item.
    """

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text( # type: ignore
                                            """ INSERT INTO cart_line_items( cart_id, sku, item_quantity)
                                                VALUES (:cart_id, :sku, :item_quantity)
                                             """),  
                                            [{"cart_id" : cart_id,"sku": item_sku ,"item_quantity": cart_item.quantity}])
    
    print(f"Item SKU: {item_sku}")
    print(f"Cart ID: {cart_id}")
    print(f"Quantity: {cart_item.quantity}")

    return "OK"


class CartCheckout(BaseModel):
    payment: str #why is this a string



@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Finalize the cart and check if the purchase can be completed.
    """
    #global carts

    #debugging statement
    print("cart payment:" , cart_checkout.payment)

    with db.engine.begin() as connection:
        result_cart = connection.execute(sqlalchemy.text("""
                                                        SELECT cart_id, sku, item_quantity
                                                        FROM cart_line_items
                                                        WHERE cart_id = :cart_id
                                                    """), {"cart_id": cart_id}).fetchall()

    total_potions = 0  # Initialize total_potions
    gold_paid = 0  # Initialize gold_paid

    for cart_info in result_cart:
        # Get potion details
        with db.engine.begin() as connection:
            
            potion_to_buy = connection.execute(sqlalchemy.text("""
                                                                    SELECT id, cost, sku
                                                                    FROM potion_types
                                                                    WHERE potion_types.sku = :sku
                                                                """), {"sku": cart_info.sku}).first()
           
           
            if potion_to_buy is None:
                raise ValueError(f"Potion with SKU {cart_info.sku} not found in storage.")
           
            # Update potion quantity
            connection.execute(sqlalchemy.text("""
                                                        INSERT INTO potion_log (pID, quantity)
                                                        VALUES (:pID,:quantity)
                                                        """), {"pID": potion_to_buy.id, "quantity": -cart_info.item_quantity})

            #Update gold_tracker
            connection.execute(sqlalchemy.text(""" 
                                                        INSERT INTO gold_tracker (gold)
                                                        VALUES (:gold)
                                                    """), {"gold": cart_info.item_quantity * potion_to_buy.cost})

            total_potions += cart_info.item_quantity
            gold_paid += cart_info.item_quantity * potion_to_buy.cost

        return {"total_potions_bought": total_potions, "total_gold_paid": gold_paid}
    
