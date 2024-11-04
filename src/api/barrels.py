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
        if "green" in barrel.sku:   
            barrel_green_ml += barrel.ml_per_barrel * barrel.quantity
                     
        elif "red" in barrel.sku:
            barrel_red_ml += barrel.ml_per_barrel * barrel.quantity
                
        elif "blue" in barrel.sku:
            barrel_blue_ml += barrel.ml_per_barrel * barrel.quantity
            

        elif "dark" in barrel.sku:
            barrel_dark_ml += barrel.ml_per_barrel * barrel.quantity

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

# Gets called once a day

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
        
        result_gold = connection.execute(sqlalchemy.text("SELECT gold FROM gold_tracker")).one()
        gold_amount = result_gold.gold

        barrels_to_purchase = []
        # Inventory types and maximum ml allowed for each type
        local_barrels = {
            'red': {'ml': result_barrel.red_ml, 'color_vector': [1, 0, 0, 0]},
            'green': {'ml': result_barrel.green_ml, 'color_vector': [0, 1, 0, 0]},
            'blue': {'ml': result_barrel.blue_ml, 'color_vector': [0, 0, 1, 0]},
            'dark': {'ml': result_barrel.dark_ml, 'color_vector': [0, 0, 0, 1]}
        }

        # Loop through each barrel type in the shuffled catalog
        for barrel in wholesale_catalog:
            # Check affordability of barrel
            if barrel.price > 0:
                max_barrels = gold_amount // barrel.price

                if max_barrels > 0:
                    # Identify color type and ml available for that type
                    for properties in local_barrels.values():
                        if barrel.potion_type == properties['color_vector'] and properties['ml'] < 100:
                            # Calculate remaining capacity and max barrels for the threshold
                            available_capacity = 100 - properties['ml']
                            barrels_to_add = min(max_barrels, available_capacity)

                            # Add barrels to purchase list and adjust gold and ml totals
                            if barrels_to_add > 0:
                                barrels_to_purchase.append({
                                    "sku": barrel.sku,
                                    "quantity": barrels_to_add
                                })
                                gold_amount -= barrel.price * barrels_to_add
                                properties['ml'] += barrels_to_add  # Update current ml level

            else:
                print(f"Can't afford barrel {barrel.sku}")

    # Print the barrels being purchased for confirmation
    for purchased in barrels_to_purchase:
        print(f"Purchasing barrels: {purchased}")

    return barrels_to_purchase
