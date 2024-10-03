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

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
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

    return "OK"

#local data for cart storage
carts: Dict = {}  # cart_id: [[item_sku, quantity]]
@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    cart_id = len(carts) +1
    carts[cart_id] = []
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Set the quantity for a specific item in the cart.
    If the item exists, it updates the quantity; otherwise, it adds the item.
    """
    #check if it exits and if found update it 
    for order in carts[cart_id]:

        if order[0]==item_sku:

            order[1] = cart_item.quantity

            return {"message": f"Updated {item_sku} quantity to {cart_item.quantity}"}
    
    #if not found append as new entry
    carts[cart_id].append([item_sku, cart_item.quantity])
    
    return {"message": f"Added {item_sku} to cart with quantity {cart_item.quantity}"}
        
    
    """ """
    # with connection open
    #     ask database for something
    #     psuh data into database
    #     find out what to return in json
    # return "OK"


class CartCheckout(BaseModel):
    payment: str



@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Finalize the cart and check if the purchase can be completed.
    """
    #global carts

    #debugging statement
    print("cart payment:" , cart_checkout.payment)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).one()

        green_potions = result.num_green_potions
        gold_count = result.gold

        green_potions_bought = 0
        gold_paid = 0
        potion_cost = 20 

        #quantity = carts[cart_id][0][1]
       

        for item_sku, quantity in carts[cart_id]:

            if "potion" in item_sku.lower():

                if quantity <= green_potions:

                    green_potions -= quantity
                    gold_paid += quantity * potion_cost
                    green_potions_bought += quantity
                    

            else:
                print("nothing purchased")
                return {}

        final_gold = gold_count + gold_paid

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :green_potions"), {"green_potions": green_potions})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold_count"), {"gold_count": final_gold})

    #need to create a local counter and cart 
    print("purchase successful")
    return {"total_potions_bought": green_potions_bought, "total_gold_paid": gold_paid}
   
