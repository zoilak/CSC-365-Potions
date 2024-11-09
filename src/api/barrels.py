from fastapi import APIRouter, Depends
from pydantic import BaseModel
import random
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    gold_price = 0
    barrel_blue_ml = 0
    barrel_red_ml = 0
    barrel_green_ml =0
    barrel_dark_ml =0
        
    for barrel in barrels_delivered:
        gold_price += (barrel.price * barrel.quantity)
        if barrel.potion_type == [1,0,0,0]:  
            barrel_green_ml += barrel.ml_per_barrel * barrel.quantity
                     
        elif barrel.potion_type == [0,1,0,0]:
            barrel_red_ml += barrel.ml_per_barrel * barrel.quantity
                
        elif barrel.potion_type == [0,0,1,0]:
            barrel_blue_ml += barrel.ml_per_barrel * barrel.quantity
            
        elif barrel.potion_type == [0,0,0,1]:
            barrel_dark_ml += barrel.ml_per_barrel * barrel.quantity

    print(f"Calculated ml amounts - Red: {barrel_red_ml}, Green: {barrel_green_ml}, Blue: {barrel_blue_ml}, Dark: {barrel_dark_ml}")
    print(f"Total gold spent: {gold_price}")
    
    with db.engine.begin() as connection:
        

        connection.execute(sqlalchemy.text("""
            INSERT INTO barrel_ml_log (red, green, blue, dark)
            VALUES (:barrel_red_ml, :barrel_green_ml, :barrel_blue_ml, :barrel_dark_ml)
        """), {
            "barrel_red_ml": barrel_red_ml,
            "barrel_green_ml": barrel_green_ml,
            "barrel_blue_ml": barrel_blue_ml,
            "barrel_dark_ml": barrel_dark_ml
        })

        #loosing gold because you are purchasing barrels
        connection.execute(sqlalchemy.text("""
           INSERT INTO gold_tracker(gold)
            VALUES (:gold_price)
            """), {"gold_price": - gold_price })
    return "OK"

# Gets called once a day , try buying equal amounts of ml in barrels

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # Print and shuffle wholesale catalog
    print("Wholesale Catalog:", wholesale_catalog)
    random.shuffle(wholesale_catalog)

    with db.engine.begin() as connection:
        # Get current ml totals and gold amount
        result_barrel = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(red), 0) AS red_ml,
                COALESCE(SUM(green), 0) AS green_ml,
                COALESCE(SUM(blue), 0) AS blue_ml,                                 
                COALESCE(SUM(dark), 0) AS dark_ml                                 
            FROM barrel_ml_log
                """)).fetchone()
        
        result_gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold), 0) AS total_gold FROM gold_tracker")).fetchone()
        gold_amount = result_gold.total_gold

        barrels_to_purchase = []
        # Inventory types and maximum ml allowed for each type
        local_barrels = {
            'red': {'ml': result_barrel.red_ml, 'color_vector': [1, 0, 0, 0]},
            'green': {'ml': result_barrel.green_ml, 'color_vector': [0, 1, 0, 0]},
            'blue': {'ml': result_barrel.blue_ml, 'color_vector': [0, 0, 1, 0]},
            'dark': {'ml': result_barrel.dark_ml, 'color_vector': [0, 0, 0, 1]}
        }

        #my logic is to buy barrels till i have equlal amount of ml across all potion tyes
        while gold_amount > 0:

            ml_to_buy = min(local_barrels,key=lambda k: local_barrels[k]['ml'])
            properties = local_barrels[ml_to_buy]

            #add a money logic check if brarrel amount is equal and gold is 0
            # if all(properties['ml'] == min_ml_value for properties in local_barrels.values()):
            #     break 

            bool_logic = False
            # Loop through each barrel type in the shuffled catalog
            for barrel in wholesale_catalog:
            # Check affordability of barrel
                if barrel.potion_type == properties ['color_vector'] and barrel.price <= gold_amount:
                    barrels_to_purchase.append({
                                    "sku": barrel.sku,
                                    "quantity": 1
                                })
                    gold_amount -=barrel.price
                    properties['ml'] +=barrel.ml_per_barrel
                    bool_logic = True

                    # Print the purchased barrel for tracking
                    print(f"Purchased 1 barrel of {barrel.sku} for potion type {ml_to_buy}.")
                    print(f"Remaining gold: {gold_amount}")
                    print(f"New ml for {ml_to_buy}: {properties['ml']}")
                    break  # Exit the loop once a barrel is purchased

            if not bool_logic:
                print("No more affordable barrels or no barrel matches the lowest ml potion type.")
                break

            
        print("Barrels purchased:")
        for purchased in barrels_to_purchase:
            print(f"SKU: {purchased['sku']}, Quantity: {purchased['quantity']}")

    return barrels_to_purchase
